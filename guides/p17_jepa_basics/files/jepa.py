"""Mini I-JEPA on 8x8 handwritten digits: predict the EMBEDDINGS of hidden patches from the visible ones.

Variants trained with the same budget:
    ema     I-JEPA: targets from an exponential-moving-average copy of the encoder (teacher), no gradient
    sigreg  LeJEPA-style: one encoder, collapse prevented by SIGReg (embeddings pushed towards an isotropic Gaussian)
    naive   no teacher, no regulariser: shows representation collapse
    pixel   generative baseline (MAE-like): predict the hidden pixels
Evaluation: freeze the encoder, average the patch embeddings, train a linear probe for the digit class.
"""
import copy
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

def sigreg(z: torch.Tensor, n_dirs: int = 64, n_t: int = 17, t_max: float = 3.0, generator=None) -> torch.Tensor:
    """z: (N, D) embeddings. Returns a scalar >= 0 that is ~0 when every random 1-D projection is N(0, 1)."""
    n, d = z.shape
    dirs = torch.randn(d, n_dirs, device=z.device, generator=generator)
    dirs = dirs / dirs.norm(dim=0, keepdim=True)
    x = z @ dirs                                                  # (N, M) projections
    t = torch.linspace(-t_max, t_max, n_t, device=z.device)       # points where characteristic functions are compared
    xt = x.unsqueeze(-1) * t                                      # (N, M, T)
    re, im = torch.cos(xt).mean(0), torch.sin(xt).mean(0)         # empirical characteristic function
    target = torch.exp(-0.5 * t ** 2)                             # N(0,1) characteristic function (real)
    weight = torch.exp(-0.5 * t ** 2)                             # Gaussian weighting (Epps-Pulley)
    err = ((re - target) ** 2 + im ** 2) * weight                 # (M, T)
    return torch.trapezoid(err, t, dim=-1).mean() * n             # scaled by N like the test statistic


@torch.no_grad()
def collapse_stats(z: torch.Tensor) -> dict:
    """Signs of collapse: per-dimension std near 0, and an effective rank far below the dimension."""
    z = z.float()
    std = z.std(0).mean().item()
    s = torch.linalg.svdvals(z - z.mean(0))
    p = s / s.sum().clamp_min(1e-12)
    eff_rank = torch.exp(-(p * torch.log(p.clamp_min(1e-12))).sum()).item()
    return {"mean_std": std, "effective_rank": eff_rank, "dim": z.shape[1]}


GRID, PATCH = 4, 2                      # 8x8 image -> 4x4 patches of 2x2 pixels
N_PATCH, PATCH_DIM = GRID * GRID, PATCH * PATCH


def load_digits_patches(seed: int = 7):
    """(train_x, train_y, test_x, test_y): x is (N, 16, 4) patches scaled to [0, 1]. Fixed split, no leakage."""
    from sklearn.datasets import load_digits
    from sklearn.model_selection import train_test_split
    d = load_digits()
    imgs = d.images.astype(np.float32) / 16.0
    patches = imgs.reshape(-1, GRID, PATCH, GRID, PATCH).transpose(0, 1, 3, 2, 4).reshape(-1, N_PATCH, PATCH_DIM)
    xtr, xte, ytr, yte = train_test_split(patches, d.target, test_size=0.25, random_state=seed, stratify=d.target)
    return torch.tensor(xtr), torch.tensor(ytr), torch.tensor(xte), torch.tensor(yte)


class Encoder(nn.Module):
    def __init__(self, dim: int = 64, depth: int = 2, heads: int = 4):
        super().__init__()
        self.embed = nn.Linear(PATCH_DIM, dim)
        self.pos = nn.Parameter(torch.randn(1, N_PATCH, dim) * 0.02)
        layer = nn.TransformerEncoderLayer(dim, heads, dim * 2, dropout=0.0, batch_first=True, norm_first=True)
        self.blocks = nn.TransformerEncoder(layer, depth, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(dim)

    def forward(self, x: torch.Tensor, keep: torch.Tensor | None = None) -> torch.Tensor:
        """x: (B, 16, 4). keep: (B, 16) bool of visible patches; hidden ones are removed by attention masking."""
        h = self.embed(x) + self.pos
        pad = None if keep is None else ~keep
        return self.norm(self.blocks(h, src_key_padding_mask=pad))


class Predictor(nn.Module):
    """Takes context embeddings plus mask tokens at the target positions and predicts the targets."""

    def __init__(self, dim: int = 64, out_dim: int | None = None, depth: int = 2, heads: int = 4):
        super().__init__()
        self.mask_token = nn.Parameter(torch.zeros(1, 1, dim))
        self.pos = nn.Parameter(torch.randn(1, N_PATCH, dim) * 0.02)
        layer = nn.TransformerEncoderLayer(dim, heads, dim * 2, dropout=0.0, batch_first=True, norm_first=True)
        self.blocks = nn.TransformerEncoder(layer, depth, enable_nested_tensor=False)
        self.out = nn.Linear(dim, out_dim or dim)

    def forward(self, ctx: torch.Tensor, keep: torch.Tensor) -> torch.Tensor:
        h = torch.where(keep.unsqueeze(-1), ctx, self.mask_token.expand_as(ctx)) + self.pos
        return self.out(self.blocks(h))


def sample_masks(b: int, gen: torch.Generator, block: int = 2) -> torch.Tensor:
    """keep mask (B, 16): hide one random block x block square of patches (the target), keep the rest."""
    keep = torch.ones(b, GRID, GRID, dtype=torch.bool)
    r = torch.randint(0, GRID - block + 1, (b,), generator=gen)
    c = torch.randint(0, GRID - block + 1, (b,), generator=gen)
    for i in range(b):
        keep[i, r[i]:r[i] + block, c[i]:c[i] + block] = False
    return keep.view(b, N_PATCH)


def train(variant: str = "ema", epochs: int = 40, dim: int = 64, batch: int = 128, lr: float = 1e-3,
          ema: float = 0.99, sigreg_weight: float = 0.5, seed: int = 7, data=None, log_every: int = 0) -> dict:
    """Returns {"encoder": ..., "history": [...], "seconds": ...}. history holds loss and collapse stats per epoch."""
    if variant not in ("ema", "sigreg", "naive", "pixel"):
        raise ValueError("variant must be ema, sigreg, naive or pixel")
    torch.manual_seed(seed)
    gen = torch.Generator().manual_seed(seed)
    xtr, _, _, _ = data or load_digits_patches(seed)
    enc = Encoder(dim)
    pred = Predictor(dim, out_dim=PATCH_DIM if variant == "pixel" else dim)
    teacher = copy.deepcopy(enc).requires_grad_(False) if variant == "ema" else None
    opt = torch.optim.AdamW(list(enc.parameters()) + list(pred.parameters()), lr=lr, weight_decay=0.05)
    history, start = [], time.time()
    for ep in range(epochs):
        perm = torch.randperm(len(xtr), generator=gen)
        losses = []
        for i in range(0, len(xtr), batch):
            x = xtr[perm[i:i + batch]]
            keep = sample_masks(len(x), gen)
            out = pred(enc(x, keep), keep)
            tgt_mask = ~keep
            if variant == "pixel":
                loss = F.mse_loss(out[tgt_mask], x[tgt_mask])
            else:
                if variant == "ema":
                    with torch.no_grad():
                        target = teacher(x)                       # teacher sees the full image
                else:
                    target = enc(x)                               # same encoder: gradients flow into the target too
                loss = F.smooth_l1_loss(out[tgt_mask], target[tgt_mask])
                if variant == "sigreg":                           # LeJEPA: (1 - w) * prediction + w * SIGReg
                    tokens = target.reshape(-1, target.shape[-1])  # every patch embedding should look N(0, I)
                    loss = (1 - sigreg_weight) * loss + sigreg_weight * sigreg(tokens, generator=gen) / len(tokens)
            opt.zero_grad()
            loss.backward()
            opt.step()
            if teacher is not None:
                with torch.no_grad():
                    for pt, ps in zip(teacher.parameters(), enc.parameters()):
                        pt.mul_(ema).add_(ps, alpha=1 - ema)
            losses.append(loss.item())
        with torch.no_grad():
            stats = collapse_stats(enc(xtr[:512]).mean(1))
        history.append({"epoch": ep + 1, "loss": float(np.mean(losses)), **stats})
        if log_every and (ep + 1) % log_every == 0:
            print(f"[{variant}] epoch {ep + 1}: loss {history[-1]['loss']:.4f}  std {stats['mean_std']:.3f}  "
                  f"rank {stats['effective_rank']:.1f}/{dim}")
    return {"encoder": enc.eval(), "history": history, "seconds": time.time() - start, "variant": variant}


@torch.no_grad()
def features(enc: Encoder | None, x: torch.Tensor) -> np.ndarray:
    """Frozen features: mean of patch embeddings (or raw pixels when enc is None)."""
    if enc is None:
        return x.reshape(len(x), -1).numpy()
    return enc(x).mean(1).numpy()


def linear_probe(enc: Encoder | None, data=None, seed: int = 7) -> float:
    """Accuracy of a logistic-regression probe on frozen features (the standard SSL evaluation)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    xtr, ytr, xte, yte = data or load_digits_patches(seed)
    sc = StandardScaler().fit(features(enc, xtr))
    clf = LogisticRegression(max_iter=3000).fit(sc.transform(features(enc, xtr)), ytr.numpy())
    return float(clf.score(sc.transform(features(enc, xte)), yte.numpy()))

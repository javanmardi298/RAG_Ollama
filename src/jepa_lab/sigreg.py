"""SIGReg (Sketched Isotropic Gaussian Regularization, LeJEPA: Balestriero & LeCun, arXiv 2511.08544).

Representation collapse = the encoder maps everything to (almost) the same point, so predicting embeddings
becomes trivially easy and useless. Older JEPAs prevent it with heuristics (EMA teacher, stop-gradient,
predictor tricks). LeJEPA shows the best target distribution for embeddings is an isotropic Gaussian and
enforces it directly: project embeddings on random directions and make each 1-D projection look like N(0,1)
by matching characteristic functions (Epps-Pulley test). Linear in batch size and dimension.
"""
from __future__ import annotations

import torch


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

# ساختن پروژه‌ی Mini I-JEPA روی ارقام دست‌نویس، از صفر در GitHub

یک JEPA کوچک را با PyTorch آموزش می‌دهی، چهار روش را با linear probe و دو baseline مقایسه می‌کنی و فروپاشی نمایش (collapse) را با عدد نشان می‌دهی. فقط CPU لازم است (چند دقیقه). مفهوم کامل: آموزش JEPA در repo آزمایشگاه (`docs/jepa.md`) و درس p17.

> نسخه‌ی تعاملی (تیک مراحل، مقایسه‌ی خروجی، پرسیدن از Claude، دانلود notebook): صفحه‌ی «راهنمای ساخت پروژه‌ها» (claude.ai artifact).

## مراحل
1. ساختن repo در GitHub
2. فایل .gitignore
3. فایل requirements.txt
4. فایل اصلی: jepa.py
5. فایل check_setup.py
6. تست‌ها: tests/test_jepa.py
7. تست خودکار در GitHub (Actions)
8. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
9. ساختن و اجرای notebook
10. اجرا در Colab (اختیاری)
11. commit و push از VS Code
12. README نهایی
13. صیقل نهایی repo

## 1. ساختن repo در GitHub
_GitHub · حدود 3 دقیقه_

**چرا:** repo خودت نمونه‌کار توست. یک پروژه‌ی پژوهشی کوچک و صادقانه (با baseline و تحلیل collapse) برای نقش‌های ML بسیار ارزشمند است.

1. در github.com بالا سمت راست **+** → **New repository**.
2. **Repository name:** `jepa_digits`
3. **Description:** `Mini I-JEPA in PyTorch on 8x8 digits: EMA teacher vs SIGReg vs pixel prediction, linear probes against baselines, and representation-collapse diagnostics`
4. **Public**، تیک **Add a README file**، **Add .gitignore:** None، **Choose a license:** MIT License → **Create repository**.

> **باید ببینی:** repo دو فایل دارد: `README.md` و `LICENSE`.

## 2. فایل .gitignore
_GitHub · حدود 2 دقیقه_

**چرا:** محیط مجازی، فایل‌های موقت و `.env` هرگز وارد repo نشوند.

1. **Add file** → **Create new file**، نام `.gitignore`، متن زیر. commit: `Add .gitignore`.

`.gitignore`

````
# Python and editors
.venv/
__pycache__/
.ipynb_checkpoints/
.pytest_cache/
.DS_Store

# secrets: API keys live here, never in git
.env
````

## 3. فایل requirements.txt
_GitHub · حدود 2 دقیقه_

**چرا:** numpy و scikit-learn (داده‌ی ارقام داخل sklearn است، بدون دانلود) و PyTorch. نسخه‌ی CPU کوچک‌تر است و کافی است.

1. **Add file → Create new file**، نام `requirements.txt`. commit: `Add requirements`.

`requirements.txt`

````
numpy>=1.24
scikit-learn>=1.3
torch>=2.2          # CPU is enough; smaller download on Windows/Linux: pip install torch --index-url https://download.pytorch.org/whl/cpu
pytest>=8.0
ipykernel>=6.29
````

## 4. فایل اصلی: jepa.py
_GitHub · حدود 5 دقیقه_

**چرا:** کل روش در یک فایل: SIGReg و آمار collapse، داده و patch ها، encoder و predictor (Transformer کوچک)، ماسک بلوکی، آموزش چهار روش، و linear probe. هر تکه را در درس p17 قدم‌به‌قدم دیده‌ای.

1. **Add file → Create new file**، نام `jepa.py`. commit: `Add mini I-JEPA: encoder, predictor, EMA, SIGReg, probes`.

`jepa.py`

````python
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
````

## 5. فایل check_setup.py
_GitHub · حدود 2 دقیقه_

**چرا:** قبل از notebook، یک epoch آموزش می‌دهد تا مطمئن شوی PyTorch و داده درست کار می‌کنند و زمان هر epoch روی لپ‌تاپت را ببینی.

1. **Add file → Create new file**، نام `check_setup.py`. commit: `Add setup check`.

`check_setup.py`

````python
"""Run once after installing: checks Python, PyTorch, the data and one training epoch."""
import sys

import torch

from jepa import linear_probe, load_digits_patches, train

print("Python", sys.version.split()[0], "| torch", torch.__version__.split("+")[0], "| GPU:", torch.cuda.is_available())
data = load_digits_patches()
print("train", tuple(data[0].shape), "test", tuple(data[2].shape))
r = train("ema", epochs=1, data=data)
print("one epoch:", round(r["seconds"], 1), "s, probe accuracy", round(linear_probe(r["encoder"], data), 2))
print("setup ok")
````

## 6. تست‌ها: tests/test_jepa.py
_GitHub · حدود 3 دقیقه_

**چرا:** تست‌های سریع: شکل ماسک و encoder، اینکه SIGReg توزیع گاوسی را به collapse ترجیح می‌دهد، و اینکه هر چهار روش یک epoch آموزش می‌بینند.

1. **Add file → Create new file**، نام `tests/test_jepa.py`. commit: `Add tests`.

`tests/test_jepa.py`

````python
import torch

from jepa import Encoder, collapse_stats, linear_probe, load_digits_patches, sample_masks, sigreg, train


def test_masks_hide_one_block():
    keep = sample_masks(5, torch.Generator().manual_seed(0))
    assert keep.shape == (5, 16) and (keep.sum(1) == 12).all()


def test_encoder_shape():
    x = load_digits_patches()[0][:3]
    assert Encoder(32)(x).shape == (3, 16, 32)


def test_sigreg_prefers_gaussian_and_stats_detect_collapse():
    g = torch.Generator().manual_seed(0)
    gauss = torch.randn(512, 16, generator=g)
    flat = 0.01 * torch.randn(512, 16, generator=g)
    assert sigreg(gauss, generator=g) < sigreg(flat, generator=g)
    assert collapse_stats(gauss)["mean_std"] > 0.5 > collapse_stats(flat)["mean_std"]


def test_every_variant_trains_one_epoch():
    data = load_digits_patches()
    small = (data[0][:256], data[1][:256], data[2][:128], data[3][:128])
    for v in ["ema", "sigreg", "naive", "pixel"]:
        assert train(v, epochs=1, dim=32, data=small)["history"][0]["loss"] >= 0
    assert 0 <= linear_probe(None, small) <= 1
````

## 7. تست خودکار در GitHub (Actions)
_GitHub · حدود 4 دقیقه_

**چرا:** با هر push تست‌ها روی ماشین تمیز اجرا می‌شوند. نسخه‌ی CPU مخصوص PyTorch نصب می‌شود تا سریع باشد.

1. **Add file → Create new file**، نام `.github/workflows/tests.yml`. commit: `Add CI`.
2. به تب **Actions** برو؛ اجرای اول چند دقیقه طول می‌کشد (نصب PyTorch).

`.github/workflows/tests.yml`

````
name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install torch --index-url https://download.pytorch.org/whl/cpu
      - run: pip install -r requirements.txt
      - run: python check_setup.py
      - run: pytest -q
````

> **باید ببینی:** اجرای `tests` با تیک سبز.

## 8. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
_VS Code · حدود 10 دقیقه_

**چرا:** محیط مجازی جدا برای این پروژه؛ PyTorch را اول از نسخه‌ی CPU نصب می‌کنیم که کوچک‌تر است.

پیش‌نیاز: Git، Python 3.10+، و افزونه‌های **Python** و **Jupyter** در VS Code.

1. VS Code: `Ctrl+Shift+P` → **Git: Clone** → `https://github.com/<نام-کاربری-تو>/jepa_digits.git` → **Open**.
2. ترمینال: ``Ctrl+` ``

_ترمینال VS Code · Windows PowerShell_

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

_ترمینال VS Code_

```
python check_setup.py
python -m pytest -q
```

**باید ببینی:**

```
Python 3.x.y | torch 2.14.1 | GPU: False
train (1347, 16, 4) test (450, 16, 4)
one epoch: 0.5 s, probe accuracy 0.84
setup ok

....                                                                     [100%]
4 passed
```

> **حواست باشد:** عدد «one epoch» و دقت probe روی سیستم تو کمی فرق دارد؛ مهم «setup ok» و «passed» است. اگر یک epoch بیش از ۱۰ ثانیه طول کشید، در notebook عدد `EPOCHS` را کم کن یا Colab را امتحان کن.

## 9. ساختن و اجرای notebook
_VS Code · حدود 15 دقیقه_

**چرا:** notebook داستان پژوهش است: داده و ماسک، آموزش، جدول probe با baseline ها، تحلیل collapse و حکم صادقانه. با خروجی‌هایش در GitHub دیده می‌شود.

1. VS Code: `Ctrl+Shift+P` → **Create: New Jupyter Notebook** → ذخیره با نام `01_jepa_digits.ipynb` در پوشه‌ی repo.
2. **Select Kernel → Python Environments → .venv**.
3. سلول‌ها را به ترتیب بساز و اجرا کن (`Shift+Enter`) و خروجی را با «باید ببینی» مقایسه کن.

_سلول متنی (Markdown):_

````markdown
# Mini I-JEPA on handwritten digits

JEPA (Joint-Embedding Predictive Architecture) predicts the **embeddings** of hidden image patches from the visible
ones, instead of the pixels. This notebook trains four variants with the same budget on 8x8 digits (sklearn, no
download), measures them with a linear probe against two baselines, and checks for representation collapse.
Runs on a laptop CPU in a few minutes.
````

_سلول کد 1:_

```python
import torch
from jepa import GRID, linear_probe, load_digits_patches, sample_masks

data = load_digits_patches()
print("train", tuple(data[0].shape), "test", tuple(data[2].shape), "(images, patches, pixels per patch)")
img = data[0][3].reshape(GRID, GRID, 2, 2).permute(0, 2, 1, 3).reshape(8, 8)
print("\n".join("".join("#" if v > 0.4 else "." for v in row) for row in img))
keep = sample_masks(1, torch.Generator().manual_seed(0))[0].reshape(GRID, GRID)
print("\nmask (X = hidden patches the model must predict):")
print("\n".join("".join("." if k else "X" for k in row) for row in keep))
```

یک رقم و ماسک: یک بلوک ۲×۲ از ۱۶ patch پنهان می‌شود و مدل باید embedding آن را از بقیه حدس بزند.

**باید ببینی:**

```
train (1347, 16, 4) test (450, 16, 4) (images, patches, pixels per patch)
....##..
...##...
..##..#.
.##..##.
.#####..
..####..
....#...
....#...

mask (X = hidden patches the model must predict):
....
....
XX..
XX..
```

_سلول متنی (Markdown):_

````markdown
## Train four variants on two seeds
Same encoder, same epochs. Baselines: raw pixels (no encoder) and a random, untrained encoder.
````

_سلول کد 2:_

```python
import time
from jepa import Encoder, train

EPOCHS, SEEDS = 20, [7, 8]
rows, histories, start = [], {}, time.time()
for seed in SEEDS:
    d = load_digits_patches(seed)
    torch.manual_seed(seed)
    rows.append({"run": "raw_pixels", "seed": seed, "probe": linear_probe(None, d)})
    rows.append({"run": "random_encoder", "seed": seed, "probe": linear_probe(Encoder(64).eval(), d)})
    for variant in ["ema", "sigreg", "pixel", "naive"]:
        r = train(variant, epochs=EPOCHS, seed=seed, data=d)
        rows.append({"run": variant, "seed": seed, "probe": linear_probe(r["encoder"], d)})
        histories[(variant, seed)] = r["history"][-1]
print(f"{len(rows)} runs in {time.time() - start:.0f} s")
```

۴ روش × ۲ seed آموزش می‌بیند. روی CPU لپ‌تاپ حدود ۱ تا ۳ دقیقه.

**باید ببینی:**

```
12 runs in 92 s
```

_سلول متنی (Markdown):_

````markdown
## Linear-probe accuracy (mean and range over seeds)
````

_سلول کد 3:_

```python
summary = {}
for name in dict.fromkeys(r["run"] for r in rows):
    v = [r["probe"] for r in rows if r["run"] == name]
    summary[name] = {"mean": round(sum(v) / len(v), 3), "min": round(min(v), 3), "max": round(max(v), 3)}
for name, s in sorted(summary.items(), key=lambda kv: -kv[1]["mean"]):
    print(f"{name:15s} {s['mean']:.3f}  [{s['min']:.3f}, {s['max']:.3f}]")
```

جدول اصلی. عددهای تو کمی فرق دارد (تصادف آموزش). پیکسل خام بالاتر از همه است، چون ارقام ۸×۸ ساده‌اند. **دام مهم:** `naive` ممکن است بالا بیاید، با اینکه collapse کرده! probe خطی با StandardScaler تفاوت‌های بسیار ریز را بزرگ می‌کند. سلول بعد نشان می‌دهد چرا نباید به این عدد اعتماد کرد.

**باید ببینی:**

```
raw_pixels      0.968  [0.964, 0.971]
naive           0.832  [0.811, 0.853]
ema             0.818  [0.798, 0.838]
random_encoder  0.807  [0.784, 0.829]
pixel           0.780  [0.776, 0.784]
sigreg          0.773  [0.662, 0.884]
```

_سلول متنی (Markdown):_

````markdown
## Collapse check
A near-zero loss with a tiny spread of embeddings (`mean_std`) means the encoder ignores its input.
````

_سلول کد 4:_

```python
print(f"{'variant':8s} {'loss':>8s} {'mean_std':>9s} {'eff.rank':>9s}")
for variant in ["ema", "sigreg", "pixel", "naive"]:
    h = histories[(variant, SEEDS[0])]
    print(f"{variant:8s} {h['loss']:8.4f} {h['mean_std']:9.4f} {h['effective_rank']:9.1f}")
```

`naive` کمترین loss و کمترین پراکندگی را دارد: collapse. به loss پایین اعتماد نکن؛ پراکندگی را هم ببین.

**باید ببینی:**

```
variant      loss  mean_std  eff.rank
ema        0.0064    0.0233      10.7
sigreg     0.0873    0.1213      19.5
pixel      0.0911    0.0744      10.9
naive      0.0003    0.0055      14.3
```

_سلول متنی (Markdown):_

````markdown
## Verdict (rules fixed before looking at the numbers)
````

_سلول کد 5:_

```python
import json, os

collapsed = [v for v in ["ema", "sigreg", "pixel", "naive"] if histories[(v, SEEDS[0])]["mean_std"] < 0.01]
learned = {k: v for k, v in summary.items() if k not in ("raw_pixels", "random_encoder", *collapsed)}
best = max(learned, key=lambda k: learned[k]["mean"])
verdict = {"collapsed": collapsed, "best_learned": best,
           "pixels_win": summary["raw_pixels"]["mean"] >= learned[best]["mean"],
           "beats_random": [k for k, v in learned.items() if v["mean"] >= summary["random_encoder"]["mean"] + 0.02],
           "unstable": [k for k, v in learned.items() if v["max"] - v["min"] > 0.1]}
print(verdict)
os.makedirs("results", exist_ok=True)
with open("results/results.json", "w") as f:
    json.dump({"summary": summary, "verdict": verdict, "epochs": EPOCHS, "seeds": SEEDS}, f, indent=2)
```

حکم قاعده‌مند: کدام روش collapse کرده (و از رقابت حذف می‌شود)، آیا پیکسل خام بهتر است، کدام روش حداقل ۰٫۰۲ از encoder تصادفی بهتر است، و کدام بین seed ها ناپایدار است. ذخیره در `results/results.json`.

**باید ببینی:**

```
{'collapsed': ['naive'], 'best_learned': 'ema', 'pixels_win': True, 'beats_random': [], 'unstable': ['sigreg']}
```

_سلول متنی (Markdown):_

````markdown
## What this shows and limitations
- On tiny, almost linearly separable 8x8 digits raw pixels win; the value of JEPA appears with large, detailed data
  (images, video) and in world models. Report it honestly.
- Two seeds and 20 epochs: results move between runs; use more seeds before claiming a difference.
- CPU-sized model (64-dim, 2 layers).
````

> **نکته:** عددهای آموزش تصادفی‌اند: عدد تو با «باید ببینی» دقیقاً یکی نیست، ولی ترتیب کلی و برچسب‌ها باید شبیه باشد. دکمه‌ی «مقایسه» فقط بخش اصلی را بررسی می‌کند.

## 10. اجرا در Colab (اختیاری)
_Colab · GitHub · حدود 5 دقیقه_

**چرا:** اگر لپ‌تاپ کند است. Colab خودش PyTorch دارد.

1. در GitHub، `01_jepa_digits.ipynb` را باز کن (بعد از مرحله‌ی ۱۱ push شده) و آدرس را در colab.research.google.com → **GitHub** paste کن.
2. یک سلول در بالا اضافه کن و اجرا کن (با نام کاربری خودت):

_اولین سلول در Colab_

```
!git clone https://github.com/<نام-کاربری-تو>/jepa_digits.git
%cd jepa_digits
```

> **حواست باشد:** Colab رایگان اگر بی‌کار بماند قطع می‌شود. برای ذخیره: **File → Save a copy in GitHub**.

## 11. commit و push از VS Code
_VS Code · GitHub · حدود 3 دقیقه_

**چرا:** notebook با خروجی‌ها و `results/results.json` باید در GitHub باشند.

1. Source Control: `Ctrl+Shift+G` → فایل‌های `01_jepa_digits.ipynb` و `results/results.json`.
2. پیام: `Add notebook: JEPA variants vs baselines and collapse check` → **Commit** → **Sync Changes**.

> **باید ببینی:** در GitHub، notebook با جدول‌ها و خروجی‌ها دیده می‌شود.

## 12. README نهایی
_GitHub · حدود 10 دقیقه_

**چرا:** README در ۳۰ ثانیه می‌گوید چه کردی، با چه baseline هایی و نتیجه‌ی صادقانه چه بود. عددها را از `results/results.json` خودت بردار.

1. در GitHub: `README.md` → مداد → متن زیر، عددهای `{...}` را پر کن (یا results.json را پایین paste کن). commit: `Write README`.

````markdown
# Mini I-JEPA on handwritten digits

![tests](https://github.com/<your-user>/jepa_digits/actions/workflows/tests.yml/badge.svg)

JEPA (Joint-Embedding Predictive Architecture) learns by predicting the **embeddings** of hidden image patches from
the visible ones. Four variants are trained with the same budget on 8x8 digits and evaluated with a linear probe on
the frozen encoder, against raw pixels and a random encoder. Collapse is measured, not assumed.

| run | linear-probe accuracy (mean over {seeds} seeds) |
|---|---|
| raw pixels (baseline) | {raw} |
| random encoder (baseline) | {random} |
| I-JEPA (EMA teacher) | {ema} |
| SIGReg (LeJEPA-style, no teacher) | {sigreg} |
| pixel prediction (MAE-like) | {pixel} |
| naive (collapsed: embedding spread ~0, excluded from the verdict) | {naive} |

**Honest reading:** on tiny 8x8 digits raw pixels win, and the collapsed naive encoder can still score well on a standardised linear probe, which is why collapse is checked with the embedding spread, not the probe; the point is the method, the collapse diagnostics and the
comparison against baselines. JEPA pays off on large, detailed data (images, video) and in world models.

## Run it (CPU, a few minutes)
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_jepa_digits.ipynb` and run all cells.

## References
I-JEPA (arXiv 2301.08243), LeJEPA / SIGReg (arXiv 2511.08544), V-JEPA 2 (arXiv 2506.09985).

## Licence
MIT
````

## 13. صیقل نهایی repo
_GitHub · حدود 5 دقیقه_

**چرا:** جزئیاتی که repo را حرفه‌ای نشان می‌دهد.

1. About → Topics: `self-supervised-learning`, `jepa`, `pytorch`, `representation-learning`.
2. repo را در پروفایل pin کن.
3. خط رزومه (پایین).

**خط رزومه:** Implemented a mini I-JEPA in PyTorch (masked latent prediction with an EMA teacher, a SIGReg variant and a pixel-prediction baseline), evaluated with linear probes against raw-pixel and random-encoder baselines over {seeds} seeds, with representation-collapse diagnostics.

## اگر به خطا خوردی
- **`pip install torch` خیلی طول می‌کشد**: از دستور نسخه‌ی CPU استفاده کن (`--index-url https://download.pytorch.org/whl/cpu`)؛ نسخه‌ی پیش‌فرض خیلی بزرگ‌تر است.
- **`No module named jepa` در notebook**: notebook باید کنار `jepa.py` باشد و kernel روی `.venv`.
- **آموزش خیلی کند است**: `EPOCHS` را ۱۰ کن، یا فقط یک seed، یا Colab.
- **عددهای من با «باید ببینی» فرق دارد**: طبیعی است (تصادف آموزش). مهم: پیکسل خام بالا، naive با mean_std نزدیک صفر، و برچسب‌های verdict.
- **تب Actions قرمز است**: روی اجرای قرمز کلیک کن؛ معمولاً نام یا مسیر فایل اشتباه است.

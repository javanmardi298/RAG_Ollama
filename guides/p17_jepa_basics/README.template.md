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

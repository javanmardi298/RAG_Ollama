# Starter: JEPA self-supervised learning on 8x8 digits (src/jepa_lab, tutorial in docs/jepa.md, steps 3-4).
#   python run.py            compares the variants in config.yaml with a linear probe over several seeds
#   python run.py --quick    1 epoch, one seed: checks the setup in seconds
# config.yaml: variants / seeds / epochs / dim / mask_block, or sigreg_weights for a SIGReg sweep (preset p18).
# Needs PyTorch: pip install -r requirements-jepa.txt (from the repo root).
import os, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
(HERE / "results").mkdir(exist_ok=True)
try:
    import torch
except ImportError:
    raise SystemExit("PyTorch is missing: pip install -r requirements-jepa.txt") from None
from jepa_lab import ssl as jssl
from jepa_lab.ssl import Encoder, linear_probe, load_digits_patches, train

quick = "--quick" in sys.argv
epochs = 1 if quick else int(cfg.get("epochs", 40))
seeds = [7] if quick else list(cfg.get("seeds", [7, 8, 9]))
dim = int(cfg.get("dim", 64))
if cfg.get("mask_block"):
    _orig = jssl.sample_masks
    jssl.sample_masks = lambda b, gen, block=int(cfg["mask_block"]): _orig(b, gen, block)
if "sigreg_weights" in cfg:                                         # p18: collapse and the SIGReg weight sweep
    runs = [("naive", {}), ("ema", {"ema": float(cfg.get("ema", 0.99))})] + \
           [("sigreg", {"sigreg_weight": float(w)}) for w in cfg["sigreg_weights"]]
else:
    runs = [(v, {}) for v in cfg.get("variants", ["ema", "sigreg", "pixel"])]

rows = []
for seed in seeds:
    data = load_digits_patches(seed)
    torch.manual_seed(seed)
    rows.append({"seed": seed, "run": "raw_pixels", "probe": linear_probe(None, data)})
    rows.append({"seed": seed, "run": "random_encoder", "probe": linear_probe(Encoder(dim).eval(), data)})
    for variant, kw in runs:
        r = train(variant, epochs=epochs, dim=dim, seed=seed, data=data, **kw)
        h = r["history"][-1]
        name = variant + "".join(f" {k}={v}" for k, v in kw.items())
        rows.append({"seed": seed, "run": name, "probe": linear_probe(r["encoder"], data), "loss": h["loss"],
                     "mean_std": h["mean_std"], "effective_rank": h["effective_rank"], "seconds": r["seconds"]})
        print(f"seed {seed} {name:22s} probe {rows[-1]['probe']:.3f}  loss {h['loss']:.4f}  std {h['mean_std']:.3f}  "
              f"rank {h['effective_rank']:.1f}/{dim}")

print("\nprobe accuracy, mean [min, max] over seeds:")
for name in dict.fromkeys(r["run"] for r in rows):
    v = [r["probe"] for r in rows if r["run"] == name]
    print(f"  {name:22s} {sum(v) / len(v):.3f} [{min(v):.3f}, {max(v):.3f}]")
print("Collapse check: loss near 0 with mean_std near 0 means the encoder ignores its input (docs/jepa.md, step 4).")
(HERE / "results" / "jepa.json").write_text(json.dumps({"config": cfg, "epochs": epochs, "rows": rows}, indent=2))

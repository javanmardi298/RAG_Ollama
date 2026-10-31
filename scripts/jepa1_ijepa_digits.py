# JEPA 1: I-JEPA in miniature. Hide patches of a digit, predict their EMBEDDINGS (not pixels), then test the frozen
# encoder with a linear probe. Compares: ema (I-JEPA teacher), sigreg (LeJEPA, no teacher), pixel (MAE-like),
# and two baselines (raw pixels, a random untrained encoder). CPU, about 2 minutes per seed.
# Usage: python scripts/jepa1_ijepa_digits.py [--epochs 40] [--seeds 7 8]
# %%
import argparse, json, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from jepa_lab.ssl import Encoder, linear_probe, load_digits_patches, train

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=40)
ap.add_argument("--seeds", type=int, nargs="+", default=[7, 8])
ap.add_argument("--variants", nargs="+", default=["ema", "sigreg", "pixel"])
args = ap.parse_args()

# %%
rows = {"raw_pixels": [], "random_encoder": [], **{v: [] for v in args.variants}}
details = []
for seed in args.seeds:
    data = load_digits_patches(seed)
    rows["raw_pixels"].append(linear_probe(None, data))
    import torch; torch.manual_seed(seed)
    rows["random_encoder"].append(linear_probe(Encoder(64).eval(), data))
    for v in args.variants:
        r = train(v, epochs=args.epochs, seed=seed, data=data)
        acc = linear_probe(r["encoder"], data)
        rows[v].append(acc)
        details.append({"seed": seed, "variant": v, "probe_acc": acc, "seconds": round(r["seconds"], 1),
                        "final": r["history"][-1]})
        print(f"seed {seed} {v:7s} probe {acc:.3f}  rank {r['history'][-1]['effective_rank']:.1f}  {r['seconds']:.0f}s")

# %%
summary = {k: {"mean": statistics.mean(v), "min": min(v), "max": max(v)} for k, v in rows.items()}
print("\nlinear-probe accuracy (mean over seeds):")
for k, s in sorted(summary.items(), key=lambda kv: -kv[1]["mean"]):
    print(f"  {k:15s} {s['mean']:.3f}  [{s['min']:.3f}, {s['max']:.3f}]")
print("\nRead it honestly: on 8x8 digits raw pixels are already linearly separable, so they win. The lesson is the\n"
      "ranking among LEARNED encoders and the gap over a random encoder; JEPA pays off with big, redundant data\n"
      "(images, video) where pixels are mostly unpredictable detail. See docs/jepa.md, step 3.")
out = ROOT / "results" / "jepa1_ijepa_digits.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"args": vars(args), "summary": summary, "runs": details}, indent=2))
print("saved", out)

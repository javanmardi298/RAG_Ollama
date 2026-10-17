# JEPA 2: representation collapse, the central failure of joint-embedding methods, and three cures.
# naive  : no teacher, no regulariser -> the loss goes to ~0 while the embeddings stop depending on the input
# ema    : I-JEPA / BYOL cure (slow teacher copy, no gradient into targets)
# sigreg : LeJEPA cure (make embeddings look like an isotropic Gaussian, one hyper-parameter)
# Watch mean_std (spread of embeddings across images) and effective_rank, not just the loss.
# Usage: python scripts/jepa2_collapse.py [--epochs 40]
# %%
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from jepa_lab.ssl import linear_probe, load_digits_patches, train

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=40)
args = ap.parse_args()
data = load_digits_patches()

# %%
out = {}
for v in ["naive", "ema", "sigreg"]:
    r = train(v, epochs=args.epochs, data=data, log_every=10)
    out[v] = {"history": r["history"], "probe_acc": linear_probe(r["encoder"], data)}

# %%
print(f"\n{'variant':8s} {'loss':>8s} {'mean_std':>9s} {'eff.rank':>9s} {'probe':>6s}")
for v, o in out.items():
    h = o["history"][-1]
    print(f"{v:8s} {h['loss']:8.4f} {h['mean_std']:9.4f} {h['effective_rank']:9.1f} {o['probe_acc']:6.3f}")
print("\nA near-zero loss with a tiny mean_std is the signature of collapse. Note the probe can still look fine because\n"
      "StandardScaler blows tiny differences back up: always check the spread itself (docs/jepa.md, step 4).")
p = ROOT / "results" / "jepa2_collapse.json"
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps(out, indent=2))
print("saved", p)

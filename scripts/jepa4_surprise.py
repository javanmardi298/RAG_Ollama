# JEPA 4: "surprise" = world-model prediction error, used as an anomaly / safety signal.
# Normal moves are predictable; teleports (physically impossible jumps) are not. ROC AUC measures how well the
# error separates them. The same idea flags violations of intuitive physics in V-JEPA and LeWorldModel, and in
# industry: unexpected sensor readings, a process step that did not have its usual effect, a robot slipping.
# Usage: python scripts/jepa4_surprise.py [--epochs 40] [--teleport-rate 0.1]
# %%
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from jepa_lab.world_model import DotWorld, surprise_auc, train_world_model

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=40)
ap.add_argument("--teleport-rate", type=float, default=0.1)
ap.add_argument("--noise", type=float, default=0.0, help="pixel noise at test time (robustness check)")
args = ap.parse_args()

# %%
r = train_world_model(epochs=args.epochs)
test_world = DotWorld(seed=123, noise=args.noise)            # fresh episodes, optionally noisy camera
s = surprise_auc(r["model"], test_world, teleport_rate=args.teleport_rate)
print(f"ROC AUC {s['auc']:.3f}  mean error normal {s['mean_error_normal']:.4f}  teleport {s['mean_error_teleport']:.4f}")
print("Pick an alert threshold on a validation set at the false-alarm rate you can afford (same idea as stage 4).")
p = ROOT / "results" / "jepa4_surprise.json"
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps({"args": vars(args), **s}, indent=2))
print("saved", p)

# Starter: latent world model + decisions (src/jepa_lab/world_model.py, docs/jepa.md steps 5-6).
#   python run.py                 train, then plan (cem vs random vs oracle) and score surprise
#   python run.py --stage plan    or --stage surprise; reuses results/world_model.pt if present
#   python run.py --quick         tiny run to check the setup
# Needs PyTorch: pip install -r requirements-jepa.txt (from the repo root).
import argparse
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
import numpy as np
from jepa_lab import world_model as wm

ap = argparse.ArgumentParser()
ap.add_argument("--stage", choices=["all", "train", "plan", "surprise"], default=cfg.get("stage", "all"))
ap.add_argument("--quick", action="store_true")
args = ap.parse_args()
epochs = 3 if args.quick else int(cfg.get("epochs", 40))
episodes = 4 if args.quick else int(cfg.get("episodes", 30))
z_dim = int(cfg.get("z_dim", 16))
ckpt = HERE / "results" / "world_model.pt"
out = {"config": cfg}

if args.stage in ("all", "train") or not ckpt.exists():
    r = wm.train_world_model(n=1500 if args.quick else 6000, epochs=epochs, z_dim=z_dim,
                             sigreg_weight=float(cfg.get("sigreg_weight", 1.0)), log_every=0 if args.quick else 10)
    model, world = r["model"], r["world"]
    torch.save(model.state_dict(), ckpt)
    out["train"] = r["history"][-1]
    out["position_probe_r2"] = wm.probe_position(model, world)
    print("trained:", {k: round(v, 4) for k, v in out["train"].items() if isinstance(v, float)},
          "position R2", round(out["position_probe_r2"], 3))
else:
    model, world = wm.WorldModel(z_dim), wm.DotWorld(0)
    model.load_state_dict(torch.load(ckpt))
    model.eval()

if args.stage in ("all", "plan"):
    plan_kw = {k: int(cfg[k]) for k in ("horizon", "samples", "elites", "iters") if k in cfg}
    if plan_kw:                                                      # route config.yaml values into the planner
        _cem = wm.cem_plan
        wm.cem_plan = lambda m, z0, zg, gen=None, **kw: _cem(m, z0, zg, gen=gen, **{**plan_kw, **kw})
    out["planning"] = {}
    for p in ["cem", "random", "oracle"]:
        res = wm.evaluate_planning(model, world, episodes=episodes, planner=p)
        out["planning"][p] = res
        print(f"planner {p:6s} success {res['success_rate']:.2f}  final distance {res['mean_final_distance']:.3f}")

if args.stage in ("all", "surprise"):
    s = wm.surprise_auc(model, wm.DotWorld(seed=123, noise=float(cfg.get("noise", 0.0))), n=500 if args.quick else 2000,
                        teleport_rate=float(cfg.get("teleport_rate", 0.1)))
    # alert threshold at the target false-alarm rate, chosen on fresh validation episodes (never on the test set)
    o, a, o2, _, _, tele = wm.DotWorld(seed=321).transitions(1000, 0.0)
    with torch.no_grad():
        err = ((model.predict(model.encoder(o), a) - model.encoder(o2)) ** 2).sum(-1).numpy()
    s["threshold"] = float(np.quantile(err, 1 - float(cfg.get("target_fpr", 0.01))))
    out["surprise"] = s
    print(f"surprise AUC {s['auc']:.3f}  alert threshold {s['threshold']:.4f} (FPR target {cfg.get('target_fpr', 0.01)})")

(HERE / "results" / "world_model.json").write_text(json.dumps(out, indent=2))

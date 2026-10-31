# JEPA 3: a latent world model used for DECISIONS. Learn encoder(image)->z and predictor(z, action)->next z from
# random interaction data only (no rewards, no labels), then plan towards a goal IMAGE with CEM + MPC in latent
# space (the V-JEPA 2-AC / LeWorldModel recipe). Also trains the same model without SIGReg to show collapse.
# Usage: python scripts/jepa3_world_model_planning.py [--epochs 40] [--episodes 30]
# %%
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from jepa_lab.world_model import evaluate_planning, probe_position, train_world_model

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=40)
ap.add_argument("--episodes", type=int, default=30)
ap.add_argument("--sigreg-weight", type=float, default=1.0)
args = ap.parse_args()

# %%
res = {}
for name, w in [("with_sigreg", args.sigreg_weight), ("no_sigreg", 0.0)]:
    r = train_world_model(epochs=args.epochs, sigreg_weight=w, log_every=10)
    m, world = r["model"], r["world"]
    res[name] = {"final": r["history"][-1], "position_probe_r2": probe_position(m, world),
                 "planning": {p: evaluate_planning(m, world, episodes=args.episodes, planner=p)
                              for p in (["cem", "random", "oracle"] if name == "with_sigreg" else ["cem"])}}
    print(name, "probe R2", round(res[name]["position_probe_r2"], 3),
          {p: v["success_rate"] for p, v in res[name]["planning"].items()})

# %%
print("\nsuccess rate = reached the goal within 25 steps.  oracle knows true positions (upper bound), random is the floor.")
print("The planner never saw a reward: it only compares predicted embeddings with the goal image's embedding.")
print("Without SIGReg the latent collapses (loss ~0) and planning drops to the random level.")
p = ROOT / "results" / "jepa3_world_model.json"
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps({"args": vars(args), **res}, indent=2))
print("saved", p)

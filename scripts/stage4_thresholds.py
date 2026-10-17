# Stage 4: choose confidence thresholds from data.
# %%
import json, sys, joblib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np, matplotlib.pyplot as plt
from support.config import RESULTS_DIR, intent_map
from support.decision import risk_coverage, choose_threshold, choose_threshold_by_cost
from support.intents import load_splits, apply_temperature

dev = load_splits()["dev"]
model = joblib.load(RESULTS_DIR / "intent_model.joblib")
T = float((RESULTS_DIR / "temperature.txt").read_text())
proba = apply_temperature(model.predict_proba(dev.text), T)
conf, pred = proba.max(1), model.classes_[proba.argmax(1)]
correct = pred == dev.intent.to_numpy()

# %% One threshold per risk level: stricter error budget for riskier intents
budgets = {"low": 0.05, "medium": 0.02, "high": 0.01}
risk = np.array([intent_map().get(p, {"risk": "low"})["risk"] for p in pred])
chosen = {lvl: choose_threshold(conf[risk == lvl], correct[risk == lvl], budgets[lvl]) for lvl in budgets}
print(json.dumps(chosen, indent=2))
print("cost-based (wrong action = 20, handoff = 1):", choose_threshold_by_cost(conf, correct, 20, 1))

# %% Risk-coverage curve: the picture to put in the README
rc = risk_coverage(conf, correct)
plt.plot([r["coverage"] for r in rc], [r["error"] for r in rc])
plt.xlabel("coverage (share handled automatically)"); plt.ylabel("error among handled"); plt.title("Risk-coverage on dev")
plt.savefig(RESULTS_DIR / "risk_coverage.png", dpi=150, bbox_inches="tight")
(RESULTS_DIR / "thresholds.json").write_text(json.dumps({k: v["threshold"] for k, v in chosen.items()}))

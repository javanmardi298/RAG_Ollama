# Stage 4: choose confidence thresholds from data.
# Parameters: configs/project.yaml -> decision.* (error budget per risk level, costs)
# %%
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import matplotlib
matplotlib.use("Agg")                      # no window: the picture is saved to results/
import numpy as np, matplotlib.pyplot as plt
from support.config import RESULTS_DIR, intent_map
from support.decision import risk_coverage, choose_threshold, choose_threshold_by_cost
from support.intents import apply_temperature, load_clinc_oos, load_splits, with_oos
from support.runtime import load_classifier
from support.settings import error_budgets, settings

D = settings().decision
# Out-of-scope messages are part of real traffic and the main source of low confidence: keep them in dev.
dev = with_oos(load_splits(), load_clinc_oos(settings().data.clinc_json or None))["dev"]
clf = load_classifier()
proba = apply_temperature(clf.model.predict_proba(dev.text), clf.temperature)
conf, pred = proba.max(1), clf.model.classes_[proba.argmax(1)]
correct = pred == dev.intent.to_numpy()

# %% One threshold per risk level: stricter error budget for riskier intents
budgets = error_budgets()
risk = np.array([intent_map().get(p, {"risk": "low"})["risk"] for p in pred])
chosen = {lvl: choose_threshold(conf[risk == lvl], correct[risk == lvl], budgets[lvl]) for lvl in budgets}
print(json.dumps(chosen, indent=2))
by_cost = choose_threshold_by_cost(conf, correct, D.cost_wrong_action, D.cost_handoff)
print(f"cost-based (wrong action = {D.cost_wrong_action}, handoff = {D.cost_handoff}):", by_cost)

# %% Risk-coverage curve: the picture to put in the README
rc = risk_coverage(conf, correct)
plt.plot([r["coverage"] for r in rc], [r["error"] for r in rc])
plt.xlabel("coverage (share handled automatically)"); plt.ylabel("error among handled"); plt.title("Risk-coverage on dev")
plt.savefig(RESULTS_DIR / "risk_coverage.png", dpi=150, bbox_inches="tight")
(RESULTS_DIR / "thresholds.json").write_text(json.dumps({k: v["threshold"] for k, v in chosen.items()}))

# Overall effect of the chosen thresholds on dev (automation and its error, reported TOGETHER)
thr = np.array([chosen[r]["threshold"] for r in risk])
auto = conf >= thr
step = max(1, len(rc) // 200)               # the panel draws the curve from these points
summary = {"budgets": budgets, "chosen": chosen, "cost_based": by_cost,
           "dev_automation_rate": float(auto.mean()),
           "dev_error_among_automated": float(1 - correct[auto].mean()) if auto.any() else 0.0,
           "curve": rc[::step]}
(RESULTS_DIR / "stage4_thresholds.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(f"dev: automation {summary['dev_automation_rate']:.1%}, error among automated "
      f"{summary['dev_error_among_automated']:.2%}")

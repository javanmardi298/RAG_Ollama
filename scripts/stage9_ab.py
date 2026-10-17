# Stage 9: plan and read out an A/B test (inputs from configs/project.yaml -> experiments.*).
# Order matters: 1) sample size BEFORE the test, 2) stable assignment, 3) SRM check, 4) primary + guardrail metrics.
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.config import RESULTS_DIR
from support.experiments import assign, readout, sample_size_per_arm, srm_check
from support.settings import settings

X = settings().experiments
# 1. Before: how many conversations do we need to see the lift we care about?
n_needed = sample_size_per_arm(X.baseline_rate, X.min_detectable_lift, X.alpha, X.power)
print(f"per arm: {n_needed} conversations to detect +{X.min_detectable_lift:.1%} from {X.baseline_rate:.0%}")
# 2. Assignment is a pure function of the session id (same user -> same arm, no database)
demo = {f"session-{i}": assign(f"session-{i}", X.name) for i in range(8)}
print(demo)
# 3 + 4. Readout
arms = {"control": {"n": X.control_n, "automated": X.control_automated, "false_automation": X.control_false_automation},
        "treatment": {"n": X.treatment_n, "automated": X.treatment_automated,
                      "false_automation": X.treatment_false_automation}}
result = readout(arms, primary="automated", guardrails={"false_automation": X.max_false_automation_increase})
result["srm"] = srm_check({a: v["n"] for a, v in arms.items()}, threshold=X.srm_threshold)
result["ship"] = result["ship"] and not result["srm"]["mismatch"]
underpowered = min(X.control_n, X.treatment_n) < n_needed
print(json.dumps(result, indent=2))
if underpowered:
    print(f"WARNING: fewer than {n_needed} conversations per arm: a non-significant result says little.")
(RESULTS_DIR / "stage9_ab.json").write_text(json.dumps(
    {"n_needed_per_arm": n_needed, "underpowered": underpowered, "assignment_demo": demo, "arms": arms, **result},
    indent=2), encoding="utf-8")

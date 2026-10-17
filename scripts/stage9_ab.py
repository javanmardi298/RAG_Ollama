# Stage 9: plan and read out an A/B test (here simulated with the stage 6 harness: arm A vs arm B config).
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.experiments import assign, sample_size_per_arm, readout

# 1. Before: how many conversations do we need to see +3 points automation (from 60 %)?
print("per arm:", sample_size_per_arm(0.60, 0.03))
# 2. Assignment is a pure function of the session id
print([assign(f"session-{i}", "prompt_v2") for i in range(8)])
# 3. Readout (numbers from a real or simulated run)
arms = {"control": {"n": 4200, "automated": 2520, "false_automation": 63},
        "treatment": {"n": 4180, "automated": 2650, "false_automation": 71}}
print(readout(arms, primary="automated", guardrails={"false_automation": 0.005}))

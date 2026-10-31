# Starter: agent reliability with pass^k (labkit.metrics.reliability_report, the tau-bench metric).
#   python run.py     1) if the support agent's stage 6 ran with evaluation.repeats > 1, reads its reliability numbers;
#                     2) always runs a small offline demo: a "flaky" agent whose per-run success differs by scenario,
#                        so you can see why pass@1 looks fine while pass^k (all k runs succeed) collapses.
import random
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
from labkit.metrics import reliability_report

stage6 = ROOT / "results" / "stage6_eval.json"
if stage6.exists():
    rel = json.loads(stage6.read_text(encoding="utf-8")).get("summary", {}).get("reliability")
    print("support agent (stage 6):", rel or "ran with repeats=1; set evaluation.repeats: 4 in configs/project.yaml")

k = int(cfg.get("repeats", 4))
n = int(cfg.get("n_scenarios", 30))
rng = random.Random(0)
# Final-state check: a run succeeds only if the database ends in the expected state, not if the reply "sounds right".
# Most scenarios are easy (p=0.97), some are brittle (p=0.6): an ambiguous request, a tool that times out, ...
p_success = [0.97 if i % 4 else 0.6 for i in range(n)]
successes = {f"s{i:02d}": [rng.random() < p for _ in range(k)] for i, p in enumerate(p_success)}
rep = reliability_report(successes)
print(f"\noffline demo: {n} scenarios x {k} runs")
for j in range(1, k + 1):
    print(f"  k={j}  pass@k {rep[f'pass@{j}']:.3f}   pass^k {rep[f'pass^{j}']:.3f}")
flaky = sorted(s for s, runs in successes.items() if 0 < sum(runs) < k)
print("flaky scenarios (sometimes pass, sometimes fail):", flaky)
print("pass^k answers 'will it work EVERY time a customer tries?'. Fix the flaky scenarios first, then re-measure with CI.")
(HERE / "results" / "reliability.json").write_text(json.dumps({"report": rep, "flaky": flaky}, indent=2))

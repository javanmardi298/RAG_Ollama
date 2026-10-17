# Stage 6b: validate the LLM judge against YOUR labels before trusting it.
# Step 1 (no labels yet): exports bot replies from stage 6 to eval/judge_labels.csv with an empty human_pass column.
#         Label them in the panel ("LLM judge" page) or in a spreadsheet: 1 = acceptable reply, 0 = not.
# Step 2 (labels present): runs the judge on the labelled rows and measures agreement and Cohen's kappa.
import csv, json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.config import RESULTS_DIR, SEED
from support.evaluation import judge_agreement, judge_reply
from support.runtime import make_llm

LABELS = ROOT / "eval" / "judge_labels.csv"
FIELDS = ["id", "customer", "bot", "human_pass"]


def read_labels():
    if not LABELS.exists():
        return []
    with LABELS.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


rows = read_labels()
if not rows:
    if not (RESULTS_DIR / "stage6_runs.jsonl").exists():
        raise SystemExit("No stage 6 conversations yet: run stage 6 (evaluation with simulated customers) first.")
    runs = [json.loads(l) for l in (RESULTS_DIR / "stage6_runs.jsonl").read_text(encoding="utf-8").splitlines() if l]
    pairs = [(r["scenario_id"], t[i - 1]["content"], t[i]["content"])
             for r in runs for t in [r["transcript"]] for i in range(1, len(t)) if t[i]["role"] == "bot"]
    random.Random(SEED).shuffle(pairs)
    with LABELS.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS); w.writeheader()
        for n, (sid, cust, bot) in enumerate(pairs[:60]):
            w.writerow({"id": f"{sid}-{n}", "customer": cust, "bot": bot, "human_pass": ""})
    print(f"exported {min(60, len(pairs))} replies to {LABELS}. Label 30+ of them, then run this script again.")
    raise SystemExit(0)

labelled = [r for r in rows if r["human_pass"] in {"0", "1"}]
if len(labelled) < 20:
    raise SystemExit(f"only {len(labelled)} labelled rows; label at least 20 (better 50) for a meaningful kappa.")
judge = make_llm("judge")
verdicts = [judge_reply(judge, r["customer"], r["bot"]) for r in labelled]
human = [r["human_pass"] == "1" for r in labelled]
res = judge_agreement(human, [bool(v["pass"]) for v in verdicts])
disagree = [{"customer": r["customer"], "bot": r["bot"], "human": h, "judge": v["pass"], "critique": v["critique"]}
            for r, h, v in zip(labelled, human, verdicts) if h != bool(v["pass"])]
print(json.dumps(res, indent=2))
print("Rule of thumb: kappa >= 0.6 before using the judge; read every disagreement below.")
(RESULTS_DIR / "stage6_judge.json").write_text(json.dumps({**res, "disagreements": disagree}, indent=2,
                                                          ensure_ascii=False), encoding="utf-8")

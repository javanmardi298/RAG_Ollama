# Starter: a durable business workflow with LLM steps inside (here: incoming request -> classify -> extract ->
# decide -> human approval if risky -> act). Runs without a model (the "LLM" steps are rules); replace them
# one by one with real LLM calls and keep the tests green.
#   python run.py            processes eval/inbox.jsonl, shows the approval queue and the audit log
#   python run.py approve <run_id> <your name>
import os, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml
from labkit.workflow import Step, Workflow

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
LIMIT = float(cfg.get("approval_above_eur", 1000))
DONE_LOG = HERE / "results" / "actions.jsonl"


def classify(ctx):                      # replace with an LLM classifier (+ confidence) later
    text = ctx["text"].lower()
    return {"category": "refund" if "refund" in text or "money back" in text else "question"}


def extract(ctx):                       # replace with labkit.structured.extract later
    amount = re.search(r"(\d+(?:\.\d+)?)\s*(?:eur|€)", ctx["text"].lower())
    order = re.search(r"HH-\d{6}", ctx["text"])
    return {"amount": float(amount.group(1)) if amount else 0.0, "order_id": order.group() if order else None}


def validate(ctx):                      # business rules in code, never in the prompt
    if ctx["category"] == "refund" and not ctx["order_id"]:
        raise ValueError("refund request without order number")
    return {}


def act(ctx):                           # the side effect: runs at most once per idempotency key
    with DONE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"order_id": ctx["order_id"], "category": ctx["category"], "amount": ctx["amount"]}) + "\n")
    return {"acted": True}


wf = Workflow("requests", [
    Step("classify", classify, retries=2),
    Step("extract", extract, retries=2),
    Step("validate", validate),
    Step("approve", approval=lambda c: c["category"] == "refund" and c["amount"] > LIMIT),
    Step("act", act, idempotency_key=lambda c: f"{c['category']}:{c['order_id'] or c['message_id']}"),
], db=str(HERE / "results" / "workflow.db"))

if len(sys.argv) >= 4 and sys.argv[1] == "approve":
    print(wf.decide(sys.argv[2], True, by=sys.argv[3]))
    raise SystemExit(0)

for line in (HERE / "eval" / "inbox.jsonl").read_text(encoding="utf-8").splitlines():
    msg = json.loads(line)
    run = wf.start(msg)
    st = wf.state(run)
    print(f"{msg['message_id']}: {st['status']:<17} run={run}  {st['ctx'].get('category')} {st['ctx'].get('amount')}")
    if st["status"] == "failed":
        print("   audit:", [e["event"] + ":" + str(e["detail"]) for e in wf.audit(run) if e["event"] == "failed"])
print("\nWaiting for approval -> python run.py approve <run_id> <name>.  The duplicate message M3 must not act twice.")

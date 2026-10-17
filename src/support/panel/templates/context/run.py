# Starter: context engineering for a long agent session (labkit.context, labkit.ops.approx_tokens).
#   python run.py     builds a synthetic 30-step tool-using session, then shows what each cheap, deterministic cut saves:
#                     truncating huge tool outputs, clearing stale tool results, and budgeted packing with a stable
#                     (cacheable) prefix. Swap in your own agent's messages (results/*.json traces) next.
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
from labkit.context import Piece, clear_stale_tool_results, pack, truncate_tool_output
from labkit.ops import approx_tokens

budget = int(cfg.get("budget_tokens", 8000))
keep_last = int(cfg.get("keep_last_tool_results", 3))
max_tool = int(cfg.get("max_tool_chars", 2000)) // 4          # chars -> approx tokens

system = "You are a support agent. Rules: never refund above 500 EUR without approval; cite policy ids." * 3
tools = "TOOLS: get_order(id), search_policies(q), create_refund(order_id, amount, confirm)" * 4
messages = [{"role": "system", "content": system}, {"role": "user", "content": "Order 1042 arrived broken, I want a refund."}]
for i in range(30):
    messages.append({"role": "assistant", "content": f"step {i}: calling search_policies"})
    messages.append({"role": "tool", "content": f"result {i}: " + ("policy text and order rows ... " * (40 if i % 5 else 400))})

tok = lambda ms: sum(approx_tokens(m["content"]) for m in ms)  # noqa: E731
t0 = tok(messages)
m1 = [{**m, "content": truncate_tool_output(m["content"], max_tokens=max_tool)} if m["role"] == "tool" else m for m in messages]
m2 = clear_stale_tool_results(m1, keep_last=keep_last)
print(f"raw session            {t0:7d} tokens")
print(f"+ truncate tool output {tok(m1):7d}")
print(f"+ clear stale results  {tok(m2):7d}   (last {keep_last} kept verbatim)")

pieces = [Piece("system", system, 100, required=True), Piece("tools", tools, 90, required=True),
          Piece("task", messages[1]["content"], 95, required=True),
          *[Piece(f"turn{i}", m["content"], 10 + i, stable=True) for i, m in enumerate(m1[2:])],
          Piece("retrieved_policy", "Policy R-3: broken items are refunded in full within 14 days.", 80, stable=False),
          Piece("now", "2026-10-17 10:00", 5, stable=False)]
kept, report = pack(pieces, budget)
print(f"pack (truncated, not cleared) {report['tokens']:7d} / {budget}   dropped {len(report['dropped'])} oldest/low-priority pieces")
print("send order:", [p.name for p in kept][:6], "...", [p.name for p in kept][-3:])
print("Stable prefix first (system, tools, task, old turns) so prompt caching hits; volatile pieces last.")
(HERE / "results" / "context.json").write_text(json.dumps({"raw": t0, "truncated": tok(m1), "cleared": tok(m2), **report}, indent=2))

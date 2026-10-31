# Stage 3: non-interactive smoke test of the whole chain (guardrails -> intent -> decision -> route -> tools).
# Uses a COPY of shop.db, so nothing in the real database changes. For a real conversation use the panel chat.
import json, shutil, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.agent import Session
from support.config import DB_PATH, RESULTS_DIR
from support.runtime import make_agent
from support.tools import connect

tmp = Path(tempfile.mkdtemp()) / "shop.db"; shutil.copy(DB_PATH, tmp)
con = connect(tmp)
order = dict(con.execute("SELECT o.order_id, c.email FROM orders o JOIN customers c USING(customer_id) "
                         "WHERE o.status='processing' AND o.scenario IS NULL LIMIT 1").fetchone())
agent = make_agent(con)
turns = ["Hi, I want to cancel my order", f"{order['order_id']} {order['email']}", "yes",
         "How long do I have to return something?"]
s, log = Session("smoke"), []
for msg in turns:
    if s.closed:
        break
    reply = agent.reply(s, msg)
    log.append({"user": msg, "bot": reply, "intent": s.intent})
    print("you>", msg); print("bot>", reply, f"   [intent={s.intent}]")
actions = [dict(r) for r in con.execute("SELECT action, order_id FROM actions")]
print("actions written:", actions)
(RESULTS_DIR / "stage3_smoke.json").write_text(json.dumps({"order": order["order_id"], "turns": log,
                                                           "actions": actions, "closed": s.closed}, indent=2,
                                                          ensure_ascii=False), encoding="utf-8")

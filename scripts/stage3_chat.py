# Stage 3: talk to the agent in the terminal.   python scripts/stage3_chat.py
# (The control panel has the same chat in its "agent chat" page.)
# Needs: stage 0 (data/shop.db), stage 1 (results/intent_model.joblib), Ollama running.
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.agent import Session
from support.config import RESULTS_DIR
from support.monitoring import TraceWriter
from support.runtime import make_agent
from support.tools import connect

con = connect()
print("Try:", dict(con.execute("SELECT o.order_id, c.email FROM orders o JOIN customers c USING(customer_id) "
                               "WHERE o.status='processing' LIMIT 1").fetchone()))
agent = make_agent(con, trace=TraceWriter(RESULTS_DIR / "traces.jsonl"))
s = Session("terminal")
while not s.closed:
    msg = input("you> ").strip()
    if msg in {"quit", "exit"}:
        break
    print("bot>", agent.reply(s, msg))

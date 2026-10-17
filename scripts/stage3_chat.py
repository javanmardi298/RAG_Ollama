# Stage 3: talk to the agent in the terminal.   python scripts/stage3_chat.py
# Needs: stage 0 (data/shop.db), stage 1 (results/intent_model.joblib), Ollama running.
import sys, joblib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.agent import Session, SupportAgent
from support.config import RESULTS_DIR
from support.intents import apply_temperature
from support.llm import OllamaLLM
from support.monitoring import TraceWriter
from support.rag import Retriever, load_chunks, make_policy_answerer
from support.tools import ToolBox, connect

model = joblib.load(RESULTS_DIR / "intent_model.joblib")
T = float((RESULTS_DIR / "temperature.txt").read_text())

def classify(text):
    p = apply_temperature(model.predict_proba([text]), T)[0]
    return str(model.classes_[p.argmax()]), float(p.max())

llm = OllamaLLM("qwen2.5:7b")
con = connect()
print("Try:", dict(con.execute("SELECT o.order_id, c.email FROM orders o JOIN customers c USING(customer_id) "
                               "WHERE o.status='processing' LIMIT 1").fetchone()))
agent = SupportAgent(llm, ToolBox(con), classify, make_policy_answerer(llm, Retriever(load_chunks())),
                     trace=TraceWriter(RESULTS_DIR / "traces.jsonl"))
s = Session("terminal")
while not s.closed:
    msg = input("you> ").strip()
    if msg in {"quit", "exit"}:
        break
    print("bot>", agent.reply(s, msg))

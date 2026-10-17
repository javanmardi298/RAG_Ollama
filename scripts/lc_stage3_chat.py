# Stage 3 (LangGraph version): chat with the graph in the terminal; state survives restarts (SQLite checkpointer).
# python scripts/lc_stage3_chat.py [thread_id]
import sqlite3, sys, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import joblib
from langgraph.checkpoint.sqlite import SqliteSaver
from support.agent import Session
from support.config import DATA_DIR, RESULTS_DIR
from support.intents import apply_temperature
from support.lc.graph import Deps, GraphSupportAgent, build_graph
from support.lc.models import chat_model, embeddings
from support.lc.rag_lc import build_retrievers, make_answer_fn
from support.monitoring import TraceWriter

model = joblib.load(RESULTS_DIR / "intent_model.joblib"); T = float((RESULTS_DIR / "temperature.txt").read_text())
def classify(text):
    p = apply_temperature(model.predict_proba([text]), T)[0]
    return str(model.classes_[p.argmax()]), float(p.max())

llm = chat_model()
checkpointer = SqliteSaver(sqlite3.connect(DATA_DIR / "checkpoints.db", check_same_thread=False))
graph = build_graph(Deps(model=llm, classify=classify,
                         answer_policy=make_answer_fn(llm, build_retrievers(embeddings()))), checkpointer)
(RESULTS_DIR / "graph.mmd").write_text(graph.get_graph().draw_mermaid())   # paste into mermaid.live to see the graph

agent = GraphSupportAgent(graph, trace=TraceWriter(RESULTS_DIR / "traces_lc.jsonl"))
s = Session(sys.argv[1] if len(sys.argv) > 1 else uuid.uuid4().hex[:8])
print("thread:", s.session_id, "(run again with this id to continue the same conversation)")
while not s.closed:
    msg = input("you> ").strip()
    if msg in {"quit", "exit"}:
        break
    print("bot>", agent.reply(s, msg))

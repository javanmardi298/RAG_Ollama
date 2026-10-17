# Stage 6 (both versions): run the SAME scenarios through the plain agent, the LangGraph graph
# and the create_agent baseline, then compare with paired bootstrap.
# %%
import json, shutil, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import joblib, numpy as np
from langgraph.checkpoint.memory import InMemorySaver
from support.agent import Session, SupportAgent
from support.config import DB_PATH, RESULTS_DIR
from support.evaluation import UserSimulator, build_scenarios, paired_bootstrap, run_scenario, score, summarize
from support.intents import apply_temperature
from support.lc.baseline import BaselineAgent, make_baseline_agent
from support.lc.graph import Deps, GraphSupportAgent, build_graph
from support.lc.models import chat_model, embeddings
from support.lc.rag_lc import build_retrievers, make_answer_fn
from support.llm import OllamaLLM
from support.rag import Retriever, load_chunks, make_policy_answerer
from support.tools import ToolBox, connect

clf = joblib.load(RESULTS_DIR / "intent_model.joblib"); T = float((RESULTS_DIR / "temperature.txt").read_text())
def classify(text):
    p = apply_temperature(clf.predict_proba([text]), T)[0]
    return str(clf.classes_[p.argmax()]), float(p.max())

plain_llm, lc_llm = OllamaLLM("qwen2.5:7b"), chat_model()
plain_answer = make_policy_answerer(plain_llm, Retriever(load_chunks()))
lc_answer = make_answer_fn(lc_llm, build_retrievers(embeddings()))

def fresh_db():
    tmp = Path(tempfile.mkdtemp()) / "shop.db"; shutil.copy(DB_PATH, tmp); return tmp

def make_plain():
    db = fresh_db(); con = connect(db)
    return SupportAgent(plain_llm, ToolBox(con), classify, plain_answer), Session("eval"), con

def make_graph():
    db = fresh_db()
    g = build_graph(Deps(model=lc_llm, classify=classify, answer_policy=lc_answer, db_path=db), InMemorySaver())
    return GraphSupportAgent(g), Session("eval"), connect(db)

def make_baseline():
    db = fresh_db(); agent, _ = make_baseline_agent(lc_llm, db)
    return BaselineAgent(agent), Session("eval"), connect(db)

# %%
scenarios = build_scenarios(connect(), n_random=40)[:20]
sim = UserSimulator(OllamaLLM("qwen2.5:7b", temperature=0.7))
runs = {name: [run_scenario(make, sim, sc) for sc in scenarios]
        for name, make in [("plain", make_plain), ("langgraph", make_graph), ("create_agent", make_baseline)]}
for name, res in runs.items():
    print(name, summarize(res))
succ = {n: np.array([score(r)["success"] for r in res], float) for n, res in runs.items()}
print("langgraph vs plain:", paired_bootstrap(succ["plain"], succ["langgraph"]))
print("create_agent vs langgraph:", paired_bootstrap(succ["langgraph"], succ["create_agent"]))
(RESULTS_DIR / "lc_stage6_compare.json").write_text(json.dumps({n: summarize(r) for n, r in runs.items()}, indent=2))

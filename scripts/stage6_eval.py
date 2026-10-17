# Stage 6: end-to-end evaluation with simulated customers. Slow (LLM on both sides): start with 20 scenarios.
# %%
import json, shutil, sys, tempfile, joblib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.agent import Session, SupportAgent
from support.config import DB_PATH, RESULTS_DIR
from support.evaluation import build_scenarios, run_scenario, summarize, UserSimulator, save_results
from support.intents import apply_temperature
from support.llm import OllamaLLM
from support.rag import Retriever, load_chunks, make_policy_answerer
from support.tools import ToolBox, connect

model = joblib.load(RESULTS_DIR / "intent_model.joblib"); T = float((RESULTS_DIR / "temperature.txt").read_text())
def classify(text):
    p = apply_temperature(model.predict_proba([text]), T)[0]
    return str(model.classes_[p.argmax()]), float(p.max())

agent_llm = OllamaLLM("qwen2.5:7b")
user_llm = OllamaLLM("qwen2.5:7b", temperature=0.7)    # a different model here makes the test harder to game
answerer = make_policy_answerer(agent_llm, Retriever(load_chunks()))

def make_agent():
    tmp = Path(tempfile.mkdtemp()) / "shop.db"
    shutil.copy(DB_PATH, tmp)                            # every scenario starts from the same clean database
    con = connect(tmp)
    return SupportAgent(agent_llm, ToolBox(con), classify, answerer), Session("eval"), con

scenarios = build_scenarios(connect(), n_random=60)
print(len(scenarios), "scenarios")

# %%
sim = UserSimulator(user_llm)
results = [run_scenario(make_agent, sim, sc) for sc in scenarios[:20]]
save_results(results, RESULTS_DIR / "stage6_runs.jsonl")
print(json.dumps(summarize(results), indent=2))

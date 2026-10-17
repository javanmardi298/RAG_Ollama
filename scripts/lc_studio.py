"""Entry point for `langgraph dev` (LangGraph Studio): exposes the compiled graph as `graph`.

The LangGraph server brings its own checkpointer, so the graph is compiled without one here.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import joblib  # noqa: E402

from support.config import RESULTS_DIR  # noqa: E402
from support.intents import apply_temperature  # noqa: E402
from support.lc.graph import Deps, build_graph  # noqa: E402
from support.lc.models import chat_model, embeddings  # noqa: E402
from support.lc.rag_lc import build_retrievers, make_answer_fn  # noqa: E402

_model = joblib.load(RESULTS_DIR / "intent_model.joblib")
_T = float((RESULTS_DIR / "temperature.txt").read_text())


def classify(text):
    p = apply_temperature(_model.predict_proba([text]), _T)[0]
    return str(_model.classes_[p.argmax()]), float(p.max())


llm = chat_model()
graph = build_graph(Deps(model=llm, classify=classify,
                         answer_policy=make_answer_fn(llm, build_retrievers(embeddings()))))

"""Builders shared by the scripts, the API and the control panel.

Every place that needs "the agent as configured" builds it here, from configs/project.yaml and the
artefacts of earlier stages (results/intent_model.joblib, temperature.txt, thresholds.json). Before this
module, each script repeated these lines with its own hard-coded model name, which is exactly how a
tuned threshold or a changed model silently fails to reach the agent.
"""
from __future__ import annotations

import sys

from .config import RESULTS_DIR
from .settings import encoder_device, settings, tuned_thresholds


def make_llm(role: str = "agent"):
    """role: agent | user_sim | judge. All roles talk to the same Ollama server."""
    from .llm import OllamaLLM

    s = settings().llm
    model, temp = {"agent": (s.chat_model, s.temperature),
                   "user_sim": (s.user_sim_model, s.user_sim_temperature),
                   "judge": (s.judge_model, 0.0)}[role]
    return OllamaLLM(model, temperature=temp, host=s.host)


def make_encoder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings().embeddings.model, device=encoder_device())


def load_classifier():
    """The stage 1 winner with its temperature: text -> (intent, calibrated confidence)."""
    import joblib

    from .intents import apply_temperature

    model = joblib.load(RESULTS_DIR / "intent_model.joblib")
    t_path = RESULTS_DIR / "temperature.txt"
    T = float(t_path.read_text()) if t_path.exists() else 1.0

    def classify(text: str) -> tuple[str, float]:
        p = apply_temperature(model.predict_proba([text]), T)[0]
        return str(model.classes_[p.argmax()]), float(p.max())

    classify.model, classify.temperature = model, T
    return classify


def make_retriever(encoder=None):
    """Policy retriever with the configured BM25/RRF parameters. Dense/hybrid need an encoder."""
    from .rag import Retriever, load_chunks

    r = settings().rag
    if encoder is None and r.mode != "bm25":
        try:
            encoder = make_encoder()
        except ImportError:   # e.g. the slim Docker image of stage 8: say so loudly instead of failing at startup
            print(f"WARNING: rag.mode={r.mode} needs sentence-transformers, which is not installed; "
                  "retrieval falls back to BM25 only.", file=sys.stderr)
    return Retriever(load_chunks(), encoder=encoder, k1=r.bm25_k1, b=r.bm25_b, rrf_k=r.rrf_k)


def make_answerer(llm, retriever=None):
    from .rag import make_policy_answerer

    r = settings().rag
    return make_policy_answerer(llm, retriever or make_retriever(), k=r.k, mode=r.mode)


def make_agent(con, llm=None, classify=None, answerer=None, trace=None):
    """A SupportAgent wired exactly as configured. Pass shared pieces to avoid reloading them per session."""
    from .agent import SupportAgent
    from .tools import ToolBox

    llm = llm or make_llm("agent")
    return SupportAgent(llm, ToolBox(con), classify or load_classifier(), answerer or make_answerer(llm),
                        trace=trace, thresholds=tuned_thresholds(),
                        max_tool_steps=settings().agent.max_tool_steps)

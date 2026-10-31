"""Stage 8 (LangGraph version): the graph behind FastAPI.

Differences from app/main.py:
* conversation state lives in a SQLite checkpointer, not in a Python dict: it survives restarts,
  and the "sessions in memory" limitation of the plain version is gone (use Postgres for several hosts);
* /chat/stream streams progress events (which node is running) as Server-Sent Events.
Run: uvicorn app.main_lc:app --port 8001
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import joblib  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402

from support.agent import Session  # noqa: E402
from support.config import DATA_DIR, RESULTS_DIR  # noqa: E402
from support.intents import apply_temperature  # noqa: E402
from support.lc.graph import Deps, GraphSupportAgent, build_graph  # noqa: E402
from support.lc.models import chat_model, embeddings  # noqa: E402
from support.lc.rag_lc import build_retrievers, make_answer_fn  # noqa: E402
from support.monitoring import TraceWriter  # noqa: E402

clf = joblib.load(RESULTS_DIR / "intent_model.joblib")
T = float((RESULTS_DIR / "temperature.txt").read_text())


def classify(text):
    p = apply_temperature(clf.predict_proba([text]), T)[0]
    return str(clf.classes_[p.argmax()]), float(p.max())


llm = chat_model()
checkpointer = SqliteSaver(sqlite3.connect(DATA_DIR / "checkpoints.db", check_same_thread=False))
graph = build_graph(Deps(model=llm, classify=classify,
                         answer_policy=make_answer_fn(llm, build_retrievers(embeddings()))), checkpointer)
agent = GraphSupportAgent(graph, trace=TraceWriter(RESULTS_DIR / "traces_lc.jsonl"))
app = FastAPI(title="Marketplace Support Agent (LangGraph)")


class ChatIn(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)


@app.post("/chat")
def chat(body: ChatIn):
    start = time.perf_counter()
    s = Session(body.session_id or uuid.uuid4().hex)
    reply = agent.reply(s, body.message)
    return {"session_id": s.session_id, "reply": reply, "closed": s.closed,
            "latency_ms": round((time.perf_counter() - start) * 1000, 1)}


@app.post("/chat/stream")
def chat_stream(body: ChatIn):
    """Progress events, one per finished node: the client can show 'checking your order...'."""
    sid = body.session_id or uuid.uuid4().hex
    config = {"configurable": {"thread_id": sid}}

    def events():
        for update in graph.stream({"messages": [HumanMessage(body.message)]}, config, stream_mode="updates"):
            for node in update:
                yield f"data: {json.dumps({'session_id': sid, 'node': node})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}

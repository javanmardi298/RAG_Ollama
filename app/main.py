"""Stage 8: the agent behind an HTTP API.

Run:  uvicorn app.main:app --port 8000
Try:  curl -X POST localhost:8000/chat -H 'Content-Type: application/json' \
           -d '{"session_id": "s1", "message": "Where is my order HH-100042?"}'
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from support.agent import Session, SupportAgent  # noqa: E402  (SupportAgent: type of the sessions dict)
from support.config import DB_PATH, RESULTS_DIR  # noqa: E402
from support.llm import OllamaLLM  # noqa: E402
from support.monitoring import TraceWriter  # noqa: E402
from support.runtime import load_classifier as _load_classifier, make_agent, make_answerer  # noqa: E402
from support.settings import settings  # noqa: E402
from support.tools import connect  # noqa: E402

# Environment variables win (Docker); otherwise configs/project.yaml.
MODEL = os.getenv("SUPPORT_MODEL", settings().llm.chat_model)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", settings().llm.host)   # in Docker: http://host.docker.internal:11434
SESSION_TTL_S = settings().serving.session_ttl_min * 60

app = FastAPI(title="Marketplace Support Agent")
llm = OllamaLLM(MODEL, temperature=settings().llm.temperature, host=OLLAMA_HOST)
trace = TraceWriter(RESULTS_DIR / "traces.jsonl")
classifier = None                                # loaded at startup (see load_classifier)
answerer = None
sessions: dict[str, tuple[Session, SupportAgent, float]] = {}


class ChatIn(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)


class ChatOut(BaseModel):
    session_id: str
    reply: str
    closed: bool
    latency_ms: float


@app.on_event("startup")
def load_classifier():
    """The intent classifier trained in stage 1 (with its temperature) and the policy answerer, loaded once."""
    global classifier, answerer
    classifier = _load_classifier()
    answerer = make_answerer(llm)


def _get_session(session_id: str | None):
    now = time.time()
    for sid in [s for s, (_, _, t) in sessions.items() if now - t > SESSION_TTL_S]:
        sessions.pop(sid)                       # forget idle sessions
    if session_id and session_id in sessions:
        s, agent, _ = sessions[session_id]
    else:
        session_id = session_id or uuid.uuid4().hex
        # one DB connection per session: sqlite3 connections must not be shared across threads
        agent = make_agent(connect(DB_PATH), llm=llm, classify=classifier, answerer=answerer, trace=trace)
        s = Session(session_id)
    sessions[session_id] = (s, agent, now)
    return s, agent


@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    start = time.perf_counter()
    s, agent = _get_session(body.session_id)
    if s.closed:
        raise HTTPException(409, "This conversation was handed to a human. Start a new session.")
    reply = agent.reply(s, body.message)
    return ChatOut(session_id=s.session_id, reply=reply, closed=s.closed,
                   latency_ms=round((time.perf_counter() - start) * 1000, 1))


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL, "active_sessions": len(sessions)}

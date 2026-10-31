"""A tiny durable workflow engine: the deterministic backbone for agentic processes.

Most "agentic" business processes (invoice approval, claim handling, email triage) are workflows with a few
LLM steps inside. What they need from the engine:
* steps run in order; each step's output is stored, so a crash resumes where it stopped (no double payments)
* retries with backoff for flaky steps (LLM timeouts), and a clear failure after the last try
* idempotency: a side-effect step runs at most once per idempotency key, across restarts
* human approval: the workflow pauses at an approval step until a person decides
* an audit log of everything, for debugging and compliance

State lives in SQLite. For production scale the same ideas exist in Temporal, Prefect or LangGraph.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable

SCHEMA = """
CREATE TABLE IF NOT EXISTS wf_runs (run_id TEXT PRIMARY KEY, workflow TEXT, status TEXT, ctx TEXT, step INTEGER,
                                    created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS wf_audit (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, ts REAL, step TEXT,
                                     event TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS wf_effects (key TEXT PRIMARY KEY, run_id TEXT, step TEXT, result TEXT, ts REAL);
"""


class NeedsApproval(Exception):
    pass


@dataclass
class Step:
    name: str
    fn: Callable[[dict], dict] | None = None      # ctx -> updates to ctx
    retries: int = 0
    backoff_s: float = 0.5
    approval: Callable[[dict], bool] | None = None  # ctx -> True if a human must approve before going on
    idempotency_key: Callable[[dict], str] | None = None   # for steps with side effects


@dataclass
class Workflow:
    name: str
    steps: list[Step]
    db: str = ":memory:"
    sleep: Callable[[float], None] = time.sleep
    _con: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self):
        self._con = sqlite3.connect(self.db, check_same_thread=False)
        self._con.executescript(SCHEMA)

    # ----- public -----
    def start(self, ctx: dict) -> str:
        """Create a run and execute it as far as possible. Returns the run id (see state() for the status)."""
        run_id = uuid.uuid4().hex[:12]
        with self._con:
            self._con.execute("INSERT INTO wf_runs VALUES (?, ?, 'running', ?, 0, ?, ?)",
                              (run_id, self.name, json.dumps(ctx), time.time(), time.time()))
        self._audit(run_id, "-", "started", ctx)
        self.resume(run_id)
        return run_id

    def resume(self, run_id: str) -> str:
        """Run from the stored step until done, waiting for approval, or failed. Returns the status."""
        status, ctx, i = self._load(run_id)
        if status in ("done", "failed", "rejected", "waiting_approval"):
            return status
        while i < len(self.steps):
            step = self.steps[i]
            try:
                ctx = self._run_step(run_id, step, ctx)
            except NeedsApproval:
                self._save(run_id, "waiting_approval", ctx, i)
                self._audit(run_id, step.name, "waiting_approval", {})
                return "waiting_approval"
            except Exception as e:
                self._save(run_id, "failed", ctx, i)
                self._audit(run_id, step.name, "failed", {"error": f"{type(e).__name__}: {e}"})
                return "failed"
            i += 1
            self._save(run_id, "running", ctx, i)
        self._save(run_id, "done", ctx, i)
        self._audit(run_id, "-", "done", {})
        return "done"

    def decide(self, run_id: str, approved: bool, by: str, note: str = "") -> str:
        status, ctx, i = self._load(run_id)
        if status != "waiting_approval":
            raise ValueError(f"run {run_id} is {status}, not waiting for approval")
        self._audit(run_id, self.steps[i].name, "approved" if approved else "rejected", {"by": by, "note": note})
        if not approved:
            self._save(run_id, "rejected", ctx, i)
            return "rejected"
        ctx = {**ctx, f"_approved_{self.steps[i].name}": by}
        self._save(run_id, "running", ctx, i)
        return self.resume(run_id)

    def state(self, run_id: str) -> dict:
        status, ctx, i = self._load(run_id)
        return {"run_id": run_id, "status": status, "step": self.steps[i].name if i < len(self.steps) else None,
                "ctx": ctx}

    def audit(self, run_id: str) -> list[dict]:
        rows = self._con.execute("SELECT ts, step, event, detail FROM wf_audit WHERE run_id = ? ORDER BY id", (run_id,))
        return [{"ts": t, "step": s, "event": e, "detail": json.loads(d)} for t, s, e, d in rows]

    # ----- internals -----
    def _run_step(self, run_id: str, step: Step, ctx: dict) -> dict:
        if step.approval and step.approval(ctx) and f"_approved_{step.name}" not in ctx:
            raise NeedsApproval(step.name)
        if step.fn is None:
            return ctx
        key = step.idempotency_key(ctx) if step.idempotency_key else None
        if key:
            row = self._con.execute("SELECT result FROM wf_effects WHERE key = ?", (key,)).fetchone()
            if row:                                # already done (e.g. before a crash): reuse, do not repeat
                self._audit(run_id, step.name, "idempotent_skip", {"key": key})
                return {**ctx, **json.loads(row[0])}
        for attempt in range(step.retries + 1):
            try:
                out = step.fn(dict(ctx)) or {}
                break
            except Exception as e:
                self._audit(run_id, step.name, "error", {"attempt": attempt + 1, "error": f"{type(e).__name__}: {e}"})
                if attempt == step.retries:
                    raise
                self.sleep(step.backoff_s * 2 ** attempt)
        if key:
            with self._con:
                self._con.execute("INSERT INTO wf_effects VALUES (?, ?, ?, ?, ?)",
                                  (key, run_id, step.name, json.dumps(out, default=str), time.time()))
        self._audit(run_id, step.name, "ok", out)
        return {**ctx, **out}

    def _load(self, run_id):
        row = self._con.execute("SELECT status, ctx, step FROM wf_runs WHERE run_id = ?", (run_id,)).fetchone()
        if not row:
            raise KeyError(run_id)
        return row[0], json.loads(row[1]), row[2]

    def _save(self, run_id, status, ctx, i):
        with self._con:
            self._con.execute("UPDATE wf_runs SET status = ?, ctx = ?, step = ?, updated = ? WHERE run_id = ?",
                              (status, json.dumps(ctx, default=str), i, time.time(), run_id))

    def _audit(self, run_id, step, event, detail):
        with self._con:
            self._con.execute("INSERT INTO wf_audit (run_id, ts, step, event, detail) VALUES (?, ?, ?, ?, ?)",
                              (run_id, time.time(), step, event, json.dumps(detail, default=str, ensure_ascii=False)))

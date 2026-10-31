"""Run history in SQLite (results/panel.db): which task ran, with which settings and commit, and what came out.

Shared by the web panel, the MCP server (Claude Desktop) and the job wrapper. They are separate processes, so
all state lives here, not in memory. Every write is a short transaction; SQLite handles the concurrency.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from contextlib import closing
from pathlib import Path

from ..config import RESULTS_DIR, ROOT



def db_path() -> Path:
    """results/panel.db; SUPPORT_PANEL_DB overrides it (tests), and child processes inherit the override."""
    return Path(os.environ.get("SUPPORT_PANEL_DB", RESULTS_DIR / "panel.db"))


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    stage       INTEGER NOT NULL,
    task        TEXT NOT NULL,
    kind        TEXT NOT NULL,              -- batch | service
    cmd         TEXT NOT NULL,              -- JSON list
    status      TEXT NOT NULL,              -- queued | running | succeeded | failed | stopped | lost
    origin      TEXT NOT NULL,              -- panel | mcp | claude
    pid         INTEGER,
    exit_code   INTEGER,
    started_at  REAL NOT NULL,
    finished_at REAL,
    log_path    TEXT NOT NULL,
    settings    TEXT NOT NULL,              -- project.yaml snapshot (JSON)
    git_commit  TEXT,
    git_dirty   INTEGER,
    metrics     TEXT                        -- headline numbers of the stage after the run (JSON)
);
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       REAL NOT NULL,
    source   TEXT NOT NULL,                 -- panel | mcp | claude | job
    kind     TEXT NOT NULL,                 -- settings_changed | tool_call | run_started | ...
    detail   TEXT NOT NULL                  -- JSON
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")       # readers do not block the job wrapper's writes
    con.executescript(SCHEMA)
    return con


def _row(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in ("cmd", "settings", "metrics"):
        if d.get(k):
            d[k] = json.loads(d[k])
    return d


def git_state() -> tuple[str | None, bool | None]:
    """Commit and dirty flag, so every result can be traced to exact code. None when git is unavailable."""
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                                text=True, timeout=5).stdout.strip() or None
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                    capture_output=True, text=True, timeout=5).stdout.strip())
        return commit, dirty
    except (OSError, subprocess.SubprocessError):
        return None, None


def create_run(stage: int, task: str, kind: str, cmd: list[str], origin: str, log_path: Path,
               settings: dict) -> int:
    commit, dirty = git_state()
    with closing(connect()) as con, con:
        cur = con.execute(
            "INSERT INTO runs (stage, task, kind, cmd, status, origin, started_at, log_path, settings, git_commit, git_dirty)"
            " VALUES (?, ?, ?, ?, 'queued', ?, ?, ?, ?, ?, ?)",
            (stage, task, kind, json.dumps(cmd), origin, time.time(), str(log_path), json.dumps(settings),
             commit, None if dirty is None else int(dirty)))
        return int(cur.lastrowid)


def update_run(run_id: int, **fields) -> None:
    if "metrics" in fields and fields["metrics"] is not None:
        fields["metrics"] = json.dumps(fields["metrics"], default=str)
    cols = ", ".join(f"{k} = ?" for k in fields)
    with closing(connect()) as con, con:
        con.execute(f"UPDATE runs SET {cols} WHERE run_id = ?", (*fields.values(), run_id))


def mark_running(run_id: int, pid: int) -> bool:
    """queued -> running, unless the run was stopped in the meantime (returns False then)."""
    with closing(connect()) as con, con:
        cur = con.execute("UPDATE runs SET status = 'running', pid = ? WHERE run_id = ? AND status = 'queued'",
                          (pid, run_id))
        return cur.rowcount == 1


def get_run(run_id: int) -> dict | None:
    with closing(connect()) as con:
        return _row(con.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone())


def list_runs(stage: int | None = None, task: str | None = None, limit: int = 50) -> list[dict]:
    sql, args = "SELECT * FROM runs WHERE 1=1", []
    if stage is not None:
        sql += " AND stage = ?"; args.append(stage)
    if task:
        sql += " AND task = ?"; args.append(task)
    sql += " ORDER BY run_id DESC LIMIT ?"; args.append(limit)
    with closing(connect()) as con:
        return [_row(r) for r in con.execute(sql, args)]


def active_runs() -> list[dict]:
    with closing(connect()) as con:
        return [_row(r) for r in con.execute("SELECT * FROM runs WHERE status IN ('queued', 'running') ORDER BY run_id")]


def log_event(source: str, kind: str, detail: dict) -> None:
    with closing(connect()) as con, con:
        con.execute("INSERT INTO events (ts, source, kind, detail) VALUES (?, ?, ?, ?)",
                    (time.time(), source, kind, json.dumps(detail, default=str, ensure_ascii=False)))


def last_event(source: str | None = None, kind: str | None = None) -> dict | None:
    sql, args = "SELECT * FROM events WHERE 1=1", []
    if source:
        sql += " AND source = ?"; args.append(source)
    if kind:
        sql += " AND kind = ?"; args.append(kind)
    with closing(connect()) as con:
        r = con.execute(sql + " ORDER BY event_id DESC LIMIT 1", args).fetchone()
    if r is None:
        return None
    d = dict(r); d["detail"] = json.loads(d["detail"])
    return d


def events(limit: int = 50, kind: str | None = None) -> list[dict]:
    sql, args = "SELECT * FROM events", []
    if kind:
        sql += " WHERE kind = ?"; args.append(kind)
    with closing(connect()) as con:
        rows = con.execute(sql + " ORDER BY event_id DESC LIMIT ?", (*args, limit)).fetchall()
    return [{**dict(r), "detail": json.loads(r["detail"])} for r in rows]


def count_runs(task: str, status: str = "succeeded") -> int:
    with closing(connect()) as con:
        return con.execute("SELECT COUNT(*) FROM runs WHERE task = ? AND status = ?", (task, status)).fetchone()[0]

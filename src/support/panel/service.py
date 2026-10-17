"""The operations behind every interface: the web panel, the MCP server (Claude Desktop) and the direct Claude chat.

One function per operation, typed and documented, returning JSON-friendly dicts. The MCP server registers these
functions as tools; the Claude chat builds its tool schemas from the same signatures. So the three interfaces
can never drift apart, and Claude can only do what the panel itself can do.
"""
from __future__ import annotations

import inspect
import shutil
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any, get_type_hints

import yaml
from pydantic import ValidationError

from ..config import CONFIG_DIR, PROCESSED_DIR, RESULTS_DIR, ROOT
from ..settings import apply_changes, load, schema
from . import advisor, registry, runner
from .catalog import STAGES, TASKS, as_dict
from .results import stage_results

# ---------- reading the project ----------


def project_status() -> dict:
    """Overview of the whole project: each stage's status and headline numbers, blocking problems,
    running jobs, the top reminders, and the main settings. Start here before anything else."""
    from .preflight import run_all
    runner.reconcile()
    checks = run_all()
    s = load()
    tips = advisor.advice(checks)
    return {
        "stages": [{"id": st.id, "title": st.title, "status": advisor.stage_status(st.id),
                    "headline": stage_results(st.id)["metrics"][:4]} for st in STAGES],
        "problems": [{"id": c["id"], "label": c["label"], "detail": c["detail"], "fix": c["fix"], "level": c["level"]}
                     for c in checks if not c["ok"] and c["level"] in ("error", "warn")],
        "active_runs": [_run_brief(r) for r in registry.active_runs()],
        "advice": tips[:8], "advice_total": len(tips),
        "models": {"agent": s.llm.chat_model, "user_sim": s.llm.user_sim_model, "embeddings": s.embeddings.model,
                   "intent_winner": s.intents.winner, "rag_mode": s.rag.mode},
    }


def get_stage(stage: int) -> dict:
    """Everything about one stage (0-9): learning goal, concepts, steps, runnable tasks, its parameters with
    current values, latest results, recent runs and the reminders for this stage."""
    st = STAGES[stage]
    s = load().model_dump(mode="json")
    return {**as_dict(st), "settings_values": {sec: s[sec] for sec in st.settings},
            "results": stage_results(stage),
            "runs": [_run_brief(r) for r in registry.list_runs(stage=stage, limit=10)],
            "advice": [a for a in advisor.advice() if a["stage"] == stage]}


def get_settings(section: str = "") -> dict:
    """Current values of configs/project.yaml with each field's description and allowed range.
    section: one of project, llm, embeddings, data, intents, rag, decision, agent, evaluation, robustness,
    serving, monitoring, experiments, lora, claude. Empty = all sections (values only)."""
    values = load().model_dump(mode="json")
    if not section:
        return values
    if section not in values:
        raise ValueError(f"unknown section '{section}'. Sections: {', '.join(values)}")
    sch = schema()
    ref = sch["properties"][section]["$ref"].split("/")[-1]
    props = sch["$defs"][ref]["properties"]
    return {k: {"value": v, **{kk: props[k][kk] for kk in ("description", "minimum", "maximum", "exclusiveMinimum",
                                                             "exclusiveMaximum", "enum", "type") if kk in props[k]}}
            for k, v in values[section].items()}


def update_settings(changes: dict[str, Any], origin: str = "panel") -> dict:
    """Change experiment parameters, e.g. {"rag.k": 5, "llm.chat_model": "llama3.1:8b"}.
    All changes are validated together; if any is invalid nothing is saved and the errors are returned.
    Store policy numbers (14/30 days, 150 EUR) are NOT settings and cannot be changed here."""
    if origin == "claude" and not load().claude.allow_settings_changes:
        return {"ok": False, "error": "claude.allow_settings_changes is off in the panel settings."}
    if any(k.startswith("claude.allow_") for k in changes) and origin in ("claude", "mcp"):
        return {"ok": False, "error": "Claude's own permissions can only be changed by the user in the panel."}
    try:
        _, diff = apply_changes(changes)
    except (KeyError, ValueError, ValidationError) as e:
        errors = e.errors() if isinstance(e, ValidationError) else [{"msg": str(e)}]
        return {"ok": False, "errors": [{"loc": ".".join(map(str, err.get("loc", []))), "msg": err["msg"]}
                                        for err in errors]}
    if diff:
        registry.log_event(origin, "settings_changed", {k: {"old": o, "new": n} for k, (o, n) in diff.items()})
    affected = sorted({st.id for st in STAGES for k in diff if k.split(".")[0] in st.settings})
    return {"ok": True, "changed": {k: {"old": o, "new": n} for k, (o, n) in diff.items()},
            "stages_to_rerun": affected}


def get_results(stage: int) -> dict:
    """Latest results of a stage (0-9): headline metrics and details (curves, missed questions, ...)."""
    return stage_results(stage)


def get_advice(stage: int = -1) -> list[dict]:
    """Reminders and suggestions computed by code from the project state. stage=-1 for all."""
    tips = advisor.advice()
    return tips if stage < 0 else [t for t in tips if t["stage"] in (stage, None)]


def job_ad_coverage() -> list[dict]:
    """For each requirement of the job ad: which stages give evidence and the numbers so far (for the CV)."""
    return advisor.coverage()


def policy_rules() -> dict:
    """Store policy (read-only): policy_rules.yaml numbers and the intent routing table (intents.yaml)."""
    return {"policy_rules": yaml.safe_load((CONFIG_DIR / "policy_rules.yaml").read_text(encoding="utf-8")),
            "intents": yaml.safe_load((CONFIG_DIR / "intents.yaml").read_text(encoding="utf-8"))["intents"],
            "note": "Edit configs/policy_rules.yaml AND both prose files in policies/en and policies/de, then run all tests."}


_FORBIDDEN = {".env", ".git", ".venv", "venv", "__pycache__"}


def read_project_file(path: str, max_chars: int = 20000) -> dict:
    """Read a text file of the project (code, configs, docs, logs, results). Relative to the project root.
    Secrets (.env), the git folder and the virtual environment are not readable."""
    p = (ROOT / path).resolve()
    if ROOT.resolve() not in p.parents and p != ROOT.resolve():
        raise ValueError("path must be inside the project")
    if any(part in _FORBIDDEN for part in p.relative_to(ROOT.resolve()).parts):
        raise ValueError("this path is not readable from here")
    if p.is_dir():
        return {"path": path, "entries": sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir()
                                                if x.name not in _FORBIDDEN)}
    if not p.exists():
        raise FileNotFoundError(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "size": len(text), "truncated": len(text) > max_chars, "text": text[:max_chars]}


# ---------- runs ----------


def list_tasks() -> list[dict]:
    """All runnable tasks (the only commands that can be started), with their stage and prerequisites."""
    from .preflight import run_all
    ok = {c["id"]: c["ok"] for c in run_all()}
    return [{"task": t.id, "stage": st.id, "label": t.label, "kind": t.kind, "langchain": t.lc, "minutes": t.minutes,
             "missing": [n for n in t.needs if not ok.get(n, True)], "note": t.note} for st, t in TASKS.values()]


def run_task(task: str, origin: str = "panel") -> dict:
    """Start a task by id (see list_tasks), e.g. "stage2_rag" or "tests_all". Returns the run id; the run
    continues in the background. Check progress with run_status."""
    if origin == "claude" and not load().claude.allow_runs:
        return {"ok": False, "error": "claude.allow_runs is off in the panel settings."}
    try:
        return {"ok": True, **runner.start(task, origin=origin)}
    except runner.RunError as e:
        return {"ok": False, "error": str(e)}


def run_status(run_id: int, tail_lines: int = 60) -> dict:
    """Status of a run and the last lines of its log. When it finished, also its headline metrics."""
    runner.reconcile()
    run = registry.get_run(run_id)
    if not run:
        raise ValueError(f"run #{run_id} does not exist")
    return {**_run_brief(run), "metrics": run.get("metrics"), "log_tail": runner.tail(run_id, tail_lines)}


def stop_run(run_id: int, origin: str = "panel") -> dict:
    """Stop a running task or service."""
    return runner.stop(run_id, origin=origin)


def list_runs(stage: int = -1, limit: int = 15) -> list[dict]:
    """Recent runs (newest first), optionally for one stage."""
    runner.reconcile()
    return [_run_brief(r) for r in registry.list_runs(stage=None if stage < 0 else stage, limit=limit)]


def compare_runs(run_a: int, run_b: int) -> dict:
    """What differs between two runs: changed parameters and the change in headline metrics."""
    a, b = registry.get_run(run_a), registry.get_run(run_b)
    if not a or not b:
        raise ValueError("both runs must exist")
    sa, sb = a["settings"], b["settings"]
    params = {f"{sec}.{k}": {"a": sa.get(sec, {}).get(k), "b": v} for sec in sb for k, v in sb[sec].items()
              if sa.get(sec, {}).get(k) != v}
    ma, mb = a.get("metrics") or {}, b.get("metrics") or {}
    metrics = {}
    for k in sorted((set(ma) | set(mb)) - {"_fmt"}):
        va, vb = ma.get(k), mb.get(k)
        delta = round(vb - va, 4) if isinstance(va, (int, float)) and isinstance(vb, (int, float)) \
            and not isinstance(va, bool) else None
        metrics[k] = {"a": va, "b": vb, "delta": delta}
    return {"a": _run_brief(a), "b": _run_brief(b), "params_changed": params, "metrics": metrics,
            "same_code": a["git_commit"] == b["git_commit"] and not a["git_dirty"] and not b["git_dirty"]}


def _run_brief(r: dict) -> dict:
    dur = (r["finished_at"] or time.time()) - r["started_at"] if r.get("started_at") else None
    return {"run_id": r["run_id"], "stage": r["stage"], "task": r["task"], "kind": r["kind"], "status": r["status"],
            "origin": r["origin"], "started_at": r["started_at"], "duration_s": round(dur, 1) if dur else None,
            "exit_code": r["exit_code"], "git_commit": r["git_commit"], "git_dirty": bool(r["git_dirty"]),
            "metrics": r.get("metrics")}


# ---------- talking to the support agent itself ----------


class AgentChats:
    """Panel/Claude conversations with the support agent. Each session works on its own COPY of shop.db,
    so trying "cancel my order" never changes the real database. Traces go to results/traces.jsonl."""

    def __init__(self):
        self._lock = threading.Lock()
        self._shared = None
        self.sessions: dict[str, tuple[Any, Any, Any]] = {}

    def _pieces(self):
        if self._shared is None:
            from ..monitoring import TraceWriter
            from ..runtime import load_classifier, make_answerer, make_llm
            llm = make_llm("agent")
            self._shared = (llm, load_classifier(), make_answerer(llm), TraceWriter(RESULTS_DIR / "traces.jsonl"))
        return self._shared

    def reply(self, session_id: str, message: str) -> dict:
        from ..agent import Session
        from ..config import DB_PATH
        from ..runtime import make_agent
        from ..tools import connect
        with self._lock:
            if message == "/new" or session_id not in self.sessions:
                if session_id in self.sessions:
                    self.sessions.pop(session_id)[2].close()
                llm, classify, answerer, trace = self._pieces()
                tmp = Path(tempfile.mkdtemp(prefix="agentchat_")) / "shop.db"
                shutil.copy(DB_PATH, tmp)
                con = connect(tmp, check_same_thread=False)
                agent = make_agent(con, llm=llm, classify=classify, answerer=answerer, trace=trace)
                self.sessions[session_id] = (agent, Session(session_id), con)
                if message == "/new":
                    return {"session_id": session_id, "reply": "(گفتگوی تازه شروع شد)", "closed": False}
            agent, s, con = self.sessions[session_id]
            if s.closed:
                return {"session_id": session_id, "reply": "این گفتگو به انسان ارجاع شده است. «گفتگوی تازه» را بزن.",
                        "closed": True, "intent": s.intent}
            text = agent.reply(s, message)
            actions = [dict(r) for r in con.execute("SELECT action, order_id FROM actions")]
            tickets = con.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            return {"session_id": session_id, "reply": text, "closed": s.closed, "intent": s.intent,
                    "pending_confirmation": s.pending, "language": s.language, "actions_in_sandbox": actions,
                    "tickets_in_sandbox": tickets, "facts": s.facts[-3:]}

    def reset(self, session_id: str) -> None:
        with self._lock:
            entry = self.sessions.pop(session_id, None)
            if entry:
                entry[2].close()

    def sample_orders(self, n: int = 6) -> list[dict]:
        """Orders to try in the chat (one per status plus boundary cases), with the email that verifies them."""
        from ..tools import connect
        con = connect()
        rows = [dict(r) for r in con.execute(
            "SELECT o.order_id, c.email, o.status, o.total_eur, o.scenario FROM orders o JOIN customers c USING(customer_id) "
            "WHERE o.order_id IN (SELECT MIN(order_id) FROM orders WHERE scenario IS NULL GROUP BY status) "
            "OR o.scenario IN ('refund_just_above_auto_limit', 'return_one_day_too_late', 'custom_made_recent') "
            "ORDER BY o.scenario IS NOT NULL, o.status")]
        con.close()
        return rows[:n + 3]


CHATS = AgentChats()


def chat_with_agent(message: str, session_id: str = "claude") -> dict:
    """Send one customer message to the support agent (as configured now) and get its reply, the detected intent,
    any pending confirmation, and what it changed in its sandbox copy of shop.db. Use "/new" to restart.
    Needs stage 0 and 1 done and Ollama running."""
    return CHATS.reply(session_id, message)


def sample_orders() -> list[dict]:
    """A few real orders from shop.db (with the email that verifies them) to try in the agent chat."""
    return CHATS.sample_orders()


# ---------- files for Colab and labelling ----------


def make_colab_bundle() -> dict:
    """Write results/colab_lora_bundle.zip: the LoRA script, the train/dev splits and lora_config.json."""
    import json
    s = load()
    out = RESULTS_DIR / "colab_lora_bundle.zip"
    missing = [n for n in ("train", "dev") if not (PROCESSED_DIR / f"intents_{n}.csv").exists()]
    if missing:
        return {"ok": False, "error": "run stage 0 first (splits missing)"}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ROOT / "scripts" / "stage9_lora_colab.py", "stage9_lora_colab.py")
        for n in ("train", "dev"):
            z.write(PROCESSED_DIR / f"intents_{n}.csv", f"intents_{n}.csv")
        z.writestr("lora_config.json", json.dumps({**s.lora.model_dump(), "seed": s.project.seed}, indent=2))
    return {"ok": True, "path": str(out), "size": out.stat().st_size}


# ---------- project presets (learning tracks) and settings presets ----------


def list_presets(level: int = 0, track: str = "") -> dict:
    """The real-world project presets (basic -> advanced) with level, tracks, progress and how many of their building
    blocks are ready in the system, added in labkit, or external tools. level: 1 basic, 2 intermediate, 3 advanced,
    0 = all. track: rag, agent, workflow, eval, ml, production or empty."""
    from . import presets
    prog = presets.progress()
    items = [presets.summary(p, prog) for p in presets.projects().values()
             if (not level or p.level == level) and (not track or track in p.tracks)]
    return {"projects": items, "levels": presets.LEVELS, "tracks": presets.TRACKS}


def get_preset(preset_id: str) -> dict:
    """Everything about one project preset: real-world use, problem, goal, data sources with licences, stack,
    building blocks (with status and where they live), stages (learn / build / measure / pitfall), metrics,
    parameters, guardrails, production notes, interview questions, advanced steps, CV line, progress."""
    from . import presets
    return presets.detail(preset_id)


def set_preset_progress(preset_id: str, stage: int, done: bool = True, origin: str = "panel") -> dict:
    """Mark a stage (0-based) of a project preset as done or not done (the learner's progress)."""
    from . import presets
    out = presets.set_progress(preset_id, stage, done)
    registry.log_event(origin, "preset_progress", {"preset": preset_id, "stage": stage, "done": done})
    return out


def scaffold_preset(preset_id: str, origin: str = "panel") -> dict:
    """Create projects/<preset_id>/ with the full plan (README), config.yaml with the preset's parameters, sample data
    and a runnable starter (run.py) built on labkit. Refuses to overwrite an existing folder."""
    from . import presets
    out = presets.scaffold(preset_id)
    if out.get("ok"):
        registry.log_event(origin, "preset_scaffolded", {"preset": preset_id, "path": out["path"]})
    return out


def list_settings_presets() -> list[dict]:
    """Ready-made parameter sets for this project (quick smoke test, laptop without GPU, full evaluation, German focus,
    strict safety, production-like, Claude read-only) with the exact changes each one makes."""
    from . import presets
    current = load().model_dump(mode="json")
    out = []
    for sp in presets.settings_presets().values():
        diff = {k: {"current": current[k.split(".")[0]][k.split(".")[1]], "preset": v} for k, v in sp.changes.items()}
        out.append({**sp.model_dump(), "diff": {k: v for k, v in diff.items() if v["current"] != v["preset"]}})
    return out


def apply_settings_preset(preset_id: str, origin: str = "panel") -> dict:
    """Apply a settings preset to configs/project.yaml (validated; nothing is saved if any value is invalid)."""
    from . import presets
    sp = presets.settings_presets()[preset_id]
    out = update_settings(dict(sp.changes), origin=origin)
    if out.get("ok"):
        registry.log_event(origin, "settings_preset_applied", {"preset": preset_id})
    return {**out, "preset": preset_id}


# ---------- tool registry for MCP and the Claude chat ----------

READ_TOOLS = [project_status, get_stage, get_settings, get_results, get_advice, job_ad_coverage, policy_rules,
              read_project_file, list_tasks, run_status, list_runs, compare_runs, sample_orders,
              list_presets, get_preset, list_settings_presets]
ACTION_TOOLS = [update_settings, run_task, stop_run, chat_with_agent, make_colab_bundle,
                set_preset_progress, scaffold_preset, apply_settings_preset]
ALL_TOOLS = READ_TOOLS + ACTION_TOOLS


def _json_type(tp) -> dict:
    origin = getattr(tp, "__origin__", None)
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is str:
        return {"type": "string"}
    if tp is dict or origin is dict:
        return {"type": "object"}
    if tp is list or origin is list:
        return {"type": "array"}
    return {}


def tool_schema(fn) -> dict:
    """Anthropic tool definition from a function's signature and docstring ('origin' is filled in by the caller)."""
    hints = get_type_hints(fn)
    props, required = {}, []
    for name, p in inspect.signature(fn).parameters.items():
        if name == "origin":
            continue
        props[name] = _json_type(hints.get(name))
        if p.default is inspect.Parameter.empty:
            required.append(name)
        else:
            props[name]["default"] = p.default
    return {"name": fn.__name__, "description": inspect.getdoc(fn) or fn.__name__,
            "input_schema": {"type": "object", "properties": props, "required": required}}


def call_tool(name: str, args: dict, origin: str) -> Any:
    fn = {f.__name__: f for f in ALL_TOOLS}[name]
    if "origin" in inspect.signature(fn).parameters:
        args = {**args, "origin": origin}
    return fn(**args)


def new_id() -> str:
    return uuid.uuid4().hex[:8]

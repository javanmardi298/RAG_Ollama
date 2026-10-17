"""The control panel's HTTP API and static page. Listens on 127.0.0.1 only: it can start processes and edit files."""
from __future__ import annotations

import csv
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..config import ROOT
from ..settings import load, schema
from . import advisor, claude_chat, claude_desktop, envfile, registry, runner, service
from .catalog import JOB_AD, STAGES, as_dict
from .preflight import run_all
from .results import files_status, result_file

STATIC = Path(__file__).parent / "static"
JUDGE_LABELS = ROOT / "eval" / "judge_labels.csv"

app = FastAPI(title="Support Agent control panel")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

LOCAL_HOSTS = {"127.0.0.1", "localhost", "testserver"}


@app.middleware("http")
async def local_only(request: Request, call_next):
    """Other websites open in the same browser must not drive the panel.
    Host check: blocks DNS rebinding. Custom header on writes: a cross-site page cannot send it without CORS."""
    host = (request.headers.get("host") or "").split(":")[0]
    if host not in LOCAL_HOSTS:
        return JSONResponse({"ok": False, "error": "panel accepts local requests only"}, status_code=403)
    if request.method not in ("GET", "HEAD") and request.headers.get("x-panel") != "1":
        return JSONResponse({"ok": False, "error": "missing X-Panel header"}, status_code=403)
    return await call_next(request)


@app.exception_handler(runner.RunError)
def _run_error(_, e):
    return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.exception_handler(claude_chat.ClaudeUnavailable)
def _claude_error(_, e):
    return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.exception_handler(ValueError)
def _value_error(_, e):
    return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


# ---------- overview ----------

@app.get("/api/overview")
def overview():
    data = service.project_status()
    s = load()
    data["connections"] = {"ollama_host": s.llm.host, "claude": claude_chat.status(), "desktop": claude_desktop.status()}
    data["commit"] = registry.git_state()
    return data


@app.get("/api/preflight")
def preflight():
    return run_all()


@app.get("/api/catalog")
def catalog():
    return {"stages": [{"id": st.id, "title": st.title, "title_en": st.title_en, "status": advisor.stage_status(st.id)}
                       for st in STAGES], "job_ad": JOB_AD}


@app.get("/api/stage/{stage_id}")
def stage(stage_id: int):
    if not 0 <= stage_id < len(STAGES):
        raise HTTPException(404)
    return service.get_stage(stage_id)


@app.get("/api/advice")
def advice():
    return advisor.advice()


@app.get("/api/coverage")
def coverage():
    return advisor.coverage()


# ---------- settings and policy ----------

@app.get("/api/settings")
def settings_get():
    return {"values": load().model_dump(mode="json"), "schema": schema()}


@app.post("/api/settings")
def settings_post(changes: dict = Body(..., embed=True)):
    return service.update_settings(changes, origin="panel")


@app.get("/api/policy")
def policy():
    return service.policy_rules()


@app.get("/api/events")
def events(kind: str | None = None):
    return registry.events(limit=60, kind=kind)


# ---------- runs ----------

@app.get("/api/tasks")
def tasks():
    return service.list_tasks()


@app.get("/api/runs")
def runs(stage: int = -1, limit: int = 30):
    return service.list_runs(stage, limit)


@app.post("/api/runs")
def run_start(task: str = Body(..., embed=True)):
    out = service.run_task(task, origin="panel")
    if not out.get("ok"):
        return JSONResponse(out, status_code=400)
    return out


@app.get("/api/runs/{run_id}")
def run_get(run_id: int, tail: int = 200):
    return service.run_status(run_id, tail)


@app.post("/api/runs/{run_id}/stop")
def run_stop(run_id: int):
    return service.stop_run(run_id, origin="panel")


@app.get("/api/compare")
def compare(a: int, b: int):
    return service.compare_runs(a, b)


# ---------- results and files ----------

@app.get("/api/results/{stage_id}")
def results(stage_id: int):
    return service.get_results(stage_id)


@app.get("/api/files")
def files():
    return files_status()


@app.get("/results/{name}")
def result_download(name: str):
    path = result_file(name)
    if not path:
        raise HTTPException(404)
    return FileResponse(path)


@app.get("/api/file")
def project_file(path: str):
    return service.read_project_file(path, max_chars=200_000)


@app.post("/api/colab_bundle")
def colab_bundle():
    return service.make_colab_bundle()


# ---------- agent chat ----------

@app.post("/api/agent_chat")
def agent_chat(message: str = Body(...), session_id: str = Body("panel")):
    try:
        return service.chat_with_agent(message, session_id)
    except FileNotFoundError as e:
        return _chat_error(f"فایل لازم پیدا نشد ({e.filename}). مرحله‌های ۰ و ۱ را اجرا کن.")
    except ModuleNotFoundError as e:
        return _chat_error(f"پکیج {e.name} نصب نیست: pip install {e.name}")
    except Exception as e:     # usually Ollama not running or model not pulled
        text = f"{type(e).__name__}: {e}"
        if "connect" in text.lower() or "refused" in text.lower():
            text = f"Ollama در {load().llm.host} جواب نمی‌دهد؛ Ollama را اجرا کن. ({text})"
        elif "not found" in text.lower() and "model" in text.lower():
            text = f"مدل در Ollama نیست: ollama pull {load().llm.chat_model} ({text})"
        return _chat_error(text)


def _chat_error(text: str) -> JSONResponse:
    return JSONResponse({"ok": False, "error": text}, status_code=400)


@app.get("/api/sample_orders")
def sample_orders():
    try:
        return service.sample_orders()
    except Exception:
        return []


# ---------- Claude ----------

@app.get("/api/claude/status")
def claude_status():
    return {**claude_chat.status(), "desktop": claude_desktop.status()}


@app.post("/api/claude/chat")
def claude_send(message: str = Body(...), chat_id: str = Body("panel"), context: str = Body("")):
    return claude_chat.CHAT.send(chat_id, message, context)


@app.post("/api/claude/reset")
def claude_reset(chat_id: str = Body("panel", embed=True)):
    claude_chat.CHAT.reset(chat_id)
    return {"ok": True}


@app.post("/api/claude/key")
def claude_key(value: str = Body(..., embed=True)):
    value = value.strip()
    if value and not value.startswith("sk-ant-"):
        raise ValueError("کلید Anthropic با sk-ant- شروع می‌شود.")
    envfile.set_value("ANTHROPIC_API_KEY", value)
    return {"ok": True, "key": envfile.mask(value)}


@app.post("/api/claude_desktop/install")
def desktop_install():
    return claude_desktop.install()


@app.post("/api/claude_desktop/uninstall")
def desktop_uninstall():
    return claude_desktop.uninstall()


# ---------- LLM judge labels (stage 6b) ----------

@app.get("/api/judge/labels")
def judge_labels():
    if not JUDGE_LABELS.exists():
        return {"exists": False, "rows": []}
    with JUDGE_LABELS.open(encoding="utf-8", newline="") as f:
        return {"exists": True, "rows": list(csv.DictReader(f))}


@app.post("/api/judge/labels")
def judge_label(id: str = Body(...), human_pass: str = Body(...)):
    if human_pass not in {"0", "1", ""}:
        raise ValueError("human_pass must be 1, 0 or empty")
    with JUDGE_LABELS.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r["id"] == id:
            r["human_pass"] = human_pass
    with JUDGE_LABELS.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["id", "customer", "bot", "human_pass"])
        w.writeheader(); w.writerows(rows)
    return {"ok": True, "labelled": sum(r["human_pass"] in {"0", "1"} for r in rows), "total": len(rows)}


def stage_dict(stage_id: int) -> dict:
    return as_dict(STAGES[stage_id])

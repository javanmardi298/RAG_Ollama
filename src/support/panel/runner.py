"""Start, watch and stop the allow-listed tasks of the catalog.

Each run is executed by a small detached wrapper process (`python -m support.panel.job <run_id>`) that writes
the log and the final status into the registry itself. So a run keeps going and reports correctly even when
the process that started it (the web panel, or the MCP server inside Claude Desktop) is closed.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from ..config import RESULTS_DIR, ROOT
from ..settings import load
from . import registry
from .catalog import TASKS

LOG_DIR = Path(os.environ.get("SUPPORT_PANEL_LOGS", RESULTS_DIR / "logs"))
IS_WINDOWS = os.name == "nt"


class RunError(Exception):
    """A run could not be started; the message says why and what to do (shown to the user and to Claude)."""


def child_env() -> dict[str, str]:
    """UTF-8 everywhere (Windows consoles default to cp1252), unbuffered output, plots without a window."""
    env = dict(os.environ)
    src = str(ROOT / "src")
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", MPLBACKEND="Agg",
               SUPPORT_ROOT=str(ROOT), PYTHONPATH=src + os.pathsep + env.get("PYTHONPATH", ""))
    return env


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        import psutil
        return psutil.pid_exists(pid) and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    except ImportError:
        pass
    except Exception:
        return False
    if IS_WINDOWS:
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259                                           # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill_tree(pid: int) -> None:
    """Stop the wrapper AND the script it started (and anything that script started)."""
    try:
        import psutil
        proc = psutil.Process(pid)
        for child in proc.children(recursive=True):
            child.kill()
        proc.kill()
        return
    except ImportError:
        pass
    except Exception:
        return
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except OSError:
            pass


def reconcile() -> None:
    """Runs whose wrapper died without reporting (PC restarted, process killed) are marked 'lost'."""
    for run in registry.active_runs():
        too_old_to_be_queued = time.time() - run["started_at"] > 60
        if (run["pid"] and not pid_alive(run["pid"])) or (not run["pid"] and too_old_to_be_queued):
            registry.update_run(run["run_id"], status="lost", finished_at=time.time())


def resolve_cmd(cmd: list[str], settings) -> list[str]:
    """Fill placeholders like {serving.port} from project.yaml."""
    data = settings.model_dump()
    out = []
    for part in cmd:
        if part.startswith("{") and part.endswith("}"):
            section, _, field = part[1:-1].partition(".")
            part = str(data[section][field])
        out.append(part)
    return out


def start(task_id: str, origin: str = "panel", check_needs: bool = True) -> dict:
    if task_id not in TASKS:
        raise RunError(f"unknown task '{task_id}'. Known tasks: {', '.join(TASKS)}")
    stage, task = TASKS[task_id]
    reconcile()
    if check_needs and task.needs:
        from .preflight import failing
        missing = failing(task.needs)
        if missing:
            raise RunError("prerequisites missing: " + "; ".join(f"{c['label']}: {c['fix']}" for c in missing))
    active = registry.active_runs()
    if task.kind == "batch" and any(r["kind"] == "batch" for r in active):
        busy = next(r for r in active if r["kind"] == "batch")
        raise RunError(f"run #{busy['run_id']} ({busy['task']}) is still running. One batch run at a time "
                       "(they share Ollama, CPU and the results folder). Wait or stop it.")
    if task.kind == "service" and any(r["task"] == task_id for r in active):
        raise RunError(f"{task.label} is already running.")

    settings = load()
    cmd = resolve_cmd(task.cmd, settings)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_id = registry.create_run(stage.id, task_id, task.kind, cmd, origin, LOG_DIR / "pending.log",
                                 settings.model_dump(mode="json"))
    log_path = LOG_DIR / f"run_{run_id:04d}_{task_id}.log"
    registry.update_run(run_id, log_path=str(log_path))

    kwargs: dict = {"cwd": ROOT, "env": child_env(), "stdin": subprocess.DEVNULL,
                    "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if IS_WINDOWS:   # no console window, survives the parent, own group for clean stopping
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000   # CREATE_NO_WINDOW
    else:
        kwargs["start_new_session"] = True
    wrapper = subprocess.Popen([sys.executable, "-m", "support.panel.job", str(run_id)], **kwargs)
    registry.update_run(run_id, pid=wrapper.pid)
    registry.log_event(origin, "run_started", {"run_id": run_id, "task": task_id})
    return {"run_id": run_id, "task": task_id, "label": task.label, "kind": task.kind, "log": str(log_path)}


def stop(run_id: int, origin: str = "panel") -> dict:
    run = registry.get_run(run_id)
    if not run:
        raise RunError(f"run #{run_id} does not exist")
    if run["status"] not in ("queued", "running"):
        return {"run_id": run_id, "status": run["status"], "note": "already finished"}
    registry.update_run(run_id, status="stopped", finished_at=time.time())
    if run["pid"]:
        kill_tree(run["pid"])
    registry.log_event(origin, "run_stopped", {"run_id": run_id})
    return {"run_id": run_id, "status": "stopped"}


def tail(run_id: int, lines: int = 80) -> str:
    run = registry.get_run(run_id)
    if not run:
        raise RunError(f"run #{run_id} does not exist")
    path = Path(run["log_path"])
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(text[-lines:])

"""Start JupyterLab on 127.0.0.1 and open a lesson notebook (used by `python -m learn lab` and by the panel's notebook button)."""
from __future__ import annotations

import importlib.util
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request

from support.config import ROOT

from . import api, notebooks

_STATE: dict = {}                                   # {"proc", "port", "token"} of the server this process started


def _free_port(start: int = 8895) -> int:
    for port in range(start, start + 50):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("no free port for JupyterLab")


def _ready(port: int, token: str, timeout: float = 40.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status?token={token}", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def start(lesson: str) -> dict:
    """(Re)build the lesson notebook, make sure JupyterLab runs, return the URL that opens it (the token is random per start)."""
    if importlib.util.find_spec("jupyterlab") is None:
        raise ValueError("JupyterLab is not installed: pip install -r requirements-notebook.txt")
    rel = notebooks.write(lesson).replace("\\", "/")
    proc = _STATE.get("proc")
    if proc is None or proc.poll() is not None:
        port, token = _free_port(), secrets.token_urlsafe(24)
        env = {**os.environ, "JUPYTER_TOKEN": token, "PYTHONPATH": os.pathsep.join([str(ROOT / "src"), os.environ.get("PYTHONPATH", "")]),
               "PYTHONUTF8": "1"}
        root_flag = ["--allow-root"] if hasattr(os, "geteuid") and os.geteuid() == 0 else []     # containers / cloud sessions
        log = api.WORK / "jupyter.log"
        log.parent.mkdir(exist_ok=True)
        proc = subprocess.Popen([sys.executable, "-m", "jupyterlab", "--no-browser", "--ServerApp.ip=127.0.0.1", f"--port={port}",
                                 f"--ServerApp.root_dir={ROOT}", "--ServerApp.open_browser=False", *root_flag], cwd=str(ROOT), env=env,
                                stdout=log.open("w"), stderr=subprocess.STDOUT)
        _STATE.update(proc=proc, port=port, token=token)
        if not _ready(port, token):
            proc.terminate()
            _STATE.clear()
            tail = " | ".join(log.read_text(errors="replace").strip().splitlines()[-3:])
            raise RuntimeError(f"JupyterLab did not start within 40 s ({tail})")
    return {"url": f"http://127.0.0.1:{_STATE['port']}/lab/tree/{rel}?token={_STATE['token']}", "notebook": rel, "port": _STATE["port"]}


def stop() -> None:
    proc = _STATE.pop("proc", None)
    if proc and proc.poll() is None:
        proc.terminate()

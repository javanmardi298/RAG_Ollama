"""Wrapper that executes one registered run:  python -m support.panel.job <run_id>

Writes the script's output to the run's log file and the final status (and the stage's headline metrics)
into the registry. Started detached by runner.start(); never run it by hand.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from ..config import ROOT
from . import registry
from .runner import child_env


def main(run_id: int) -> int:
    run = registry.get_run(run_id)
    log_path = Path(run["log_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", buffering=1) as log:
        log.write(f"# run #{run_id}  task={run['task']}  commit={run['git_commit']}"
                  f"{' (uncommitted changes)' if run['git_dirty'] else ''}\n# {' '.join(run['cmd'])}\n\n")
        start = time.time()
        try:
            proc = subprocess.Popen(run["cmd"], cwd=ROOT, env=child_env(), stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT)
        except OSError as e:
            log.write(f"\n# could not start: {e}\n")
            registry.update_run(run_id, status="failed", exit_code=-1, finished_at=time.time())
            return 1
        if not registry.mark_running(run_id, os.getpid()):   # stopped before it really started
            proc.kill()
        code = proc.wait()
        log.write(f"\n# finished with exit code {code} after {time.time() - start:.1f} s\n")

    current = registry.get_run(run_id)["status"]
    if current == "stopped":                     # stop() already recorded it; keep that
        registry.update_run(run_id, exit_code=code)
        return code
    status = "succeeded" if code == 0 else "failed"
    metrics = None
    if status == "succeeded" and run["kind"] == "batch" and not run["task"].startswith("tests"):
        try:
            from .results import headline
            metrics = headline(run["stage"])
        except Exception as e:                   # metrics are a convenience; never fail the run for them
            metrics = {"error": str(e)}
    registry.update_run(run_id, status=status, exit_code=code, finished_at=time.time(), metrics=metrics)
    return code


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1])))

"""Used inside notebooks: run a step's check against the names defined in the notebook."""
from __future__ import annotations

import types

from . import _runner, api


def check_cell(lesson: str, step: str, namespace: dict) -> None:
    sd = api._step_dir(lesson, step)
    mod = types.ModuleType("notebook_answer")
    mod.__dict__.update({k: v for k, v in namespace.items() if not k.startswith("_")})
    out = _runner.run(sd / "check.py", mod)
    if out["skipped"]:
        print("SKIPPED:", out["skipped"])
        return
    for r in out["results"]:
        print(("✓ " if r["ok"] else "✗ ") + r["name"] + ("" if r["ok"] else "\n    " + r["message"]))
    print("\nPASSED" if all(r["ok"] for r in out["results"]) else "\nNot yet: fix the ✗ lines and run the code cell again.")

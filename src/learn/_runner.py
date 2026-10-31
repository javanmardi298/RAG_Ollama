"""Run one check.py against one answer file. Prints a single JSON line; never raises to the caller.

check.py defines functions check_*(m) that receive the student's module and raise AssertionError(message) on failure.
Optional: REQUIRES = ["torch"] -> skipped (not failed) when a package is missing.
Usage: python -m learn._runner <check.py> <answer.py>
"""
from __future__ import annotations

import importlib.util
import json
import sys
import traceback
from pathlib import Path


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run(check_path: Path, module) -> dict:
    """module: a loaded module (or anything with the student's names). Returns {"results": [...], "skipped": str|None}."""
    chk = _load(check_path, "learn_check")
    missing = [r for r in getattr(chk, "REQUIRES", []) if importlib.util.find_spec(r) is None]
    if missing:
        return {"results": [], "skipped": "needs " + ", ".join(missing) + " (pip install -r requirements-jepa.txt)"}
    results = []
    for name in sorted(n for n in dir(chk) if n.startswith("check_")):
        label = getattr(getattr(chk, name), "__doc__", None) or name[6:].replace("_", " ")
        try:
            getattr(chk, name)(module)
            results.append({"name": label.strip(), "ok": True})
        except AssertionError as e:
            results.append({"name": label.strip(), "ok": False, "message": str(e) or "assertion failed"})
        except NotImplementedError as e:
            results.append({"name": label.strip(), "ok": False, "message": f"not implemented yet: {e}", "todo": True})
        except Exception as e:                              # a crash in the student's code: show the last frames only
            tb = traceback.format_exc().strip().splitlines()
            results.append({"name": label.strip(), "ok": False, "message": f"{type(e).__name__}: {e}", "trace": tb[-6:]})
    return {"results": results, "skipped": None}


def main() -> None:
    check, answer = Path(sys.argv[1]), Path(sys.argv[2])
    try:
        sys.path.insert(0, str(answer.parent))
        out = run(check, _load(answer, "learn_answer"))
    except SyntaxError as e:
        out = {"results": [{"name": "the file can be imported", "ok": False, "message": f"SyntaxError: {e.msg} (line {e.lineno})"}],
               "skipped": None}
    except Exception as e:
        tb = traceback.format_exc().strip().splitlines()
        out = {"results": [{"name": "the file can be imported", "ok": False, "message": f"{type(e).__name__}: {e}", "trace": tb[-6:]}],
               "skipped": None}
    print("LEARN_RESULT " + json.dumps(out))


if __name__ == "__main__":
    main()

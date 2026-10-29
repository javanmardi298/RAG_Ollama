from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

from support.config import ROOT

LESSONS = ROOT / "lessons"
WORK = ROOT / "work"
STEP_RE = re.compile(r"step(\d\d)_")
HINT_RE = re.compile(r"^##\s*(?:Hint|راهنمایی)\s*(\d)", re.M)


def lessons() -> list[str]:
    return sorted(p.name for p in LESSONS.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


def steps(lesson: str) -> list[str]:
    d = LESSONS / lesson
    if not d.is_dir():
        raise FileNotFoundError(f"unknown lesson {lesson!r}; see `python -m learn list`")
    return sorted(p.name for p in d.iterdir() if p.is_dir() and STEP_RE.match(p.name))


def _step_dir(lesson: str, step: str | int) -> Path:
    names = steps(lesson)
    if isinstance(step, int) or str(step).isdigit():
        i = int(step)
        match = [n for n in names if int(STEP_RE.match(n).group(1)) == i]
    else:
        match = [n for n in names if n == step or n.startswith(str(step))]
    if len(match) != 1:
        raise FileNotFoundError(f"unknown step {step!r} in {lesson}; steps: {', '.join(names) or 'none yet'}")
    return LESSONS / lesson / match[0]


def title(path: Path) -> str:
    m = re.search(r"^#\s+(.*)", path.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip() if m else path.parent.name


# ---------- progress ----------

def _progress_file() -> Path:
    return WORK / "progress.json"


def progress() -> dict:
    f = _progress_file()
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _update(lesson: str, step: str, **kw) -> dict:
    p = progress()
    rec = p.setdefault(lesson, {}).setdefault(step, {"passed": False, "attempts": 0, "hints": 0, "solution_viewed": False})
    for k, v in kw.items():
        rec[k] = v(rec[k]) if callable(v) else v
    WORK.mkdir(exist_ok=True)
    _progress_file().write_text(json.dumps(p, indent=1), encoding="utf-8")
    return rec


def overview() -> list[dict]:
    p = progress()
    out = []
    for lid in lessons():
        try:
            st = steps(lid)
        except FileNotFoundError:
            st = []
        done = sum(bool(p.get(lid, {}).get(s, {}).get("passed")) for s in st)
        out.append({"lesson": lid, "steps": len(st), "done": done, "status": "interactive" if st else "guide only"})
    return out


def next_step(lesson: str) -> str | None:
    p = progress().get(lesson, {})
    return next((s for s in steps(lesson) if not p.get(s, {}).get("passed")), None)


# ---------- showing and working ----------

def answer_file(lesson: str, step: str | int) -> Path:
    sd = _step_dir(lesson, step)
    f = WORK / lesson / sd.name / "answer.py"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sd / "starter.py", f)
    return f


def show(lesson: str, step: str | int) -> dict:
    """Lesson text and where to write the answer. Never includes the solution."""
    sd = _step_dir(lesson, step)
    return {"lesson": lesson, "step": sd.name, "title": title(sd / "lesson.md"), "text": (sd / "lesson.md").read_text(encoding="utf-8"),
            "answer_file": str(answer_file(lesson, step).relative_to(ROOT)),
            "progress": progress().get(lesson, {}).get(sd.name, {})}


def check(lesson: str, step: str | int, target: Path | None = None, timeout: int = 120, record: bool = True) -> dict:
    sd = _step_dir(lesson, step)
    target = target or answer_file(lesson, step)
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(ROOT / "src"), os.environ.get("PYTHONPATH", "")]),
           "PYTHONUTF8": "1", "SUPPORT_ROOT": str(ROOT)}
    try:
        proc = subprocess.run([sys.executable, "-m", "learn._runner", str(sd / "check.py"), str(target)], capture_output=True, text=True,
                              timeout=timeout, cwd=str(ROOT), env=env, encoding="utf-8")
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("LEARN_RESULT ")), None)
        out = json.loads(line[13:]) if line else {"results": [{"name": "the check ran", "ok": False,
                                                              "message": (proc.stderr or proc.stdout)[-600:]}], "skipped": None}
    except subprocess.TimeoutExpired:
        out = {"results": [{"name": "finished in time", "ok": False, "message": f"timeout after {timeout}s (infinite loop?)"}], "skipped": None}
    res = out["results"]
    out["passed"] = bool(res) and all(r["ok"] for r in res)
    out["lesson"], out["step"] = lesson, sd.name
    if record and not out["skipped"]:
        _update(lesson, sd.name, attempts=lambda n: n + 1, **({"passed": True, "passed_at": time.strftime("%Y-%m-%d %H:%M")} if out["passed"] else {}))
        for r in res:
            if not r["ok"] and not r.get("todo") and r["message"].split(":")[0].endswith(("Error", "Exception")):
                _diary(lesson, sd.name, r)
    return out


def _diary(lesson: str, step: str, r: dict) -> None:
    WORK.mkdir(exist_ok=True)
    with (WORK / "errors.md").open("a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%Y-%m-%d %H:%M')} `{lesson}/{step}` **{r['message']}**  \n  (what fixed it: write it here)\n")


def hint(lesson: str, step: str | int, level: int | None = None) -> dict:
    """Hints come in three levels (nudge, direction, almost the answer). Without `level` you get the next unseen one."""
    sd = _step_dir(lesson, step)
    text = (sd / "hints.md").read_text(encoding="utf-8")
    parts = re.split(HINT_RE, text)
    found = {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    rec = progress().get(lesson, {}).get(sd.name, {})
    level = level or min(rec.get("hints", 0) + 1, max(found))
    _update(lesson, sd.name, hints=lambda n: max(n, level))
    return {"step": sd.name, "level": level, "of": max(found), "hint": found[level]}


def solution(lesson: str, step: str | int, force: bool = False) -> dict:
    sd = _step_dir(lesson, step)
    rec = progress().get(lesson, {}).get(sd.name, {})
    if not force and rec.get("attempts", 0) < 1:
        return {"ok": False, "error": "Run `learn check` at least once first: you learn more from a wrong attempt than from reading the answer. "
                                      "(--force to override)"}
    _update(lesson, sd.name, solution_viewed=True)
    return {"ok": True, "step": sd.name, "code": (sd / "solution.py").read_text(encoding="utf-8")}


# ---------- quiz ----------

def quiz(lesson: str, step: str | int) -> list[dict]:
    f = _step_dir(lesson, step) / "quiz.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else []


def record_quiz(lesson: str, step: str | int, wrong: list[int]) -> None:
    sd = _step_dir(lesson, step)
    _update(lesson, sd.name, quiz_wrong=wrong, quiz_done=True)


def review() -> list[dict]:
    """Quiz questions answered wrongly earlier: repeat them (spaced review)."""
    out = []
    for lid, sts in progress().items():
        for s, rec in sts.items():
            if rec.get("quiz_wrong"):
                qs = quiz(lid, s)
                out += [{"lesson": lid, "step": s, "i": i, **qs[i]} for i in rec["quiz_wrong"] if i < len(qs)]
    return out


# ---------- maintenance (CI) ----------

def selftest(only: str | None = None) -> list[str]:
    """Every solution must pass its check, every starter must NOT pass it, every relative link in the lessons must resolve."""
    problems = []
    for lid in ([only] if only else lessons()):
        for s in steps(lid):
            sd = LESSONS / lid / s
            for need in ("lesson.md", "starter.py", "solution.py", "check.py", "hints.md", "quiz.yaml"):
                if not (sd / need).exists():
                    problems.append(f"{lid}/{s}: missing {need}")
            if problems and problems[-1].startswith(f"{lid}/{s}: missing"):
                continue
            sol = check(lid, s, sd / "solution.py", record=False)
            if sol["skipped"]:
                continue
            if not sol["passed"]:
                bad = [r["name"] + ": " + r["message"] for r in sol["results"] if not r["ok"]]
                problems.append(f"{lid}/{s}: solution fails: {bad}")
            if check(lid, s, sd / "starter.py", record=False)["passed"]:
                problems.append(f"{lid}/{s}: the starter already passes (nothing to learn)")
            if len(re.findall(HINT_RE, (sd / "hints.md").read_text(encoding="utf-8"))) < 3:
                problems.append(f"{lid}/{s}: hints.md needs three levels")
    for md in LESSONS.rglob("*.md"):
        for target in re.findall(r"\]\((?!https?:|#|mailto:)([^)\s#]+)", md.read_text(encoding="utf-8")):
            if not (md.parent / target).resolve().exists():
                problems.append(f"{md.relative_to(ROOT)}: broken link {target}")
    return problems

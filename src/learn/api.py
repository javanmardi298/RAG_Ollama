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


# ---------- model provider chosen in the panel (work/provider.json) ----------

PROVIDERS = ("offline", "ollama", "anthropic", "opencode", "openai_compatible")
_DEFAULT_PROVIDER = {"provider": "offline", "model": "", "api_base": "", "budget_usd": 0.0, "price_in": 0.0, "price_out": 0.0}


def provider_config() -> dict:
    f = WORK / "provider.json"
    return {**_DEFAULT_PROVIDER, **(json.loads(f.read_text(encoding="utf-8")) if f.exists() else {})}


def set_provider(cfg: dict) -> dict:
    """Validate and store the model used when the learner runs an answer file (never stores keys: those live in .env)."""
    c = {**_DEFAULT_PROVIDER, **{k: cfg[k] for k in _DEFAULT_PROVIDER if k in cfg}}
    if c["provider"] not in PROVIDERS:
        raise ValueError(f"unknown provider {c['provider']!r}")
    if c["provider"] == "opencode" and "/" not in str(c["model"]):
        raise ValueError("opencode needs a model like provider/model (see `opencode models`)")
    if c["provider"] == "openai_compatible" and not str(c["api_base"]).startswith("http"):
        raise ValueError("openai_compatible needs an api_base starting with http")
    for k in ("budget_usd", "price_in", "price_out"):
        c[k] = float(c[k] or 0)
        if c[k] < 0:
            raise ValueError(f"{k} must not be negative")
    WORK.mkdir(exist_ok=True)
    (WORK / "provider.json").write_text(json.dumps(c, indent=1), encoding="utf-8")
    return c


def provider_env() -> dict:
    """LEARN_* variables for the processes that run learner code; the Anthropic key comes from .env / the environment."""
    from support.panel import envfile
    c = provider_config()
    env = {"LEARN_PROVIDER": c["provider"], "LEARN_MODEL": str(c["model"]), "LEARN_API_BASE": str(c["api_base"]),
           "LEARN_BUDGET_USD": str(c["budget_usd"]), "LEARN_PRICE_IN": str(c["price_in"]), "LEARN_PRICE_OUT": str(c["price_out"])}
    for k in ("ANTHROPIC_API_KEY", "OLLAMA_HOST"):
        if envfile.get(k):
            env[k] = envfile.get(k)
    return env


def _run_env() -> dict:
    return {**os.environ, **provider_env(), "PYTHONPATH": os.pathsep.join([str(ROOT / "src"), os.environ.get("PYTHONPATH", "")]),
            "PYTHONUTF8": "1", "SUPPORT_ROOT": str(ROOT)}


def test_provider(timeout: int = 90) -> dict:
    """One tiny chat call with the chosen provider (in a separate process). Returns the reply, latency or the error."""
    code = ("import time, json\nfrom learn import llm\nt = time.perf_counter()\n"
            "r = llm.get().chat([{'role': 'user', 'content': 'Reply with the single word OK.'}])\n"
            "print('LEARN_RESULT ' + json.dumps({'ok': True, 'reply': r.content[:200], 'seconds': round(time.perf_counter() - t, 2)}))")
    try:
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=timeout, cwd=str(ROOT),
                              env=_run_env(), encoding="utf-8")
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"no answer within {timeout}s"}
    line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("LEARN_RESULT ")), None)
    if line:
        return json.loads(line[13:])
    return {"ok": False, "error": (proc.stderr.strip().splitlines() or ["failed"])[-1][:400]}


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


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:                                     # WORK moved outside the repository (tests)
        return str(path)


def show(lesson: str, step: str | int) -> dict:
    """Lesson text and where to write the answer. Never includes the solution."""
    sd = _step_dir(lesson, step)
    return {"lesson": lesson, "step": sd.name, "title": title(sd / "lesson.md"), "text": (sd / "lesson.md").read_text(encoding="utf-8"),
            "answer_file": _rel(answer_file(lesson, step)),
            "progress": progress().get(lesson, {}).get(sd.name, {})}


def check(lesson: str, step: str | int, target: Path | None = None, timeout: int = 120, record: bool = True) -> dict:
    sd = _step_dir(lesson, step)
    target = target or answer_file(lesson, step)
    env = _run_env()
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


# ---------- helpers for the panel UI ----------

MAX_CODE = 200_000


def tree() -> list[dict]:
    """Sidebar data: every lesson with its steps (title, passed) and whether it has interactive steps."""
    p = progress()
    out = []
    for lid in lessons():
        sts = steps(lid) if (LESSONS / lid).is_dir() else []
        out.append({"lesson": lid, "interactive": bool(sts), "readme": f"lessons/{lid}/README.md",
                    "steps": [{"step": s, "title": title(LESSONS / lid / s / "lesson.md"), "passed": bool(p.get(lid, {}).get(s, {}).get("passed"))}
                              for s in sts]})
    return out


def detail(lesson: str, step: str | int) -> dict:
    """Everything the lesson page needs for one step (the quiz is sent without its answers)."""
    d = show(lesson, step)
    sd = _step_dir(lesson, step)
    hints = len(re.findall(HINT_RE, (sd / "hints.md").read_text(encoding="utf-8")))
    code = answer_file(lesson, step).read_text(encoding="utf-8")
    starter = (sd / "starter.py").read_text(encoding="utf-8")
    names = steps(lesson)
    i = names.index(sd.name)
    return {**d, "code": code, "is_starter": code == starter, "hints_total": hints,
            "quiz": [{"q": q["q"], "options": q["options"]} for q in quiz(lesson, step)],
            "prev": names[i - 1] if i else None, "next": names[i + 1] if i + 1 < len(names) else None,
            "runnable": "__main__" in starter}


def save_answer(lesson: str, step: str | int, code: str) -> dict:
    if len(code) > MAX_CODE:
        raise ValueError("answer file too large")
    answer_file(lesson, step).write_text(code, encoding="utf-8")
    return {"ok": True}


def reset_answer(lesson: str, step: str | int) -> dict:
    sd = _step_dir(lesson, step)
    answer_file(lesson, step).write_text((sd / "starter.py").read_text(encoding="utf-8"), encoding="utf-8")
    return {"ok": True}


def run_answer(lesson: str, step: str | int, timeout: int = 180) -> dict:
    """Run the learner's answer file as a script with the chosen model (its `if __name__ == "__main__"` part)."""
    f = answer_file(lesson, step)
    try:
        proc = subprocess.run([sys.executable, str(f)], capture_output=True, text=True, timeout=timeout, cwd=str(ROOT), env=_run_env(),
                              encoding="utf-8")
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": f"timeout after {timeout}s"}
    return {"ok": proc.returncode == 0, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-4000:], "provider": provider_config()["provider"]}


def grade_quiz(lesson: str, step: str | int, answers: list[int]) -> dict:
    qs = quiz(lesson, step)
    if len(answers) != len(qs):
        raise ValueError(f"expected {len(qs)} answers")
    wrong = [i for i, (a, q) in enumerate(zip(answers, qs)) if a != q["answer"]]
    record_quiz(lesson, step, wrong)
    return {"score": len(qs) - len(wrong), "total": len(qs), "wrong": wrong,
            "results": [{"ok": a == q["answer"], "why": q["why"], "answer": q["answer"]} for a, q in zip(answers, qs)]}


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

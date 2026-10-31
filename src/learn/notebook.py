"""Used inside notebooks: check a step against the names defined in the notebook, run the quiz, print the lesson report."""
from __future__ import annotations

import os
import time
import types

from . import _runner, api

RESULTS: dict[tuple[str, str], dict] = {}            # (lesson, step) -> {"passed", "ok", "n", "quiz"}; lives as long as the kernel


def _persist(lesson: str, step: str, passed: bool) -> None:
    try:                                              # the panel / `python -m learn list` show the same progress
        api._update(lesson, step, attempts=lambda n: n + 1, **({"passed": True, "passed_at": time.strftime("%Y-%m-%d %H:%M")} if passed else {}))
    except Exception:                                 # read-only folder (some cloud notebooks): progress stays in this kernel
        pass


def check_cell(lesson: str, step: str, namespace: dict) -> bool:
    sd = api._step_dir(lesson, step)
    mod = types.ModuleType("notebook_answer")
    mod.__dict__.update({k: v for k, v in namespace.items() if not k.startswith("_")})
    out = _runner.run(sd / "check.py", mod)
    if out["skipped"]:
        print("SKIPPED:", out["skipped"])
        RESULTS[(lesson, sd.name)] = {"skipped": out["skipped"], "passed": None, "ok": 0, "n": 0, "quiz": None}
        return False
    for r in out["results"]:
        print(("✓ " if r["ok"] else "✗ ") + r["name"] + ("" if r["ok"] else "\n    " + r["message"]))
    ok = sum(r["ok"] for r in out["results"])
    passed = bool(out["results"]) and ok == len(out["results"])
    RESULTS[(lesson, sd.name)] = {**RESULTS.get((lesson, sd.name), {"quiz": None}), "passed": passed, "ok": ok, "n": len(out["results"])}
    _persist(lesson, sd.name, passed)
    print(f"\n{ok}/{len(out['results'])} — " + ("PASSED 🎉" if passed else "هنوز نه: خط‌های ✗ را بخوان، سلول «کد تو» را اصلاح و اجرا کن، بعد دوباره همین سلول."))
    return passed


def quiz_cell(lesson: str, step: str) -> None:
    qs = api.quiz(lesson, step)
    auto = os.environ.get("LEARN_QUIZ_AUTO") == "1"          # CI: answer correctly without a keyboard
    wrong = []
    for i, q in enumerate(qs):
        print(f"\n{i + 1}. {q['q']}")
        for k, o in enumerate(q["options"]):
            print(f"   {k + 1}) {o}")
        try:
            got = str(q["answer"] + 1) if auto else input("شماره‌ی گزینه: ").strip()
        except Exception:
            print("   (برای پاسخ‌دادن، این سلول را در Jupyter/Colab اجرا کن)")
            return
        ok = got == str(q["answer"] + 1)
        print(("   ✓ " if ok else "   ✗ ") + q["why"])
        if not ok:
            wrong.append(i)
    sd = api._step_dir(lesson, step)
    RESULTS.setdefault((lesson, sd.name), {"passed": None, "ok": 0, "n": 0})["quiz"] = f"{len(qs) - len(wrong)}/{len(qs)}"
    try:
        api.record_quiz(lesson, step, wrong)
    except Exception:
        pass
    print(f"\nامتیاز: {len(qs) - len(wrong)}/{len(qs)}")


def lesson_report(lesson: str) -> dict:
    rows, done = [], 0
    for s in api.steps(lesson):
        r = RESULTS.get((lesson, s))
        title = api.title(api.LESSONS / lesson / s / "lesson.md")
        if r is None:
            status = "اجرا نشده"
        elif r.get("skipped"):
            status = "رد شد: " + r["skipped"]
        else:
            status = ("✓ پاس" if r["passed"] else "✗ ناقص") + f" ({r['ok']}/{r['n']} تست)"
            done += bool(r["passed"])
        rows.append((s, title, status, (r or {}).get("quiz") or "—"))
    print(f"گزارش درس {lesson}\n" + "=" * 60)
    for s, t, st, qz in rows:
        print(f"{s[:6]}  {st:28s} امتحان: {qz:5s} {t}")
    total = len(rows)
    print("=" * 60 + f"\n{done}/{total} گام پاس شد.")
    print("درس کامل است. 🎉 قدم بعد: درس بعدی یا پروژه‌ی کامل با `python -m support.panel.presets scaffold <preset>`." if done == total
          else "گام‌های ناقص را در بالا اصلاح کن و سلول «بررسی خودکار» همان گام را دوباره اجرا کن؛ بعد این سلول را دوباره بزن.")
    return {"passed": done, "total": total}

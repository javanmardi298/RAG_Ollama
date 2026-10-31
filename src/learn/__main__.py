"""python -m learn <command>

    list                          all lessons with your progress
    start <lesson>                create your answer files in work/ and show step 1
    show <lesson> [step]          lesson text of a step (default: your next step)
    check <lesson> [step]         run the automatic check on work/<lesson>/<step>/answer.py
    hint <lesson> [step] [-l N]   a hint (3 levels: nudge, direction, almost the answer)
    solution <lesson> [step]      the reference solution (after at least one attempt; --force skips that)
    quiz <lesson> [step]          3 questions; wrong ones come back in `review`
    review                        repeat questions you got wrong
    notebook <lesson>             write lessons/<lesson>/<lesson>.ipynb for Colab / Jupyter
    lab <lesson>                  write the notebook and open it in JupyterLab (pip install -r requirements-notebook.txt)
    build                         regenerate lessons/README.md and the guide-only lesson pages from presets/
    selftest                      maintainers / CI: solutions pass, starters fail, links resolve
    errors                        your error diary (work/errors.md)
"""
from __future__ import annotations

import argparse
import sys

from . import api


def _print_check(out: dict) -> int:
    if out["skipped"]:
        print("SKIPPED:", out["skipped"])
        return 0
    for r in out["results"]:
        print(("  ✓ " if r["ok"] else "  ✗ ") + r["name"])
        if not r["ok"]:
            print("      " + r["message"])
            for ln in r.get("trace", [])[-3:]:
                print("      | " + ln.strip())
    if out["passed"]:
        nxt = api.next_step(out["lesson"])
        print(f"\nPASSED {out['step']}. " + (f"Next: python -m learn show {out['lesson']} {nxt}" if nxt else "Lesson complete! Take the quiz: python -m learn quiz " + out["lesson"]))
        return 0
    print("\nNot yet. Read the failing line, then try `python -m learn hint " + out["lesson"] + "` if you are stuck.")
    return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="learn", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd")
    ap.add_argument("lesson", nargs="?")
    ap.add_argument("step", nargs="?")
    ap.add_argument("-l", "--level", type=int)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)

    def step_of():
        return a.step or api.next_step(a.lesson) or api.steps(a.lesson)[-1]

    try:
        if a.cmd == "list":
            for o in api.overview():
                print(f"{o['lesson']:36s} {o['done']}/{o['steps']} steps  [{o['status']}]")
        elif a.cmd in ("start", "show"):
            s = api.show(a.lesson, step_of())
            print(s["text"])
            print(f"\n--- write your answer in: {s['answer_file']}\n--- then run:  python -m learn check {a.lesson} {s['step'][:6]}")
        elif a.cmd == "check":
            return _print_check(api.check(a.lesson, step_of()))
        elif a.cmd == "hint":
            h = api.hint(a.lesson, step_of(), a.level)
            print(f"Hint {h['level']}/{h['of']}:\n{h['hint']}")
        elif a.cmd == "solution":
            r = api.solution(a.lesson, step_of(), a.force)
            print(r["code"] if r["ok"] else r["error"])
        elif a.cmd in ("quiz", "review"):
            qs = [(q["lesson"], q["step"], q["i"], q) for q in api.review()] if a.cmd == "review" else \
                 [(a.lesson, api.steps(a.lesson)[0] if not a.step else a.step, i, q) for i, q in enumerate(api.quiz(a.lesson, step_of()))]
            wrong = []
            for _lid, _st, i, q in qs:
                print(f"\n{q['q']}")
                for k, o in enumerate(q["options"]):
                    print(f"  {k + 1}) {o}")
                got = input("answer number: ").strip()
                ok = got == str(q["answer"] + 1)
                print(("✓ " if ok else "✗ ") + q["why"])
                if not ok:
                    wrong.append(i)
            if a.cmd == "quiz":
                api.record_quiz(a.lesson, step_of(), wrong)
        elif a.cmd == "notebook":
            from . import notebooks
            print("wrote", notebooks.write(a.lesson))
        elif a.cmd == "lab":
            import webbrowser

            from . import lab
            info = lab.start(a.lesson)
            print("JupyterLab:", info["url"], "\n(Ctrl+C to stop)")
            webbrowser.open(info["url"])
            try:
                lab._STATE["proc"].wait()
            except KeyboardInterrupt:
                lab.stop()
        elif a.cmd == "build":
            from . import build
            print(build.build())
        elif a.cmd == "selftest":
            probs = api.selftest(a.lesson)
            print("\n".join(probs) or "selftest ok")
            return 1 if probs else 0
        elif a.cmd == "errors":
            f = api.WORK / "errors.md"
            print(f.read_text(encoding="utf-8") if f.exists() else "no errors recorded yet")
        else:
            ap.error("unknown command")
    except (FileNotFoundError, KeyError) as e:
        print("error:", e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

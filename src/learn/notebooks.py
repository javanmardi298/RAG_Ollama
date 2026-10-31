"""One notebook per lesson, written to be read and run top to bottom (Jupyter, VS Code, Colab).

For every step, in this order:
    lesson text (markdown cells, one per section, up to and including the exercise)
    ✍️  your code      the starter with TODOs: you write it here, in the notebook (no other file needed)
    ▶   demo           the example run of the step (the code is visible first, then you run it)
    ✅  check          automatic tests against what you wrote in the cells above
    🔍  the tests      the source of the check, so you can see what is being tested
    💡  solution       reference solution, folded, for after an honest attempt
    the rest of the lesson text (expected output, what to do if it differs, pitfalls)
    📝  quiz           a few questions (answer in the box)
At the end: a lesson report with every step's result.

build(lesson, mode="solution") produces the same notebook with the reference solution in the code cells; CI executes it to prove
that every notebook runs from the first cell to the report.
"""
from __future__ import annotations

import json
import re
import textwrap

import yaml

from support.config import ROOT

from . import api

CONF = ROOT / "lessons" / "learn.yaml"
MAIN = re.compile(r'^if __name__ == "__main__":\s*$', re.M)


def _conf() -> dict:
    return yaml.safe_load(CONF.read_text(encoding="utf-8")) if CONF.exists() else {}


def _src(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def _md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _src(text.strip("\n"))}


def _code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _src(text.strip("\n"))}


def split_main(source: str) -> tuple[str, str]:
    """(code without the __main__ block, the block's body dedented). The block becomes the visible demo cell."""
    m = MAIN.search(source)
    if not m:
        return source.rstrip() + "\n", ""
    return source[:m.start()].rstrip() + "\n", textwrap.dedent(source[m.end():]).strip("\n")


def sections(text: str) -> list[tuple[str, str]]:
    """Lesson markdown -> [(heading, body markdown including the heading line)]; the first item is the title block."""
    parts = re.split(r"(?m)^(?=## )", text)
    return [((p.splitlines()[0][3:].strip() if p.startswith("## ") else ""), p.strip("\n")) for p in parts if p.strip()]


SKIP_LINES = re.compile(r"فایل پاسخ|python -m learn (show|start|check|hint|quiz)|work[/\\]")
DROP_SECTIONS = ("اجرا کن", "امتحان کوتاه", "گام بعد")           # the notebook has cells for these


def _links_off(text: str) -> str:
    """Relative links do not work inside a notebook; lines that describe the command-line / file workflow are dropped."""
    text = "\n".join(ln for ln in text.splitlines() if not SKIP_LINES.search(ln))
    return re.sub(r"\]\((?!https?:|#)[^)]*\)", "](#)", text)


def _intro(lesson: str, repo: str, branch: str) -> list[dict]:
    badge = f"https://colab.research.google.com/github/{repo}/blob/{branch}/lessons/{lesson}/{lesson}.ipynb"
    return [
        _md(f"# {lesson}\n\n[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({badge})\n\n"
            "**روال هر گام:** ۱) متن را بخوان ۲) کد را ببین و کامل کن (✍️) ۳) سلول را اجرا کن (Shift+Enter) ۴) «بررسی خودکار» (✅) "
            "را اجرا کن ۵) امتحان کوتاه (📝). در پایان «گزارش نهایی درس» نتیجه‌ی همه‌ی گام‌ها را نشان می‌دهد.\n\n"
            "همه‌ی کد همین‌جا نوشته و اجرا می‌شود؛ به فایل جداگانه‌ای نیاز نیست. سلول‌ها را **به ترتیب** اجرا کن."),
        _code("# 1) آماده‌سازی (Colab: پروژه را clone و نصب می‌کند؛ محلی: اگر داخل پوشه‌ی پروژه‌ای چیزی تغییر نمی‌کند)\n"
              "import os, sys, subprocess\n"
              "if 'google.colab' in sys.modules and not os.path.exists('repo'):\n"
              f"    subprocess.run(['git', 'clone', '--depth', '1', '-b', '{branch}', 'https://github.com/{repo}.git', 'repo'], check=True)\n"
              "    subprocess.run([sys.executable, '-m', 'pip', '-q', 'install', '-r', 'repo/requirements.txt', '-e', 'repo'], check=True)\n"
              "if os.path.exists('repo'):\n"
              "    os.chdir('repo')\n"
              "while not os.path.exists('lessons') and os.getcwd() != os.path.dirname(os.getcwd()):   # باز کردن از داخل lessons/...\n"
              "    os.chdir(os.path.dirname(os.getcwd()))\n"
              "print('پوشه‌ی کار:', os.getcwd())"),
        _md("### مدل زبانی درس‌ها\nپیش‌فرض `offline` است (بدون نصب؛ شکل کار را نشان می‌دهد). برای جواب واقعی یکی از خط‌های زیر را از حالت "
            "توضیح (`#`) دربیاور. کلید API را **داخل notebook ننویس** (commit می‌شود)؛ از `.env` یا `getpass` استفاده کن."),
        _code("import os\n"
              "os.environ['LEARN_PROVIDER'] = 'offline'      # 'offline' | 'ollama' | 'anthropic' | 'opencode' | 'openai_compatible'\n"
              "# os.environ['LEARN_PROVIDER'] = 'ollama';     os.environ['LEARN_MODEL'] = 'qwen2.5:7b'\n"
              "# os.environ['LEARN_PROVIDER'] = 'anthropic';  os.environ['LEARN_MODEL'] = 'claude-sonnet-5-5'; os.environ['LEARN_BUDGET_USD'] = '0.5'\n"
              "#   import getpass; os.environ['ANTHROPIC_API_KEY'] = getpass.getpass('ANTHROPIC_API_KEY: ')   # اشتراک Claude.ai کلید API نیست\n"
              "# os.environ['LEARN_PROVIDER'] = 'opencode';   os.environ['LEARN_MODEL'] = 'anthropic/claude-sonnet-5-5'\n"
              "# os.environ['LEARN_PROVIDER'] = 'openai_compatible'; os.environ['LEARN_API_BASE'] = 'http://localhost:1234/v1'; os.environ['LEARN_MODEL'] = '...'\n"
              "from learn import llm as learn_llm\n"
              "reply = learn_llm.get().chat([{'role': 'user', 'content': 'Reply with the single word OK.'}])\n"
              "print(os.environ['LEARN_PROVIDER'], '->', reply.content[:80], f'({reply.latency_s:.1f}s)')"),
    ]


def _step_cells(lesson: str, step: str, mode: str) -> list[dict]:
    sd = api.LESSONS / lesson / step
    text = (sd / "lesson.md").read_text(encoding="utf-8")
    secs = sections(text)
    starter = (sd / ("solution.py" if mode == "solution" else "starter.py")).read_text(encoding="utf-8")
    solution = (sd / "solution.py").read_text(encoding="utf-8")
    code, demo = split_main(starter)
    sol_code, _ = split_main(solution)
    check_src = (sd / "check.py").read_text(encoding="utf-8")
    ex = next((i for i, (h, _) in enumerate(secs) if h.startswith("تمرین کد")), len(secs) - 1)
    cells = [_md("---")]
    cells += [_md(_links_off(body)) for _, body in secs[:ex + 1]]
    cells += [_md("### ✍️ کد تو\nکد زیر را ببین، TODO ها را کامل کن و سلول را اجرا کن (Shift+Enter). این‌جا می‌نویسی، نه در فایل دیگر."
                  if mode != "solution" else "### ✍️ کد (نسخه‌ی مرجع)"), _code(code)]
    if demo:
        cells += [_md("### ▶ اجرای نمایشی\nاول کد را بخوان، بعد اجرا کن. این سلول از توابعی که بالا نوشتی استفاده می‌کند."), _code(demo)]
    cells += [_md("### ✅ بررسی خودکار\nتست‌ها را روی چیزی که در سلول‌های بالا نوشتی اجرا می‌کند. ✗ = هنوز نه؛ پیام را بخوان و سلول کد را اصلاح و دوباره اجرا کن."),
              _code(f"from learn.notebook import check_cell\ncheck_cell({lesson!r}, {step!r}, globals())"),
              _md("<details><summary><b>🔍 این تست‌ها دقیقاً چه چیزی را می‌سنجند؟</b> (کد تست)</summary>\n\n```python\n" + check_src.strip() + "\n```\n\n</details>")]
    if mode != "solution":
        cells += [_md("<details><summary><b>💡 جواب مرجع</b> (بعد از یک تلاش واقعی باز کن)</summary>\n\n```python\n"
                      + sol_code.strip() + "\n```\n\n</details>")]
    cells += [_md(_links_off(body)) for h, body in secs[ex + 1:] if h and not h.startswith(DROP_SECTIONS)]
    cells += [_md("### 📝 امتحان کوتاه\nبه هر سؤال با شماره‌ی گزینه جواب بده."),
              _code(f"from learn.notebook import quiz_cell\nquiz_cell({lesson!r}, {step!r})")]
    return cells


def build(lesson: str, mode: str = "student") -> dict:
    c = _conf()
    cells = _intro(lesson, c.get("repo", "OWNER/REPO"), c.get("branch", "main"))
    for s in api.steps(lesson):
        cells += _step_cells(lesson, s, mode)
    cells += [_md("---\n## 🏁 گزارش نهایی درس\nنتیجه‌ی تست و امتحان هر گام، و آنچه هنوز مانده."),
              _code(f"from learn.notebook import lesson_report\nlesson_report({lesson!r})")]
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                         "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}


def write(lesson: str) -> str:
    path = ROOT / "lessons" / lesson / f"{lesson}.ipynb"
    path.write_text(json.dumps(build(lesson), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))

# ساختن مجموعه‌ی Agent Skills (SKILL.md) با تست، از صفر در GitHub

سه skill برای عامل‌های کدنویسی (Claude Code و ابزارهای سازگار) می‌سازی: گزارش وضعیت پروژه، بررسی فاکتور با اسکریپت، و خلاصه‌ی جلسه. یک ابزار کوچک هم می‌نویسی که skill ها را اعتبارسنجی کند، هزینه‌ی context را بسنجد و تست کند هر skill کی فعال شود. بدون GPU و بدون مدل.

> نسخه‌ی تعاملی (تیک مراحل، مقایسه‌ی خروجی، پرسیدن از Claude، دانلود notebook): صفحه‌ی «راهنمای ساخت پروژه‌ها» (claude.ai artifact).

**برای فهمیدن بهتر:** پروژه در نقشه‌ی راه (نقشه‌ی راه، پروژه‌ی `p30_agent_skills`) · [پژوهش ۲۰۲۶: Agent Skills](../../docs/research_2026.md)

## مراحل
1. ساختن repo در GitHub
2. فایل .gitignore
3. فایل requirements.txt
4. skill اول: skills/project-report/SKILL.md
5. فایل skills/project-report/scripts/summarize.py
6. فایل skills/invoice-check/SKILL.md
7. فایل skills/invoice-check/reference/schema.json
8. فایل skills/invoice-check/scripts/validate_invoice.py
9. فایل skills/meeting-notes/SKILL.md
10. فایل examples/invoice_ok.json
11. فایل examples/invoice_bad.json
12. فایل examples/activation_tests.json
13. ابزار: skills_kit.py
14. فایل check_setup.py
15. تست‌ها: tests/test_skills.py
16. تست خودکار در GitHub (Actions)
17. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
18. ساختن و اجرای notebook
19. استفاده‌ی واقعی در Claude Code (اختیاری)
20. commit و push از VS Code
21. README نهایی
22. صیقل نهایی repo

## 1. ساختن repo در GitHub
_GitHub · حدود 3 دقیقه_

**چرا:** repo خودت نمونه‌کار توست: هر فایلی که اینجا می‌سازی، کارفرما می‌بیند. اسم و توضیح کوتاه و دقیق، اولین چیزی است که دیده می‌شود.

1. در github.com بالا سمت راست **+** → **New repository**.
2. **Repository name:** `agent_skills`
3. **Description:** `Agent Skills (SKILL.md) for coding agents: project report, invoice check and meeting notes, with a toolkit that validates skills, measures context cost and tests activation`
4. **Public** را انتخاب کن (برای نمونه‌کار و Actions رایگان).
5. تیک **Add a README file**، **Add .gitignore:** None (خودمان می‌سازیم)، **Choose a license:** MIT License → **Create repository**.

> **باید ببینی:** repo دو فایل دارد: `README.md` و `LICENSE`. در LICENSE اگر نام تو در خط Copyright نیست، با آیکون مداد اصلاحش کن.

## 2. فایل .gitignore
_GitHub · حدود 2 دقیقه_

**چرا:** به git می‌گوید چه چیزهایی هرگز وارد repo نشوند: محیط مجازی، فایل‌های موقت، و `.env` که کلید API در آن است. **قبل از** هر فایل دیگری بساز.

1. **Add file** → **Create new file**، نام `.gitignore`، متن زیر را paste کن. commit: `Add .gitignore`.

`.gitignore`

````
# Python and editors
.venv/
__pycache__/
.ipynb_checkpoints/
.pytest_cache/
.DS_Store

# secrets: API keys live here, never in git
.env
````

## 3. فایل requirements.txt
_GitHub · حدود 2 دقیقه_

**چرا:** فقط `pyyaml` برای خواندن frontmatter، به‌علاوه‌ی pytest و ipykernel.

1. **Add file → Create new file**، نام `requirements.txt`. commit: `Add requirements`.

`requirements.txt`

````
pyyaml>=6.0
pytest>=8.0
ipykernel>=6.29
````

## 4. skill اول: skills/project-report/SKILL.md
_GitHub · حدود 3 دقیقه_

**چرا:** یک skill = یک پوشه با `SKILL.md`. بالای فایل بین دو `---` نام و توضیح می‌آید؛ توضیح باید بگوید skill چه می‌کند و **کی** استفاده شود («Use when ...»)، چون عامل فقط همین را همیشه می‌بیند و از روی آن تصمیم می‌گیرد. بقیه‌ی متن دستورالعمل است و فقط وقتی skill لازم شد خوانده می‌شود.

1. **Add file → Create new file**، در کادر نام بنویس `skills/project-report/SKILL.md` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add project-report skill`.

`skills/project-report/SKILL.md`

````
---
name: project-report
description: Summarise a project's latest results (results/*.json) into a short status report with numbers, gaps and next steps. Use when the user asks how a project is doing, for a status report, or what to do next.
---

# Project report

1. Run `python scripts/summarize.py <project folder>`; it prints every `results/*.json` as compact key numbers.
2. Write the report in this order: the headline metric, what changed since the last run, the weakest part, at most three next steps.
3. Never invent a number. If a results file is missing, say which step has not run yet.
````

## 5. فایل skills/project-report/scripts/summarize.py
_GitHub · حدود 2 دقیقه_

**چرا:** اسکریپت قطعی که عددهای `results/*.json` را بیرون می‌کشد. کاری که با کد قابل انجام است را به استدلال مدل نسپار.

1. **Add file → Create new file**، در کادر نام بنویس `skills/project-report/scripts/summarize.py` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add summarize script`.

`skills/project-report/scripts/summarize.py`

````python
"""Print the numbers in every results/*.json of a project folder (nested keys joined with '.')."""
import json
import sys
from pathlib import Path


def flatten(d, prefix=""):
    out = {}
    for k, v in (d.items() if isinstance(d, dict) else enumerate(d)):
        key = f"{prefix}{k}"
        if isinstance(v, (dict, list)):
            out.update(flatten(v, key + "."))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[key] = v
    return out


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
files = sorted(root.glob("results/*.json"))
if not files:
    print("no results/*.json found: has the notebook been run?")
for f in files:
    nums = flatten(json.loads(f.read_text(encoding="utf-8")))
    print(f.name, "|", ", ".join(f"{k}={v}" for k, v in list(nums.items())[:12]))
````

## 6. فایل skills/invoice-check/SKILL.md
_GitHub · حدود 2 دقیقه_

**چرا:** skill دوم: بررسی فاکتور. دقت کن قاعده‌ها (جمع، تاریخ) در اسکریپت‌اند و دستور صریح دارد که عدد را بی‌صدا «درست» نکند.

1. **Add file → Create new file**، در کادر نام بنویس `skills/invoice-check/SKILL.md` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add invoice-check skill`.

`skills/invoice-check/SKILL.md`

````
---
name: invoice-check
description: Check an invoice or receipt the user shares (as text or JSON) - required fields, total equals net plus tax, date not in the future - and report problems without fixing numbers silently. Use when the user shares an invoice or receipt and wants it checked or its data extracted.
---

# Invoice check

1. Put the invoice fields into JSON matching `reference/schema.json` (supplier, number, date, net, tax, total, iban).
2. Run `python scripts/validate_invoice.py <file.json>`; it lists every failed rule.
3. Report each failed rule and ask the user; never change a number to make the totals match.
4. When you show the IBAN, mask everything except the last 4 characters.
````

## 7. فایل skills/invoice-check/reference/schema.json
_GitHub · حدود 2 دقیقه_

**چرا:** فایل مرجع: ساختار JSON فاکتور. skill به آن اشاره می‌کند و عامل فقط وقتی لازم شد می‌خواندش.

1. **Add file → Create new file**، در کادر نام بنویس `skills/invoice-check/reference/schema.json` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add invoice schema`.

`skills/invoice-check/reference/schema.json`

````json
{"type": "object", "required": ["supplier", "number", "date", "total"],
 "properties": {"supplier": {"type": "string"}, "number": {"type": "string"}, "date": {"type": "string", "format": "date"},
                "net": {"type": "number"}, "tax": {"type": "number"}, "total": {"type": "number"}, "iban": {"type": "string"}}}
````

## 8. فایل skills/invoice-check/scripts/validate_invoice.py
_GitHub · حدود 3 دقیقه_

**چرا:** اسکریپت اعتبارسنجی فاکتور: فیلدهای لازم، جمع = خالص + مالیات، تاریخ نه در آینده، و پنهان کردن IBAN. کد خروج ۱ یعنی مشکل دارد.

1. **Add file → Create new file**، در کادر نام بنویس `skills/invoice-check/scripts/validate_invoice.py` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add invoice validation script`.

`skills/invoice-check/scripts/validate_invoice.py`

````python
"""Validate an invoice JSON: required fields, total = net + tax (to the cent), date not in the future. Exit code 1 on problems."""
import datetime as dt
import json
import sys

REQUIRED = ["supplier", "number", "date", "total"]


def problems(inv, today=None):
    today = today or dt.date.today()
    out = [f"missing field: {f}" for f in REQUIRED if inv.get(f) in (None, "")]
    if all(isinstance(inv.get(k), (int, float)) for k in ("net", "tax", "total")) and abs(inv["net"] + inv["tax"] - inv["total"]) > 0.01:
        out.append(f"total {inv['total']} is not net {inv['net']} + tax {inv['tax']}")
    try:
        if inv.get("date") and dt.date.fromisoformat(inv["date"]) > today:
            out.append(f"date {inv['date']} is in the future")
    except ValueError:
        out.append(f"date {inv['date']!r} is not YYYY-MM-DD")
    return out


def mask_iban(iban):
    s = iban.replace(" ", "")
    return "*" * (len(s) - 4) + s[-4:] if len(s) > 4 else s


if __name__ == "__main__":
    inv = json.load(open(sys.argv[1], encoding="utf-8"))
    found = problems(inv)
    print("\n".join(found) if found else "invoice ok")
    if inv.get("iban"):
        print("iban:", mask_iban(inv["iban"]))
    sys.exit(1 if found else 0)
````

## 9. فایل skills/meeting-notes/SKILL.md
_GitHub · حدود 2 دقیقه_

**چرا:** skill سوم، فقط دستورالعمل و بدون اسکریپت: قالب خروجی ثابت و قاعده‌ی «حدس نزن» برای مسئول و تاریخ.

1. **Add file → Create new file**، در کادر نام بنویس `skills/meeting-notes/SKILL.md` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add meeting-notes skill`.

`skills/meeting-notes/SKILL.md`

````
---
name: meeting-notes
description: Turn a meeting transcript or rough notes into decisions, action items with an owner and a due date, and open questions. Use when the user pastes a transcript or meeting notes and wants a summary or the action items.
---

# Meeting notes

Output three sections, in this order:
1. **Decisions** - one line each, in the past tense.
2. **Action items** - `owner - task - due date`; write `owner: ?` or `due: ?` when the notes do not say, never guess.
3. **Open questions** - what was raised but not decided.

Keep names exactly as written in the notes. No section longer than 8 lines.
````

## 10. فایل examples/invoice_ok.json
_GitHub · حدود 2 دقیقه_

**چرا:** نمونه‌ی فاکتور درست برای تست اسکریپت.

1. **Add file → Create new file**، در کادر نام بنویس `examples/invoice_ok.json` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add example invoices`.

`examples/invoice_ok.json`

````json
{"supplier": "Acme Office Supplies", "number": "INV-2041", "date": "2026-03-14", "net": 200.0, "tax": 38.0, "total": 238.0,
 "iban": "DE89 3704 0044 0532 0130 00"}
````

## 11. فایل examples/invoice_bad.json
_GitHub · حدود 2 دقیقه_

**چرا:** نمونه‌ی فاکتور با سه مشکل: شماره‌ی خالی، تاریخ آینده، جمع اشتباه.

1. **Add file → Create new file**، در کادر نام بنویس `examples/invoice_bad.json` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add a broken example invoice`.

`examples/invoice_bad.json`

````json
{"supplier": "Acme Office Supplies", "number": "", "date": "2099-01-01", "net": 200.0, "tax": 38.0, "total": 250.0}
````

## 12. فایل examples/activation_tests.json
_GitHub · حدود 2 دقیقه_

**چرا:** هشت درخواست کاربر با skill درستی که باید فعال شود (یا هیچ‌کدام). مثل مجموعه‌ی ارزیابی برای توضیح‌ها.

1. **Add file → Create new file**، در کادر نام بنویس `examples/activation_tests.json` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add activation test cases`.

`examples/activation_tests.json`

````json
[{"request": "how is the project doing? give me a status report", "skill": "project-report"},
 {"request": "what should I do next on this project, based on the results", "skill": "project-report"},
 {"request": "here is a receipt, check the totals", "skill": "invoice-check"},
 {"request": "extract the data from this invoice", "skill": "invoice-check"},
 {"request": "summarise this meeting transcript and list the action items", "skill": "meeting-notes"},
 {"request": "who owns which task from yesterday's meeting notes", "skill": "meeting-notes"},
 {"request": "what's the weather in Berlin", "skill": null},
 {"request": "write a poem about autumn", "skill": null}]
````

## 13. ابزار: skills_kit.py
_GitHub · حدود 4 دقیقه_

**چرا:** اعتبارسنجی skill ها (نام، توضیح، فایل‌های ارجاع‌شده)، اندازه‌ی context (همیشه در context در برابر فقط هنگام نیاز)، و یک تست فعال‌سازی ساده با کلمه‌های مشترک. عامل واقعی با مدل تصمیم می‌گیرد، ولی این تست جلوی توضیح‌های مبهم را می‌گیرد.

1. **Add file → Create new file**، در کادر نام بنویس `skills_kit.py`. commit: `Add skills toolkit: validation, context cost, activation test`.

`skills_kit.py`

````python
"""Agent Skills toolkit: validate SKILL.md folders, estimate their context cost (progressive disclosure), and test when each
skill should activate with a simple keyword proxy (a real agent decides from the description)."""
import json
import re
from pathlib import Path

import yaml

NAME = re.compile(r"[a-z0-9-]{1,64}")
STOP = {"the", "a", "an", "and", "or", "to", "of", "is", "when", "use", "user", "asks", "for", "it", "in", "this", "with", "as", "me",
        "please", "here", "give", "out", "how", "what", "one", "its", "into", "wants", "on", "from", "be", "are", "at", "by", "who",
        "which", "should", "do", "next", "based", "s", "data", "list"}


def load_skills(folder="skills"):
    """name -> {"meta": frontmatter, "body": markdown, "dir": path}. Raises ValueError for a SKILL.md without frontmatter."""
    out = {}
    for f in sorted(Path(folder).glob("*/SKILL.md")):
        m = re.match(r"---\n(.*?)\n---\n(.*)", f.read_text(encoding="utf-8"), re.S)
        if not m:
            raise ValueError(f"{f}: missing --- frontmatter ---")
        meta = yaml.safe_load(m.group(1)) or {}
        out[meta.get("name", f.parent.name)] = {"meta": meta, "body": m.group(2), "dir": f.parent}
    return out


def validate(skills):
    """Problems: name format and folder, description length and a 'Use when' clause, referenced files exist."""
    problems = []
    for name, s in skills.items():
        desc = s["meta"].get("description", "")
        if name != s["dir"].name or not NAME.fullmatch(name):
            problems.append(f"{name}: name must equal the folder name (lowercase letters, digits, hyphens)")
        if not 40 <= len(desc) <= 1024:
            problems.append(f"{name}: description should be 40-1024 characters")
        if "use when" not in desc.lower():
            problems.append(f"{name}: description should say when to use the skill ('Use when ...')")
        for ref in re.findall(r"`((?:scripts|reference)/[^`\s]+)", s["body"]):
            if not (s["dir"] / ref).exists():
                problems.append(f"{name}: references a missing file {ref}")
    return problems


def tokens(text):
    """About 4 characters per token: good enough to compare sizes."""
    return max(1, len(text) // 4)


def context_cost(skills):
    """Always in context: name + description. Loaded only when used: the body (and files it reads)."""
    always = sum(tokens(s["meta"]["name"] + s["meta"]["description"]) for s in skills.values())
    bodies = sum(tokens(s["body"]) for s in skills.values())
    return {"always_loaded_tokens": always, "on_demand_tokens": bodies, "if_all_in_prompt_tokens": always + bodies}


def words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP and len(w) > 2}


def activate(request, skills, min_overlap=2):
    """Keyword proxy for 'which skill fits this request' (a real agent reads the descriptions); None if nothing fits."""
    scores = {n: len(words(request) & words(s["meta"]["description"])) for n, s in skills.items()}
    best = max(scores, key=scores.get) if scores else None
    return best if best and scores[best] >= min_overlap else None


def activation_report(skills, cases_path="examples/activation_tests.json"):
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    rows = [{"request": c["request"], "expected": c["skill"], "got": activate(c["request"], skills)} for c in cases]
    return {"correct": sum(r["expected"] == r["got"] for r in rows), "total": len(rows), "rows": rows}
````

<details><summary><b>درک کد: تابع به تابع</b></summary>

- **`load_skills`**: هر `skills/*/SKILL.md` خوانده می‌شود: بین دو `---` frontmatter (YAML) و بعد بدنه.
- **`validate`**: قاعده‌های قالب: نام = نام پوشه، توضیح ۴۰ تا ۱۰۲۴ حرف با «Use when»، و وجود فایل‌هایی که بدنه به آن‌ها اشاره می‌کند.
- **`tokens و context_cost`**: progressive disclosure با عدد: نام و توضیح همیشه در context، بدنه فقط هنگام نیاز.
- **`words، activate، activation_report`**: تقریب ساده‌ی «کدام skill به این درخواست می‌خورد» با کلمه‌های مشترک؛ عامل واقعی با مدل تصمیم می‌گیرد، ولی این تست توضیح‌های مبهم را پیدا می‌کند.

</details>

## 14. فایل check_setup.py
_GitHub · حدود 2 دقیقه_

**چرا:** یک بررسی کوچک که بعد از نصب روی لپ‌تاپ اجرا می‌کنی تا مطمئن شوی پایتون، داده و توابع اصلی کار می‌کنند، قبل از notebook.

1. **Add file → Create new file**، نام `check_setup.py`. commit: `Add setup check`.

`check_setup.py`

````python
"""Run once after installing: checks Python, the skills and their validation."""
import sys

from skills_kit import load_skills, validate

print("Python", sys.version.split()[0])
skills = load_skills()
print(len(skills), "skills:", ", ".join(skills))
print("problems:", validate(skills) or "none")
print("setup ok")
````

## 15. تست‌ها: tests/test_skills.py
_GitHub · حدود 3 دقیقه_

**چرا:** تست‌ها چک می‌کنند skill ها معتبر باشند، اعتبارسنج اشتباه‌های رایج را بگیرد، progressive disclosure context را کم کند، فعال‌سازی درست باشد و اسکریپت فاکتور مشکل‌ها را پیدا کند.

1. **Add file → Create new file**، نام `tests/test_skills.py`. commit: `Add tests`.

`tests/test_skills.py`

````python
import json
import subprocess
import sys

from skills_kit import activate, activation_report, context_cost, load_skills, validate


def test_skills_are_valid():
    assert validate(load_skills()) == []


def test_validation_catches_mistakes(tmp_path):
    d = tmp_path / "skills" / "Bad_Name"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: Bad_Name\ndescription: does things\n---\nRun `scripts/missing.py`.\n")
    probs = " ".join(validate(load_skills(tmp_path / "skills")))
    assert "name must equal" in probs and "40-1024" in probs and "Use when" in probs and "missing file" in probs


def test_progressive_disclosure_saves_context():
    c = context_cost(load_skills())
    assert c["always_loaded_tokens"] < c["if_all_in_prompt_tokens"]


def test_activation():
    skills = load_skills()
    assert activate("check the totals of this invoice", skills) == "invoice-check"
    assert activate("write a poem about autumn", skills) is None
    assert activation_report(skills)["correct"] >= 6


def test_invoice_script(tmp_path):
    script = "skills/invoice-check/scripts/validate_invoice.py"
    ok = subprocess.run([sys.executable, script, "examples/invoice_ok.json"], capture_output=True, text=True)
    bad = subprocess.run([sys.executable, script, "examples/invoice_bad.json"], capture_output=True, text=True)
    assert ok.returncode == 0 and "invoice ok" in ok.stdout and "******************3000" in ok.stdout.replace(" ", "")
    assert bad.returncode == 1 and "missing field: number" in bad.stdout and "in the future" in bad.stdout and "not net" in bad.stdout
    json.loads(open("examples/invoice_bad.json").read())
````

## 16. تست خودکار در GitHub (Actions)
_GitHub · حدود 3 دقیقه_

**چرا:** با هر push، GitHub تست‌ها را روی یک ماشین تمیز اجرا می‌کند. تیک سبز یعنی پروژه روی هر سیستمی کار می‌کند، نه فقط لپ‌تاپ تو.

1. **Add file → Create new file**، نام `.github/workflows/tests.yml`. commit: `Add CI`.
2. به تب **Actions** برو و چند ثانیه صبر کن.

`.github/workflows/tests.yml`

````
name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python check_setup.py
      - run: pytest -q
````

> **باید ببینی:** در تب Actions یک اجرای `tests` با تیک سبز. اگر قرمز شد، رویش کلیک کن: خطا دقیقاً می‌گوید کدام فایل یا خط.

## 17. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
_VS Code · حدود 8 دقیقه_

**چرا:** محیط مجازی (venv) یک پایتون جدا فقط برای این پروژه است تا بسته‌هایش با پروژه‌های دیگر قاطی نشوند.

پیش‌نیاز: Git (از git-scm.com) و Python 3.10 یا جدیدتر، و در VS Code افزونه‌های **Python** و **Jupyter** از Microsoft.

1. VS Code: `Ctrl+Shift+P` → **Git: Clone** → آدرس `https://github.com/<نام-کاربری-تو>/agent_skills.git` → یک پوشه انتخاب کن → **Open**.
2. ترمینال را باز کن: ``Ctrl+` ``

_ترمینال VS Code · Windows PowerShell_

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

_ترمینال VS Code_

```
python check_setup.py
python -m pytest -q
```

**باید ببینی:**

```
Python 3.x.y
3 skills: invoice-check, meeting-notes, project-report
problems: none
setup ok

.....                                                                    [100%]
5 passed
```

> **حواست باشد:** اگر PowerShell گفت running scripts is disabled: یک بار `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` و دوباره فعال کن. روی Mac/Linux به‌جای خط دوم: `source .venv/bin/activate`.

## 18. ساختن و اجرای notebook
_VS Code · حدود 15 دقیقه_

**چرا:** notebook نشان می‌دهد skill ها چطور ارزیابی می‌شوند: اعتبارسنجی، هزینه‌ی context، تست فعال‌سازی و اجرای اسکریپت.

1. VS Code: `Ctrl+Shift+P` → **Create: New Jupyter Notebook** → `Ctrl+S` با نام `01_agent_skills.ipynb` در پوشه‌ی repo.
2. بالا سمت راست **Select Kernel → Python Environments → .venv**.
3. سلول‌ها را به ترتیب زیر بساز (متن: **+ Markdown**، کد: **+ Code**) و هر سلول کد را با `Shift+Enter` اجرا کن. خروجی را با «باید ببینی» زیرش مقایسه کن.

_سلول متنی (Markdown):_

````markdown
# Agent Skills: packaging procedures as SKILL.md folders

A skill is a folder with a `SKILL.md` (a short name and description in the frontmatter, then instructions) and
optional scripts and reference files. An agent (Claude Code, the Claude Agent SDK and other compatible tools) keeps
only the name and description in its context and reads the rest when a request needs it (progressive disclosure).
This notebook validates three skills, measures their context cost, tests when each should activate, and runs one
skill's script.
````

_سلول کد 1:_

```python
from skills_kit import activation_report, context_cost, load_skills, validate

skills = load_skills()
for name, s in skills.items():
    print(f"{name:15s} {s['meta']['description'][:70]}...")
print("problems:", validate(skills) or "none")
```

سه skill و نتیجه‌ی اعتبارسنجی: نام برابر نام پوشه، توضیح با «Use when ...»، و وجود فایل‌هایی که SKILL.md به آن‌ها اشاره می‌کند.

**باید ببینی:**

```
invoice-check   Check an invoice or receipt the user shares (as text or JSON) - requir...
meeting-notes   Turn a meeting transcript or rough notes into decisions, action items ...
project-report  Summarise a project's latest results (results/*.json) into a short sta...
problems: none
```

_سلول متنی (Markdown):_

````markdown
## Context cost: why only the description is always loaded
````

_سلول کد 2:_

```python
print(context_cost(skills))
```

با progressive disclosure فقط نام و توضیح همیشه در context است؛ بدنه وقتی لازم شد خوانده می‌شود. با ده‌ها skill این تفاوت بزرگ می‌شود.

**باید ببینی:**

```
{'always_loaded_tokens': 183, 'on_demand_tokens': 274, 'if_all_in_prompt_tokens': 457}
```

_سلول متنی (Markdown):_

````markdown
## When does each skill activate?
A keyword proxy over the descriptions; a real agent decides from the description with the model, so a good description
matters more than anything else in the skill.
````

_سلول کد 3:_

```python
report = activation_report(skills)
for r in report["rows"]:
    mark = "ok " if r["expected"] == r["got"] else "MISS"
    print(f"{mark} {r['request'][:52]:52s} expected={r['expected']} got={r['got']}")
print(f"\n{report['correct']}/{report['total']} correct")
```

یک مورد رد می‌شود: «extract the data from this invoice» با توضیح invoice-check کلمه‌ی مشترک کافی ندارد. تمرین: توضیح invoice-check را طوری بهتر کن که این را هم بگیرد (مثلاً «extract») و دوباره اجرا کن.

**باید ببینی:**

```
ok  how is the project doing? give me a status report    expected=project-report got=project-report
ok  what should I do next on this project, based on the  expected=project-report got=project-report
ok  here is a receipt, check the totals                  expected=invoice-check got=invoice-check
MISS extract the data from this invoice                   expected=invoice-check got=None
ok  summarise this meeting transcript and list the actio expected=meeting-notes got=meeting-notes
ok  who owns which task from yesterday's meeting notes   expected=meeting-notes got=meeting-notes
ok  what's the weather in Berlin                         expected=None got=None
ok  write a poem about autumn                            expected=None got=None

7/8 correct
```

_سلول متنی (Markdown):_

````markdown
## A skill with a script: invoice-check
````

_سلول کد 4:_

```python
import subprocess, sys

for f in ["examples/invoice_ok.json", "examples/invoice_bad.json"]:
    out = subprocess.run([sys.executable, "skills/invoice-check/scripts/validate_invoice.py", f], capture_output=True, text=True)
    print(f, "-> exit", out.returncode)
    print("   " + out.stdout.strip().replace("\n", "\n   "))
```

قاعده‌های قطعی (جمع، تاریخ، فیلد خالی) در اسکریپت‌اند، نه در استدلال مدل. مدل اسکریپت را اجرا می‌کند و نتیجه را گزارش می‌دهد.

**باید ببینی:**

```
examples/invoice_ok.json -> exit 0
   invoice ok
   iban: ******************3000
examples/invoice_bad.json -> exit 1
   missing field: number
   total 250.0 is not net 200.0 + tax 38.0
   date 2099-01-01 is in the future
```

_سلول متنی (Markdown):_

````markdown
## Save the results
````

_سلول کد 5:_

```python
import json, os

os.makedirs("results", exist_ok=True)
with open("results/results.json", "w") as f:
    json.dump({"skills": list(skills), "problems": validate(skills), "context": context_cost(skills),
               "activation": {"correct": report["correct"], "total": report["total"]}}, f, indent=2)
print(open("results/results.json").read())
```

خلاصه‌ی نتایج برای README.

**باید ببینی:**

```
{
  "skills": [
    "invoice-check",
    "meeting-notes",
    "project-report"
  ],
  "problems": [],
  "context": {
    "always_loaded_tokens": 183,
    "on_demand_tokens": 274,
    "if_all_in_prompt_tokens": 457
  },
  "activation": {
    "correct": 7,
    "total": 8
  }
}
```

> **نکته:** اگر نمی‌خواهی سلول‌ها را یکی‌یکی بسازی: دکمه‌ی **دانلود notebook** بالای سلول‌ها فایل آماده را می‌دهد؛ در پوشه‌ی repo بگذار و Run All. ولی یک بار دستی ساختن، کد را بهتر در ذهنت می‌نشاند.

## 19. استفاده‌ی واقعی در Claude Code (اختیاری)
_VS Code · Ollama / Claude / OpenCode · حدود 10 دقیقه_

**چرا:** skill ها برای عامل‌ها ساخته شده‌اند. در Claude Code آن‌ها را در پوشه‌ی skills پروژه بگذار و ببین کی و چطور استفاده می‌شوند.

1. در ترمینال VS Code (داخل repo):
2. بعد Claude Code را در همین پوشه باز کن و بگو: «summarise the results of this project» یا «check this invoice: ...».

_Windows PowerShell: skill ها را برای Claude Code همین پروژه فعال کن_

```
New-Item -ItemType Directory -Force .claude\skills | Out-Null
Copy-Item -Recurse -Force skills\* .claude\skills\
```

_Mac/Linux_

```
mkdir -p .claude/skills && cp -r skills/* .claude/skills/
```

> **حواست باشد:** skill شخص ثالث را بدون خواندن نصب نکن: اسکریپت‌هایش روی سیستم تو اجرا می‌شوند. پوشه‌ی `.claude/` را اگر نمی‌خواهی commit شود به `.gitignore` اضافه کن.

## 20. commit و push از VS Code
_VS Code · GitHub · حدود 3 دقیقه_

**چرا:** notebook با خروجی‌هایش و فایل نتایج باید در GitHub باشند تا بدون اجرا دیده شوند.

1. پنل Source Control: `Ctrl+Shift+G`. فایل‌های `01_agent_skills.ipynb` و `results/results.json` را می‌بینی.
2. پیام: `Add notebook: validation, context cost, activation, invoice script` → **Commit** → **Sync Changes**.

> **باید ببینی:** در GitHub، `01_agent_skills.ipynb` را باز کن: جدول‌ها و خروجی‌ها بدون اجرا دیده می‌شوند. تب Actions دوباره سبز است.

> **حواست باشد:** قانون ساده: قبل از هر کار در VS Code اول **Pull** بزن، و یک فایل را هم‌زمان در GitHub و VS Code ویرایش نکن.

## 21. README نهایی
_GitHub · حدود 10 دقیقه_

**چرا:** README صفحه‌ی اول پروژه است: در ۳۰ ثانیه بگوید چه مسئله‌ای، چه روشی، چه عددی و چه محدودیتی. عددها را از `results/results.json` خودت بردار، نه از این صفحه.

1. در GitHub روی `README.md` → آیکون مداد → متن زیر را جایگزین کن و عددهای `{...}` را پر کن (یا results.json را پایین paste کن). commit: `Write README`.
2. نام کاربری‌ات را در خط badge جایگزین کن.

````markdown
# Agent Skills: team procedures as SKILL.md folders

![tests](https://github.com/<your-user>/agent_skills/actions/workflows/tests.yml/badge.svg)

Three skills for coding agents (Claude Code, the Claude Agent SDK and other tools that read `SKILL.md`):

| skill | what it does |
|---|---|
| `project-report` | turns `results/*.json` into a status report (script: `summarize.py`) |
| `invoice-check` | checks invoice fields, totals and dates; masks the IBAN (script: `validate_invoice.py`) |
| `meeting-notes` | decisions, action items with owner and due date, open questions |

Plus a small toolkit (`skills_kit.py`) that validates the skills, measures their context cost and tests activation.

## Results (`results/results.json`)
- Validation problems: none
- Context: {always} tokens always loaded vs {all} if every skill body were in the prompt (progressive disclosure)
- Activation test (keyword proxy): {correct}/{total}

## Use the skills
Copy a skill folder to `~/.claude/skills/` (personal) or `<repo>/.claude/skills/` (project) for Claude Code, then ask
for something its description covers.

## Run the checks
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```

## Licence
MIT
````

## 22. صیقل نهایی repo
_GitHub · حدود 5 دقیقه_

**چرا:** جزئیات کوچکی که repo را حرفه‌ای نشان می‌دهد.

1. صفحه‌ی repo → چرخ‌دنده‌ی **About** → Topics: `agent-skills`, `claude-code`, `llm-agents`, `prompt-engineering`, `python`.
2. در پروفایل GitHub: **Customize your pins** → این repo را pin کن.
3. خط رزومه‌ی پایین را با عددهای خودت بردار.

**خط رزومه:** Packaged team procedures as Agent Skills (SKILL.md with scripts and references) and built a toolkit that validates skills, measures context cost ({always} vs {all} tokens with progressive disclosure) and tests activation ({correct}/{total} on labelled requests).

## اگر به خطا خوردی
- **`No module named yaml`**: `pip install -r requirements.txt` را در venv فعال اجرا کن.
- **Claude Code skill را نمی‌بیند**: پوشه باید `.claude/skills/<name>/SKILL.md` باشد و Claude Code را از ریشه‌ی repo باز کرده باشی.
- **`python` شناخته نمی‌شود**: Python را با تیک «Add to PATH» نصب کن، یا به‌جای `python` بنویس `py`.
- **تب Actions قرمز است**: روی اجرای قرمز کلیک کن؛ معمولاً یک فایل با نام یا مسیر اشتباه ساخته شده (مثلاً `test/` به‌جای `tests/`).

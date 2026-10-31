# ساختن پرسش‌وپاسخ روی اسناد شرکت با ارجاع، از صفر در GitHub

دستیاری می‌سازی که سؤال‌های کارمندان را از روی سندهای داخلی (چند قالب فایل) جواب می‌دهد، به بخش درست سند ارجاع می‌دهد، هر عدد جواب را با سند چک می‌کند و وقتی سند چیزی نمی‌گوید امتناع می‌کند. بدون GPU و بدون مدل؛ مدل واقعی اختیاری است. بهتر است اول p01 را ساخته باشی.

> نسخه‌ی تعاملی (تیک مراحل، مقایسه‌ی خروجی، پرسیدن از Claude، دانلود notebook): صفحه‌ی «راهنمای ساخت پروژه‌ها» (claude.ai artifact).

**برای فهمیدن بهتر:** پروژه در نقشه‌ی راه (نقشه‌ی راه، پروژه‌ی `p03_document_qa`) · [جواب با ارجاع و امتناع: درس p01 گام ۵](../../lessons/p01_faq_search/README.md) · [نسخه‌ی پیشرفته: Agentic RAG](../p22_agentic_rag/GUIDE.md)

## مراحل
1. ساختن repo در GitHub
2. فایل .gitignore
3. فایل requirements.txt
4. سندها: docs/employee_handbook.md
5. سند HTML: docs/it_security.html
6. سند متنی: docs/travel_policy.txt
7. سند: docs/expenses.md
8. سؤال‌ها: docs/questions.json
9. فایل اصلی: doc_qa.py
10. فایل check_setup.py
11. تست‌ها: tests/test_doc_qa.py
12. تست خودکار در GitHub (Actions)
13. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
14. ساختن و اجرای notebook
15. اجرا با مدل زبانی واقعی (اختیاری)
16. commit و push از VS Code
17. README نهایی
18. صیقل نهایی repo

## 1. ساختن repo در GitHub
_GitHub · حدود 3 دقیقه_

**چرا:** repo خودت نمونه‌کار توست: هر فایلی که اینجا می‌سازی، کارفرما می‌بیند. اسم و توضیح کوتاه و دقیق، اولین چیزی است که دیده می‌شود.

1. در github.com بالا سمت راست **+** → **New repository**.
2. **Repository name:** `document_qa`
3. **Description:** `Q&A over company documents (markdown, text, HTML, optional PDF/Word): heading-aware chunking, BM25, cited answers, number grounding and abstention`
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

**چرا:** هسته فقط کتابخانه‌ی استاندارد پایتون است (خواندن HTML هم با `html.parser` داخلی). `pypdf` و `python-docx` برای PDF و Word اختیاری‌اند؛ اگر سند PDF داری از حالت `#` درشان بیاور.

1. **Add file → Create new file**، نام `requirements.txt`. commit: `Add requirements`.

`requirements.txt`

````
# core: standard library only, plus tests and notebooks
pytest>=8.0
ipykernel>=6.29
# optional: PDF and Word files
# pypdf>=4.0
# python-docx>=1.1
# optional model providers
# ollama>=0.4
# anthropic>=0.40
````

## 4. سندها: docs/employee_handbook.md
_GitHub · حدود 2 دقیقه_

**چرا:** چهار سند داخلی در سه قالب: markdown، HTML و متن ساده. این واقعی‌تر از یک قالب است: در شرکت‌ها سندها همیشه قالب‌های مختلف دارند و هر کدام باید به یک شکل یکسان (متن با عنوان) تبدیل شود.

1. **Add file → Create new file**، در کادر نام بنویس `docs/employee_handbook.md` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add employee handbook`.

`docs/employee_handbook.md`

````
# Employee Handbook

## Vacation
Full-time employees get 25 days of paid vacation per calendar year. Up to 5 unused days can be carried over to the next year; they expire on 31 March.

## Sick leave
Tell your manager before 10:00 on the first day of illness. From the fourth day of illness a doctor's certificate is required.

## Remote work
You may work remotely up to 2 days per week after your probation period. Remote work from another country needs written approval from HR and is limited to 20 days per year.

## Probation
The probation period is 6 months. During probation the notice period is 2 weeks.
````

## 5. سند HTML: docs/it_security.html
_GitHub · حدود 2 دقیقه_

**چرا:** یک صفحه‌ی intranet. عنوان‌های `<h1>` و `<h2>` به `#` و `##` تبدیل می‌شوند تا ساختار بخش‌ها حفظ شود.

1. **Add file → Create new file**، در کادر نام بنویس `docs/it_security.html` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add IT security policy (HTML)`.

`docs/it_security.html`

````
<html><head><title>IT Security Policy</title></head><body>
<h1>IT Security Policy</h1>
<h2>Passwords</h2>
<p>Passwords must have at least 12 characters. Never reuse a work password on another website. Use the company password manager.</p>
<h2>Multi-factor authentication</h2>
<p>Multi-factor authentication (MFA) is mandatory for email, VPN and the HR portal. Use the authenticator app; SMS codes are not allowed.</p>
<h2>Phishing</h2>
<p>Report suspicious emails with the "Report phishing" button. Do not forward them to colleagues. The security team answers within 4 working hours.</p>
<h2>Laptops</h2>
<p>Laptops are replaced every 3 years. A lost or stolen laptop must be reported to the IT service desk within 24 hours.</p>
</body></html>
````

## 6. سند متنی: docs/travel_policy.txt
_GitHub · حدود 2 دقیقه_

**چرا:** متن ساده بدون علامت‌گذاری؛ کد خط‌های کوتاهی را که متن بعدشان می‌آید عنوان در نظر می‌گیرد.

1. **Add file → Create new file**، در کادر نام بنویس `docs/travel_policy.txt` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add travel policy (plain text)`.

`docs/travel_policy.txt`

````
TRAVEL POLICY

Flights
Book economy class for flights shorter than 6 hours. Business class is allowed for flights of 6 hours or more with approval from your director.

Hotels
The hotel limit is 140 EUR per night in most cities and 190 EUR per night in London, Paris and New York. Book through the travel portal.

Meals
The meal allowance (per diem) is 45 EUR per full day of travel and 25 EUR for a half day.
````

## 7. سند: docs/expenses.md
_GitHub · حدود 2 دقیقه_

**چرا:** سند چهارم: هزینه‌ها و بازپرداخت، با عددهایی که نگهبان عدد باید چک کند.

1. **Add file → Create new file**، در کادر نام بنویس `docs/expenses.md` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add expenses policy`.

`docs/expenses.md`

````
# Expenses

## Deadline
Submit expenses within 30 days after the purchase or the end of the trip. Late claims need approval from your manager.

## Receipts
Upload a receipt for every expense above 25 EUR. Photos are fine if the amount, date and seller are readable.

## Reimbursement
Approved expenses are paid with the next salary. Claims approved after the 20th of the month are paid one month later.
````

## 8. سؤال‌ها: docs/questions.json
_GitHub · حدود 2 دقیقه_

**چرا:** ۱۸ سؤال کارمند با سند درست هر کدام؛ ۳ سؤال عمداً درباره‌ی چیزی است که در سندها نیست (مرخصی والدین، سگ در دفتر، سهام). سیستم باید آن‌ها را امتناع کند.

1. **Add file → Create new file**، در کادر نام بنویس `docs/questions.json` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add labelled questions`.

`docs/questions.json`

````json
[
 {
  "question": "how many vacation days do I get",
  "source": "employee_handbook",
  "answerable": "yes"
 },
 {
  "question": "can I carry over unused vacation days",
  "source": "employee_handbook",
  "answerable": "yes"
 },
 {
  "question": "when do I need a doctor's certificate",
  "source": "employee_handbook",
  "answerable": "yes"
 },
 {
  "question": "how many days a week can I work from home",
  "source": "employee_handbook",
  "answerable": "yes"
 },
 {
  "question": "how long is the probation period",
  "source": "employee_handbook",
  "answerable": "yes"
 },
 {
  "question": "how long must my password be",
  "source": "it_security",
  "answerable": "yes"
 },
 {
  "question": "are SMS codes allowed for MFA",
  "source": "it_security",
  "answerable": "yes"
 },
 {
  "question": "what do I do with a phishing email",
  "source": "it_security",
  "answerable": "yes"
 },
 {
  "question": "how often are laptops replaced",
  "source": "it_security",
  "answerable": "yes"
 },
 {
  "question": "can I fly business class",
  "source": "travel_policy",
  "answerable": "yes"
 },
 {
  "question": "what is the hotel limit in Paris",
  "source": "travel_policy",
  "answerable": "yes"
 },
 {
  "question": "how much is the meal allowance per day",
  "source": "travel_policy",
  "answerable": "yes"
 },
 {
  "question": "when do I have to submit expenses",
  "source": "expenses",
  "answerable": "yes"
 },
 {
  "question": "do I need a receipt for a 10 EUR taxi",
  "source": "expenses",
  "answerable": "yes"
 },
 {
  "question": "when are approved expenses paid",
  "source": "expenses",
  "answerable": "yes"
 },
 {
  "question": "what is the company's parental leave policy",
  "source": "",
  "answerable": "no"
 },
 {
  "question": "can I bring my dog to the office",
  "source": "",
  "answerable": "no"
 },
 {
  "question": "what is the stock option vesting schedule",
  "source": "",
  "answerable": "no"
 }
]
````

## 9. فایل اصلی: doc_qa.py
_GitHub · حدود 5 دقیقه_

**چرا:** همه‌ی منطق در یک فایل: خواندن قالب‌های مختلف، تکه‌کردن با حفظ عنوان و پنجره‌ی هم‌پوشان برای بخش‌های بلند، BM25، بررسی کافی بودن شاهد، جواب با ارجاع، و دو نگهبان در کد: ارجاع باید واقعی باشد و هر عدد جواب باید در متن ارجاع‌شده باشد.

1. **Add file → Create new file**، در کادر نام بنویس `doc_qa.py`. commit: `Add document Q&A: loaders, chunking, BM25, cited answers, number grounding`.

`doc_qa.py`

````python
"""Question answering over company documents (markdown, text, HTML; PDF and Word optional) with citations.

load -> chunk (by heading, long sections split into overlapping windows) -> retrieve (BM25) -> check there is enough
evidence -> answer with citations -> check every number in the answer appears in the cited text -> otherwise abstain."""
import json
import math
import os
import re
import shutil
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "me", "to", "of", "and", "or", "in", "on", "for", "can",
        "how", "what", "when", "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that", "much", "many", "need",
        "have", "long", "must", "get", "per"}


# ---------- loading ----------

class _HTMLText(HTMLParser):
    """HTML -> markdown-like text: <h1>/<h2> become '#' / '##' headings, paragraphs become lines."""

    def __init__(self):
        super().__init__()
        self.lines, self.prefix, self.skip = [], "", False

    def handle_starttag(self, tag, attrs):
        self.prefix = {"h1": "# ", "h2": "## ", "h3": "## "}.get(tag, "")
        self.skip = tag in ("script", "style", "title")

    def handle_endtag(self, tag):
        self.skip = False

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.lines.append(self.prefix + " ".join(data.split()))
            self.prefix = ""


def text_headings(raw):
    """Plain text: a short line followed by text is treated as a heading; an ALL-CAPS first line is the title."""
    lines, out = raw.splitlines(), []
    for i, line in enumerate(lines):
        s = line.strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if s and s.isupper() and not out:
            out.append("# " + s.title())
        elif s and len(s.split()) <= 4 and nxt and not s.endswith("."):
            out.append("## " + s)
        else:
            out.append(line)
    return "\n".join(out)


def load_documents(folder="docs"):
    docs = {}
    for p in sorted(Path(folder).iterdir()):
        if p.suffix == ".md":
            text = p.read_text(encoding="utf-8")
        elif p.suffix == ".txt":
            text = text_headings(p.read_text(encoding="utf-8"))
        elif p.suffix in (".html", ".htm"):
            parser = _HTMLText()
            parser.feed(p.read_text(encoding="utf-8"))
            text = "\n".join(parser.lines)
        elif p.suffix == ".pdf":
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(p).pages)
        elif p.suffix == ".docx":
            import docx
            text = "\n".join(par.text for par in docx.Document(p).paragraphs)
        else:
            continue
        docs[p.stem] = text
    return docs


def load_questions(path="docs/questions.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------- chunking ----------

def chunk(text, doc_id, max_words=80, overlap=20):
    """One chunk per section; a section longer than max_words becomes overlapping windows. The heading path stays."""
    sections, title, heading, buf = [], "", "", []
    for line in text.splitlines() + ["# "]:
        if line.startswith("#"):
            body = " ".join(" ".join(buf).split())
            if body:
                sections.append((" > ".join(x for x in (title, heading) if x), body))
            buf = []
            if line.startswith("## "):
                heading = line[3:].strip()
            else:
                title, heading = line[2:].strip(), ""
        else:
            buf.append(line)
    chunks = []
    for head, body in sections:
        words = body.split()
        step = max(max_words - overlap, 1)
        for start in range(0, max(len(words) - overlap, 1), step):
            chunks.append({"id": f"{doc_id}#{len(chunks)}", "doc_id": doc_id, "heading": head,
                           "text": " ".join(words[start:start + max_words])})
    return chunks


def chunk_all(docs, **kw):
    return [c for d, t in docs.items() for c in chunk(t, d, **kw)]


# ---------- retrieval ----------

def tokenize(text):
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class BM25:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.chunks = chunks
        toks = [tokenize(c["heading"] + " " + c["text"]) for c in chunks]
        self.tf, self.len = [Counter(t) for t in toks], [len(t) for t in toks]
        self.n, self.avg = len(toks), sum(map(len, toks)) / len(toks)
        self.df = Counter(w for t in toks for w in set(t))
        self.k1, self.b = k1, b

    def search(self, query, k=3):
        s = [0.0] * self.n
        for w in tokenize(query):
            df = self.df.get(w, 0)
            if not df:
                continue
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            for i, tf in enumerate(t.get(w, 0) for t in self.tf):
                if tf:
                    s[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        order = sorted(range(self.n), key=lambda i: (-s[i], i))
        return [self.chunks[i] for i in order if s[i] > 0][:k]


def enough_evidence(question, chunk, min_ratio=0.5):
    """At least half of the question's content words appear in the chunk (heading included)."""
    q = set(tokenize(question))
    return bool(q) and len(q & set(tokenize(chunk["heading"] + " " + chunk["text"]))) / len(q) >= min_ratio


# ---------- answering ----------

def numbers_grounded(answer, chunks):
    """Every number in the answer must appear in the cited text (a wrong number is the costliest mistake)."""
    source = " ".join(c["text"] for c in chunks)
    return all(n in source for n in re.findall(r"\d+(?:[.,]\d+)?", re.sub(r"\[[^\]]*\]", " ", answer)))


def offline_llm(question, chunks):
    """No model: the sentence of the evidence that shares the most words with the question, cited."""
    q = set(tokenize(question))
    best = max(((c, s) for c in chunks for s in re.split(r"(?<=[.!?])\s+", c["text"])), key=lambda cs: len(q & set(tokenize(cs[1]))))
    return f"{best[1]} [{best[0]['id']}]"


def make_llm(provider=None, model=None):
    """(question, chunks) -> answer text. provider: offline (default) | ollama | anthropic | opencode (DOCQA_PROVIDER)."""
    provider = provider or os.environ.get("DOCQA_PROVIDER", "offline")
    if provider == "offline":
        return offline_llm

    def prompt(question, chunks):
        src = "\n".join(f"[{c['id']}] {c['heading']}: {c['text']}" for c in chunks)
        return (f"Answer ONLY from these company documents and cite each claim like [expenses#0]. If they do not contain the "
                f"answer, say you do not know.\n\n{src}\n\nQuestion: {question}")
    if provider == "ollama":
        import ollama
        model = model or "qwen2.5:7b"
        return lambda q, cs: ollama.chat(model=model, messages=[{"role": "user", "content": prompt(q, cs)}],
                                         options={"temperature": 0})["message"]["content"]
    if provider == "anthropic":
        import anthropic
        client, model = anthropic.Anthropic(), model or "claude-sonnet-5-5"
        return lambda q, cs: "".join(b.text for b in client.messages.create(
            model=model, max_tokens=400, messages=[{"role": "user", "content": prompt(q, cs)}]).content if b.type == "text")
    if provider == "opencode":
        if not shutil.which("opencode"):
            raise RuntimeError("opencode is not installed (https://opencode.ai)")
        model = model or "anthropic/claude-sonnet-5-5"
        return lambda q, cs: subprocess.run(["opencode", "run", "-m", model, prompt(q, cs)], capture_output=True, text=True,
                                            encoding="utf-8", timeout=300).stdout.strip()
    raise ValueError(f"unknown provider {provider!r}")


def answer(question, index, llm=offline_llm, k=3):
    """Retrieve, require evidence, answer with citations, check citations and numbers; otherwise abstain."""
    hits = [c for c in index.search(question, k) if enough_evidence(question, c)]
    if not hits:
        return {"answer": None, "citations": [], "abstained": True, "reason": "no evidence"}
    text = llm(question, hits)
    ids = {c["id"] for c in hits}
    cites = list(dict.fromkeys(c for c in re.findall(r"\[([^\]]+)\]", text) if c in ids))
    if not cites:
        return {"answer": None, "citations": [], "abstained": True, "reason": "no valid citation"}
    if not numbers_grounded(text, [c for c in hits if c["id"] in cites]):
        return {"answer": None, "citations": [], "abstained": True, "reason": "number not in the source"}
    return {"answer": text, "citations": cites, "abstained": False, "reason": ""}


def evaluate(questions, index, llm=offline_llm):
    """Answerable: answered with a citation from the right document. Unanswerable: abstained."""
    r = {"correct_source": 0, "wrong_source": 0, "abstained_wrongly": 0, "abstained_correctly": 0, "answered_unanswerable": 0}
    for q in questions:
        out = answer(q["question"], index, llm)
        if q["answerable"] == "no":
            r["abstained_correctly" if out["abstained"] else "answered_unanswerable"] += 1
        elif out["abstained"]:
            r["abstained_wrongly"] += 1
        else:
            r["correct_source" if any(c.split("#")[0] == q["source"] for c in out["citations"]) else "wrong_source"] += 1
    return r
````

مدل با متغیر محیطی `DOCQA_PROVIDER` انتخاب می‌شود: `offline` (پیش‌فرض)، `ollama`، `anthropic` یا `opencode`.

<details><summary><b>درک کد: تابع به تابع</b></summary>

- **`_HTMLText و text_headings`**: هر قالب به متن با عنوان `#`/`##` تبدیل می‌شود تا تکه‌کردن برای همه یکسان باشد.
- **`load_documents`**: md، txt و html با کتابخانه‌ی استاندارد؛ pdf و docx فقط اگر بسته‌اش نصب باشد.
- **`chunk`**: یک تکه برای هر بخش؛ بخش بلند به پنجره‌های ۸۰ کلمه‌ای با ۲۰ کلمه هم‌پوشانی، تا جمله‌ای که مرز را رد می‌کند گم نشود. ([درس](../../lessons/p01_faq_search/step01_chunk_markdown/lesson.md))
- **`BM25 و enough_evidence`**: BM25 با ریشه‌یابی ساده؛ بعد شرط شاهد: نصف کلمه‌های سؤال باید در تکه باشد، وگرنه امتناع. ([درس](../../lessons/p22_agentic_rag/step02_grader/lesson.md))
- **`numbers_grounded`**: هر عدد جواب باید در متن ارجاع‌شده باشد. عدد اشتباه پرهزینه‌ترین خطای این نوع سیستم است.
- **`answer و evaluate`**: جست‌وجو، شاهد، جواب، ارجاع واقعی، عدد درست؛ اگر هر کدام نشد امتناع با دلیل. evaluate منبع درست و امتناع درست را می‌شمارد. ([درس](../../lessons/p01_faq_search/step05_answer_citations/lesson.md))

</details>

## 10. فایل check_setup.py
_GitHub · حدود 2 دقیقه_

**چرا:** یک بررسی کوچک که بعد از نصب روی لپ‌تاپ اجرا می‌کنی تا مطمئن شوی پایتون، داده و توابع اصلی کار می‌کنند، قبل از notebook.

1. **Add file → Create new file**، نام `check_setup.py`. commit: `Add setup check`.

`check_setup.py`

````python
"""Run once after installing: checks Python, the documents in all formats and one answer."""
import sys

from doc_qa import BM25, answer, chunk_all, load_documents

print("Python", sys.version.split()[0])
docs = load_documents()
for name, text in docs.items():
    print(f"{name:18s} {len(text.split()):4d} words, first line: {text.splitlines()[0]}")
index = BM25(chunk_all(docs))
print(answer("how long must my password be", index)["answer"])
print("setup ok")
````

## 11. تست‌ها: tests/test_doc_qa.py
_GitHub · حدود 3 دقیقه_

**چرا:** تست‌ها چک می‌کنند هر سه قالب با عنوان خوانده شوند، پنجره‌ها هم‌پوشان باشند، عدد ساختگی و ارجاع ساختگی رد شوند، و روی مجموعه‌ی سؤال‌ها هیچ سؤال بی‌جوابی جواب نگیرد.

1. **Add file → Create new file**، نام `tests/test_doc_qa.py`. commit: `Add tests`.

`tests/test_doc_qa.py`

````python
from doc_qa import BM25, answer, chunk, chunk_all, enough_evidence, evaluate, load_documents, load_questions, numbers_grounded


def test_all_formats_load_with_headings():
    docs = load_documents()
    assert set(docs) == {"employee_handbook", "it_security", "travel_policy", "expenses"}
    assert docs["it_security"].startswith("# IT Security Policy") and "## Passwords" in docs["it_security"]
    assert docs["travel_policy"].startswith("# Travel Policy") and "## Hotels" in docs["travel_policy"]


def test_long_sections_become_overlapping_windows():
    text = "# T\n## S\n" + " ".join(f"w{i}" for i in range(200))
    cs = chunk(text, "d", max_words=80, overlap=20)
    assert len(cs) == 3 and cs[0]["text"].split()[-20:] == cs[1]["text"].split()[:20] and cs[0]["heading"] == "T > S"


def test_numbers_must_come_from_the_source():
    src = [{"id": "e#0", "text": "Submit expenses within 30 days."}]
    assert numbers_grounded("Within 30 days [e#0]", src) and not numbers_grounded("Within 60 days [e#0]", src)


def test_wrong_number_and_fake_citation_are_rejected():
    index = BM25(chunk_all(load_documents()))
    assert answer("when do I have to submit expenses", index, lambda q, cs: f"Within 60 days [{cs[0]['id']}]")["reason"] == "number not in the source"
    assert answer("when do I have to submit expenses", index, lambda q, cs: "Within 30 days [policy#9]")["reason"] == "no valid citation"


def test_evaluation_on_the_question_set():
    r = evaluate(load_questions(), BM25(chunk_all(load_documents())))
    assert r["answered_unanswerable"] == 0 and r["correct_source"] >= 13
    assert not enough_evidence("what is the CEO's phone number", {"heading": "Probation", "text": "The probation period is 6 months."})
````

## 12. تست خودکار در GitHub (Actions)
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

## 13. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
_VS Code · حدود 8 دقیقه_

**چرا:** محیط مجازی (venv) یک پایتون جدا فقط برای این پروژه است تا بسته‌هایش با پروژه‌های دیگر قاطی نشوند.

پیش‌نیاز: Git (از git-scm.com) و Python 3.10 یا جدیدتر، و در VS Code افزونه‌های **Python** و **Jupyter** از Microsoft.

1. VS Code: `Ctrl+Shift+P` → **Git: Clone** → آدرس `https://github.com/<نام-کاربری-تو>/document_qa.git` → یک پوشه انتخاب کن → **Open**.
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
employee_handbook   110 words, first line: # Employee Handbook
expenses             70 words, first line: # Expenses
it_security          98 words, first line: # IT Security Policy
travel_policy        81 words, first line: # Travel Policy
Passwords must have at least 12 characters. [it_security#0]
setup ok

.....                                                                    [100%]
5 passed
```

> **حواست باشد:** اگر PowerShell گفت running scripts is disabled: یک بار `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` و دوباره فعال کن. روی Mac/Linux به‌جای خط دوم: `source .venv/bin/activate`.

## 14. ساختن و اجرای notebook
_VS Code · حدود 15 دقیقه_

**چرا:** notebook داستان پروژه است: قالب‌های مختلف، تکه‌ها، جواب‌ها با ارجاع، نمایش دو نگهبان (عدد اشتباه و ارجاع ساختگی) و ارزیابی.

1. VS Code: `Ctrl+Shift+P` → **Create: New Jupyter Notebook** → `Ctrl+S` با نام `01_document_qa.ipynb` در پوشه‌ی repo.
2. بالا سمت راست **Select Kernel → Python Environments → .venv**.
3. سلول‌ها را به ترتیب زیر بساز (متن: **+ Markdown**، کد: **+ Code**) و هر سلول کد را با `Shift+Enter` اجرا کن. خروجی را با «باید ببینی» زیرش مقایسه کن.

_سلول متنی (Markdown):_

````markdown
# Question answering over company documents, with citations

Four internal documents in three formats (markdown, plain text, HTML; PDF and Word are optional) and 18 employee
questions: 15 answerable, 3 about things the documents do not cover. Every answer must cite its source, every number
in it must appear in the cited text, and without enough evidence the system abstains.
````

_سلول کد 1:_

```python
from doc_qa import BM25, answer, chunk_all, evaluate, load_documents, load_questions

docs = load_documents()
questions = load_questions()
for name, text in docs.items():
    print(f"{name:18s} {len(text.split()):4d} words | {text.splitlines()[0]}")
print(len(questions), "questions")
```

سه قالب فایل خوانده می‌شوند و هر کدام به متن با عنوان‌های `#` تبدیل می‌شود، تا تکه‌کردن برای همه یکسان باشد.

**باید ببینی:**

```
employee_handbook   110 words | # Employee Handbook
expenses             70 words | # Expenses
it_security          98 words | # IT Security Policy
travel_policy        81 words | # Travel Policy
18 questions
```

_سلول متنی (Markdown):_

````markdown
## Chunks keep their heading path
````

_سلول کد 2:_

```python
chunks = chunk_all(docs)
print(len(chunks), "chunks")
for c in chunks[:5]:
    print(f"{c['id']:20s} {c['heading']:32s} {c['text'][:50]}")
```

هر بخش یک تکه است و عنوان کامل کنارش می‌ماند. بخش‌های بلندتر از ۸۰ کلمه به پنجره‌های هم‌پوشان تقسیم می‌شوند (تست این را چک می‌کند).

**باید ببینی:**

```
14 chunks
employee_handbook#0  Employee Handbook > Vacation     Full-time employees get 25 days of paid vacation p
employee_handbook#1  Employee Handbook > Sick leave   Tell your manager before 10:00 on the first day of
employee_handbook#2  Employee Handbook > Remote work  You may work remotely up to 2 days per week after 
employee_handbook#3  Employee Handbook > Probation    The probation period is 6 months. During probation
expenses#0           Expenses > Deadline              Submit expenses within 30 days after the purchase
```

_سلول متنی (Markdown):_

````markdown
## Answers
````

_سلول کد 3:_

```python
index = BM25(chunks)
for q in questions:
    out = answer(q["question"], index)
    shown = f"ABSTAIN ({out['reason']})" if out["abstained"] else out["answer"][:70]
    print(f"{q['question'][:38]:38s} -> {shown}")
```

مدل پیش‌فرض offline جمله‌ی مرتبط را از سند برمی‌دارد و ارجاع می‌دهد. سه سؤال آخر شاهد ندارند و امتناع می‌شوند.

**باید ببینی:**

```
how many vacation days do I get        -> Full-time employees get 25 days of paid vacation per calendar year. [e
can I carry over unused vacation days  -> Up to 5 unused days can be carried over to the next year; they expire 
when do I need a doctor's certificate  -> From the fourth day of illness a doctor's certificate is required. [em
how many days a week can I work from h -> You may work remotely up to 2 days per week after your probation perio
how long is the probation period       -> The probation period is 6 months. [employee_handbook#3]
how long must my password be           -> Passwords must have at least 12 characters. [it_security#0]
are SMS codes allowed for MFA          -> Use the authenticator app; SMS codes are not allowed. [it_security#1]
what do I do with a phishing email     -> Report suspicious emails with the "Report phishing" button. [it_securi
how often are laptops replaced         -> Laptops are replaced every 3 years. [it_security#3]
can I fly business class               -> Business class is allowed for flights of 6 hours or more with approval
what is the hotel limit in Paris       -> The hotel limit is 140 EUR per night in most cities and 190 EUR per ni
how much is the meal allowance per day -> The meal allowance (per diem) is 45 EUR per full day of travel and 25 
when do I have to submit expenses      -> Submit expenses within 30 days after the purchase or the end of the tr
do I need a receipt for a 10 EUR taxi  -> Upload a receipt for every expense above 25 EUR. [expenses#1]
when are approved expenses paid        -> Approved expenses are paid with the next salary. [expenses#2]
what is the company's parental leave p -> ABSTAIN (no evidence)
can I bring my dog to the office       -> ABSTAIN (no evidence)
what is the stock option vesting sched -> ABSTAIN (no evidence)
```

_سلول متنی (Markdown):_

````markdown
## Guards against wrong answers
Two answers a model could plausibly give: a wrong number with a real citation, and a right number with an invented citation.
````

_سلول کد 4:_

```python
q = "when do I have to submit expenses"
wrong_number = lambda question, cs: f"Within 60 days [{cs[0]['id']}]"
fake_citation = lambda question, cs: "Within 30 days [policy#9]"
print("wrong number  ->", answer(q, index, wrong_number)["reason"])
print("fake citation ->", answer(q, index, fake_citation)["reason"])
```

دفاع در کد است، نه در prompt: عدد ۶۰ در سند نیست، پس جواب رد می‌شود؛ ارجاع ساختگی هم رد می‌شود.

**باید ببینی:**

```
wrong number  -> number not in the source
fake citation -> no valid citation
```

_سلول متنی (Markdown):_

````markdown
## Evaluation
````

_سلول کد 5:_

```python
import json, os

result = evaluate(questions, index)
print(result)
os.makedirs("results", exist_ok=True)
with open("results/results.json", "w") as f:
    json.dump({"offline": result}, f, indent=2)
```

روی این مجموعه‌ی کوچک همه درست است؛ این یعنی مجموعه کوچک و تمیز است، نه اینکه سیستم بی‌نقص است. با سؤال‌های واقعی همکاران و سندهای بلندتر امتحان کن.

**باید ببینی:**

```
{'correct_source': 15, 'wrong_source': 0, 'abstained_wrongly': 0, 'abstained_correctly': 3, 'answered_unanswerable': 0}
```

_سلول متنی (Markdown):_

````markdown
## With a real model (optional)
Set `DOCQA_PROVIDER` to `ollama`, `anthropic` or `opencode` before starting the notebook. The same guards apply.
````

_سلول کد 6:_

```python
import os
from doc_qa import make_llm

if os.environ.get("DOCQA_PROVIDER", "offline") != "offline":
    result_llm = evaluate(questions, index, make_llm())
    print(result_llm)
    with open("results/results.json", "w") as f:
        json.dump({"offline": result, os.environ["DOCQA_PROVIDER"]: result_llm}, f, indent=2)
else:
    print("No model set: DOCQA_PROVIDER = ollama | anthropic | opencode (see the guide)")
```

با مدل واقعی جواب‌ها روان‌تر می‌شوند؛ ببین چند بار نگهبان‌ها (عدد و ارجاع) جواب مدل را رد می‌کنند.

**باید ببینی:**

```
No model set: DOCQA_PROVIDER = ollama | anthropic | opencode (see the guide)
```

> **نکته:** اگر نمی‌خواهی سلول‌ها را یکی‌یکی بسازی: دکمه‌ی **دانلود notebook** بالای سلول‌ها فایل آماده را می‌دهد؛ در پوشه‌ی repo بگذار و Run All. ولی یک بار دستی ساختن، کد را بهتر در ذهنت می‌نشاند.

## 15. اجرا با مدل زبانی واقعی (اختیاری)
_VS Code · Ollama / Claude / OpenCode · حدود 10 دقیقه_

**چرا:** مدل offline جمله را از سند برمی‌دارد. با مدل واقعی جواب روان‌تر است، ولی همان دو نگهبان باید جواب مدل را چک کنند؛ ببین چند بار جواب مدل رد می‌شود.

1. یکی از سه راه را در ترمینال VS Code اجرا کن، بعد kernel را **Restart** و سلول «With a real model» را اجرا کن.

_Ollama (محلی، رایگان) · از ollama.com نصب کن_

```
ollama pull qwen2.5:7b
pip install ollama
$env:DOCQA_PROVIDER = "ollama"
```

_Claude (کلید API از console.anthropic.com؛ اشتراک Claude.ai کلید API نیست)_

```
pip install anthropic
$env:ANTHROPIC_API_KEY = "sk-ant-..."     # فقط در ترمینال
$env:DOCQA_PROVIDER = "anthropic"
```

_OpenCode_

```
opencode models
$env:DOCQA_PROVIDER = "opencode"
```

> **حواست باشد:** کلید API را هرگز در notebook یا فایل‌های repo ننویس. سندهای واقعی شرکت را به مدل ابری نفرست مگر اجازه داشته باشی؛ برای سند محرمانه Ollama محلی را انتخاب کن.

## 16. commit و push از VS Code
_VS Code · GitHub · حدود 3 دقیقه_

**چرا:** notebook با خروجی‌هایش و فایل نتایج باید در GitHub باشند تا بدون اجرا دیده شوند.

1. پنل Source Control: `Ctrl+Shift+G`. فایل‌های `01_document_qa.ipynb` و `results/results.json` را می‌بینی.
2. پیام: `Add notebook: document Q&A with citations and guards` → **Commit** → **Sync Changes**.

> **باید ببینی:** در GitHub، `01_document_qa.ipynb` را باز کن: جدول‌ها و خروجی‌ها بدون اجرا دیده می‌شوند. تب Actions دوباره سبز است.

> **حواست باشد:** قانون ساده: قبل از هر کار در VS Code اول **Pull** بزن، و یک فایل را هم‌زمان در GitHub و VS Code ویرایش نکن.

## 17. README نهایی
_GitHub · حدود 10 دقیقه_

**چرا:** README صفحه‌ی اول پروژه است: در ۳۰ ثانیه بگوید چه مسئله‌ای، چه روشی، چه عددی و چه محدودیتی. عددها را از `results/results.json` خودت بردار، نه از این صفحه.

1. در GitHub روی `README.md` → آیکون مداد → متن زیر را جایگزین کن و عددهای `{...}` را پر کن (یا results.json را پایین paste کن). commit: `Write README`.
2. نام کاربری‌ات را در خط badge جایگزین کن.

````markdown
# Company document Q&A with citations

![tests](https://github.com/<your-user>/document_qa/actions/workflows/tests.yml/badge.svg)

Employees ask questions about internal policies (markdown, text, HTML; PDF and Word optional). Answers cite their
source section; every number in an answer must appear in the cited text; without enough evidence the system abstains.

## Results (`results/results.json`, 18 questions: 15 answerable, 3 not covered by the documents)
| | right source | wrong source | wrong abstentions | right abstentions | answered unanswerable |
|---|---|---|---|---|---|
| offline (extractive) | {correct} | {wrong} | {wrong_abstain} | {right_abstain} | {unanswerable} |

## How it works
load (md / txt / html / pdf / docx) → chunk by heading, long sections as overlapping windows → BM25 → evidence check
(half of the question's content words) → answer with citations (offline extractive, Ollama, Claude or OpenCode) →
citation and number checks → abstain if any check fails.

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_document_qa.ipynb` and run all cells. Optional model: `DOCQA_PROVIDER=ollama|anthropic|opencode`.

## Limitations
- Four short documents and 18 questions: the perfect score says the set is small, not that the system is.
- Word-overlap evidence check; tables and scanned PDFs need OCR / table extraction.

## Licence
MIT
````

## 18. صیقل نهایی repo
_GitHub · حدود 5 دقیقه_

**چرا:** جزئیات کوچکی که repo را حرفه‌ای نشان می‌دهد.

1. صفحه‌ی repo → چرخ‌دنده‌ی **About** → Topics: `rag`, `document-qa`, `retrieval`, `llm`, `python`.
2. در پروفایل GitHub: **Customize your pins** → این repo را pin کن.
3. خط رزومه‌ی پایین را با عددهای خودت بردار.

**خط رزومه:** Built a document Q&A assistant over multi-format company policies (md/txt/html, optional pdf/docx) with heading-aware chunking, BM25, cited answers and code-level guards (citation and number grounding); {correct}/15 answerable questions answered from the right source and {right_abstain}/3 out-of-scope questions abstained.

## اگر به خطا خوردی
- **`No module named doc_qa` در notebook**: notebook باید کنار `doc_qa.py` باشد و kernel روی `.venv`.
- **`FileNotFoundError: docs`**: سندها را در پوشه‌ی `docs/` ساخته‌ای؟ notebook را از پوشه‌ی repo اجرا کن.
- **سند PDF من خوانده نمی‌شود**: `pip install pypdf`؛ PDF اسکن‌شده متن ندارد و OCR لازم دارد.
- **`python` شناخته نمی‌شود**: Python را با تیک «Add to PATH» نصب کن، یا به‌جای `python` بنویس `py`.
- **تب Actions قرمز است**: روی اجرای قرمز کلیک کن؛ معمولاً یک فایل با نام یا مسیر اشتباه ساخته شده (مثلاً `test/` به‌جای `tests/`).

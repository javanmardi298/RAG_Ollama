# ساختن Agentic RAG (جواب با شاهد یا «نمی‌دانم»)، از صفر در GitHub

عاملی می‌سازی که اگر شاهد کافی پیدا نکند دوباره جست‌وجو می‌کند و اگر باز هم نبود می‌گوید «نمی‌دانم»، و آن را با RAG ساده با عدد مقایسه می‌کنی. بدون GPU و بدون مدل اجرا می‌شود؛ نسخه‌ی مدلی (Ollama، Claude یا OpenCode) در مرحله‌ی ۱۱ اختیاری است. بهتر است اول پروژه‌ی جست‌وجوی FAQ (p01) را ساخته باشی.

> نسخه‌ی تعاملی (تیک مراحل، مقایسه‌ی خروجی، پرسیدن از Claude، دانلود notebook): صفحه‌ی «راهنمای ساخت پروژه‌ها» (claude.ai artifact).

**برای فهمیدن بهتر:** [درس قدم‌به‌قدم Agentic RAG (۵ گام)](../../lessons/p22_agentic_rag/README.md) · پروژه در نقشه‌ی راه (نقشه‌ی راه، پروژه‌ی `p22_agentic_rag`) · [پژوهش ۲۰۲۶: Agentic RAG چه چیزی تثبیت شده](../../docs/research_2026.md)

## مراحل
1. ساختن repo در GitHub
2. فایل .gitignore
3. فایل requirements.txt
4. فایل داده: data/faq.json
5. فایل اصلی: agentic_rag.py
6. فایل check_setup.py
7. تست‌ها: tests/test_agentic_rag.py
8. تست خودکار در GitHub (Actions)
9. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
10. ساختن و اجرای notebook
11. اجرا با مدل زبانی واقعی (اختیاری)
12. commit و push از VS Code
13. README نهایی
14. صیقل نهایی repo

## 1. ساختن repo در GitHub
_GitHub · حدود 3 دقیقه_

**چرا:** repo خودت نمونه‌کار توست: هر فایلی که اینجا می‌سازی، کارفرما می‌بیند. اسم و توضیح کوتاه و دقیق، اولین چیزی است که دیده می‌شود.

1. در github.com بالا سمت راست **+** → **New repository**.
2. **Repository name:** `agentic_rag`
3. **Description:** `Agentic RAG on FAQ pages: routing, evidence grading, bounded query rewriting, answer verification and abstention, rule-based and LLM-based (Ollama / Claude / OpenCode)`
4. **Public** را انتخاب کن (برای نمونه‌کار و برای اینکه Actions رایگان باشد).
5. تیک **Add a README file** را بزن. **Add .gitignore:** None (خودمان می‌سازیم). **Choose a license:** MIT License.
6. **Create repository**.

> **باید ببینی:** repo دو فایل دارد: `README.md` و `LICENSE`. در LICENSE اگر نام تو در خط Copyright نیست، با آیکون مداد اصلاحش کن.

## 2. فایل .gitignore
_GitHub · حدود 2 دقیقه_

**چرا:** به git می‌گوید چه چیزهایی هرگز وارد repo نشوند: محیط مجازی پایتون، فایل‌های موقت، و مهم‌تر از همه `.env` که کلید API در آن است. باید **قبل از** هر فایل دیگری ساخته شود.

1. در صفحه‌ی repo: **Add file** → **Create new file**، نام: `.gitignore`، متن زیر را paste کن.
2. **Commit changes** با پیام `Add .gitignore`.

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

**چرا:** فهرست بسته‌هایی که پروژه لازم دارد. هسته‌ی پروژه فقط با کتابخانه‌ی استاندارد پایتون کار می‌کند (عمداً: می‌خواهی ببینی جست‌وجو زیر پوشش چطور کار می‌کند)؛ `pytest` برای تست و `ipykernel` برای اینکه VS Code بتواند notebook را با همین محیط اجرا کند.

1. **Add file → Create new file**، نام `requirements.txt`. commit: `Add requirements`.

`requirements.txt`

````
# core: standard library only, plus tests and notebooks
pytest>=8.0
ipykernel>=6.29
# optional model providers (install the one you use)
# ollama>=0.4        # local models
# anthropic>=0.40    # Claude API (needs an API key from console.anthropic.com)
````

## 4. فایل داده: data/faq.json
_GitHub · حدود 3 دقیقه_

**چرا:** همان پنج صفحه‌ی FAQ پروژه‌ی p01 به‌علاوه‌ی ۱۶ سؤال: ۱۲ قابل‌پاسخ، ۳ عمداً بی‌جواب و یک سلام. ستون `answerable` می‌گوید سیستم باید جواب بدهد، امتناع کند یا مستقیم جواب بدهد.

1. **Add file → Create new file**، در کادر نام بنویس `data/faq.json` (با تایپ `/` خود GitHub پوشه را می‌سازد).
2. متن زیر را paste کن. commit: `Add FAQ data with answerable, unanswerable and direct questions`.

`data/faq.json`

````json
{
 "docs": {
  "payment": "# Payment\n\n## Methods\nWe accept credit cards, PayPal and bank transfer. We do not accept cash or cryptocurrency.\n\n## Invoices\nThe invoice is attached to your order confirmation email and can be downloaded again from the account page.\n",
  "refunds": "# Refunds\n\n## Timing\nWe send your money back to the original payment method within 14 days after we receive the item.\n\n## Partial refunds\nIf an item comes back damaged or used, we may refund only part of the price and explain the deduction by email.\n\n## Gift orders\nRefunds for gift orders go to the buyer, not to the recipient.\n",
  "returns": "# Returns\n\n## Return window\nYou can return most items within 30 days of delivery. Return shipping is free for orders in Germany.\n\n## Exceptions\nCustom-made and personalised items cannot be returned. Opened hygiene products cannot be returned.\n\n## How to start a return\nOpen your order in the account page and choose \"Return item\". Print the label and hand the parcel to any carrier.\n",
  "shipping": "# Shipping\n\n## Delivery times\nStandard delivery takes 3 to 5 working days. Express delivery takes 1 to 2 working days and is available for small items.\n\n## Costs\nShipping is free above 50 EUR. Below that, standard shipping costs 4.90 EUR and express costs 9.90 EUR.\n\n## Tracking\nYou receive a tracking link by email when the parcel leaves our warehouse.\n",
  "warranty": "# Warranty\n\n## Coverage\nFurniture has a 2-year warranty against manufacturing defects. Damage from misuse or normal wear is not covered.\n\n## How to claim\nSend a photo of the defect and your order number to support. We answer within 2 working days.\n"
 },
 "questions": [
  {
   "question": "how long do I have to send back a sofa",
   "relevant": "returns",
   "answerable": "yes"
  },
  {
   "question": "can I return a personalised mirror",
   "relevant": "returns",
   "answerable": "yes"
  },
  {
   "question": "how do I start a return",
   "relevant": "returns",
   "answerable": "yes"
  },
  {
   "question": "when do I get my money back",
   "relevant": "refunds",
   "answerable": "yes"
  },
  {
   "question": "what if the item comes back damaged",
   "relevant": "refunds",
   "answerable": "yes"
  },
  {
   "question": "how fast is standard delivery",
   "relevant": "shipping",
   "answerable": "yes"
  },
  {
   "question": "how much does express shipping cost",
   "relevant": "shipping",
   "answerable": "yes"
  },
  {
   "question": "is there a tracking link",
   "relevant": "shipping",
   "answerable": "yes"
  },
  {
   "question": "is a broken table leg covered",
   "relevant": "warranty",
   "answerable": "yes"
  },
  {
   "question": "how do I claim the warranty",
   "relevant": "warranty",
   "answerable": "yes"
  },
  {
   "question": "can I pay with PayPal",
   "relevant": "payment",
   "answerable": "yes"
  },
  {
   "question": "where is my invoice",
   "relevant": "payment",
   "answerable": "yes"
  },
  {
   "question": "can I pay by cheque",
   "relevant": "",
   "answerable": "no"
  },
  {
   "question": "what is the CEO's phone number",
   "relevant": "",
   "answerable": "no"
  },
  {
   "question": "do you sell gift cards",
   "relevant": "",
   "answerable": "no"
  },
  {
   "question": "hello",
   "relevant": "",
   "answerable": "direct"
  }
 ]
}
````

## 5. فایل اصلی: agentic_rag.py
_GitHub · حدود 5 دقیقه_

**چرا:** حلقه‌ی کامل در یک فایل: مسیریابی، جست‌وجو، نمره‌دادن به شواهد، بازنویسی query با سقف دور، جواب با ارجاع، راستی‌آزمایی و امتناع؛ هر تصمیم یک تابع کوچک است با نسخه‌ی قاعده‌ای (بدون مدل) و نسخه‌ی مدلی (`make_llm_components`). هر تکه را در درس p22 قدم‌به‌قدم ساخته‌ای.

1. **Add file → Create new file**، نام `agentic_rag.py`. commit: `Add agentic RAG loop with rule-based and model-based decisions`.

`agentic_rag.py`

````python
"""Agentic RAG on FAQ pages: route -> retrieve -> grade -> rewrite (bounded) -> answer -> verify -> abstain.

Every decision is a small function. The rule-based versions run without any model; the model-based versions
(make_llm_components) ask an LLM for the same decisions in JSON. Both plug into the same loop, so they can be compared."""
import json
import os
import re
import shutil
import subprocess

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "and", "or", "in", "on", "for", "can", "how",
        "what", "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that", "when", "where", "there", "much", "many",
        "get", "have", "long", "within", "will"}
SYN = {"send back": "return", "money back": "refund", "broken": "damage defect", "couch": "sofa"}
GREETINGS = {"hello", "hi", "hey", "thanks", "thank you", "bye"}


# ---------- data and a simple retriever ----------

def load_data(path="data/faq.json"):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["docs"], data["questions"]


def chunk_all(docs):
    """One chunk per '## ' section, heading path kept ('Returns > Return window')."""
    out = []
    for doc_id, text in docs.items():
        title, heading, buf, n = "", "", [], 0
        for line in text.splitlines() + ["# "]:
            if line.startswith("#"):
                body = " ".join(" ".join(buf).split())
                if body:
                    out.append({"id": f"{doc_id}#{n}", "doc_id": doc_id, "heading": " > ".join(x for x in (title, heading) if x), "text": body})
                    n += 1
                buf = []
                if line.startswith("## "):
                    heading = line[3:].strip()
                else:
                    title, heading = line[2:].strip(), ""
            else:
                buf.append(line)
    return out


def content_words(text):
    """Lowercase words without stop words; a trailing 's' is removed (invoices -> invoice)."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words if w not in STOP and len(w) > 1}


def expand(text):
    text = text.lower()
    for a, b in SYN.items():
        text = text.replace(a, b)
    return text


def make_search(chunks, k=3):
    """Word-overlap retriever (stand-in for BM25 / hybrid from the FAQ search project)."""
    def search(query):
        q = content_words(query)
        scored = [(len(q & content_words(c["heading"] + " " + c["text"])), i) for i, c in enumerate(chunks)]
        return [chunks[i] for s, i in sorted(scored, key=lambda t: (-t[0], t[1])) if s > 0][:k]
    return search


# ---------- rule-based decisions ----------

def route(question):
    q = question.strip().lower().rstrip("!.? ").strip()
    if q in GREETINGS or re.fullmatch(r"[\d\s+\-*/().]+", q):
        return "direct"
    return "retrieve"


def grade(question, chunk, min_ratio=0.5):
    """Relevant when at least half of the question's content words appear in the chunk."""
    q = content_words(expand(question))
    return bool(q) and len(q & content_words(chunk["heading"] + " " + chunk["text"])) / len(q) >= min_ratio


def rewrite(question, tried):
    words = sorted(content_words(expand(question)))
    out = []
    for cand in [expand(question), " ".join(words), *words]:
        if cand and cand not in tried and cand not in out:
            out.append(cand)
    return out


def verify(answer, chunks):
    """Every content word of the answer (citations removed) must appear in the evidence."""
    words = content_words(re.sub(r"\[[^\]]*\]", " ", answer or ""))
    return bool(words) and words <= content_words(" ".join(c["text"] for c in chunks))


def extractive_answer(question, chunks):
    """Best sentence of the best chunk, cited. No model needed."""
    qw = content_words(expand(question))
    best = max(chunks, key=lambda c: len(qw & content_words(c["text"])))
    sents = re.split(r"(?<=[.!?])\s+", best["text"])
    return max(sents, key=lambda s: len(qw & content_words(s))) + f" [{best['id']}]", [best["id"]]


# ---------- the loop ----------

def agentic_search(question, search, grade, rewrite, max_rounds=3, min_relevant=1):
    queries, tried, relevant, rounds = [question], [], {}, 0
    while queries and rounds < max_rounds:
        rounds += 1
        for q in queries:
            tried.append(q)
            for c in search(q):
                if grade(question, c):
                    relevant.setdefault(c["id"], c)
        if len(relevant) >= min_relevant:
            break
        queries = [x for x in rewrite(question, tried) if x not in tried]
    return {"chunks": list(relevant.values()), "rounds": rounds, "queries": tried}


def run_agent(question, search, grade=grade, rewrite=rewrite, answer_fn=extractive_answer, verify=verify, route=route,
              direct=lambda q: "Hello! How can I help?"):
    r = route(question)
    if r == "direct":
        return {"answer": direct(question), "citations": [], "route": r, "rounds": 0, "abstained": False}
    found = agentic_search(question, search, grade, rewrite)
    abstain = {"answer": None, "citations": [], "route": r, "rounds": found["rounds"], "abstained": True}
    if not found["chunks"]:
        return abstain
    text, cites = answer_fn(question, found["chunks"])
    ids = {c["id"] for c in found["chunks"]}
    cites = [c for c in cites if c in ids]
    if not cites or not verify(text, found["chunks"]):
        return abstain
    return {"answer": text, "citations": cites, "route": r, "rounds": found["rounds"], "abstained": False}


def plain_rag(question, search):
    """Baseline: always answers from whatever the search returns."""
    chunks = search(question)
    if not chunks:
        return {"answer": None, "citations": [], "route": "retrieve", "rounds": 1, "abstained": True}
    text, cites = extractive_answer(question, chunks)
    return {"answer": text, "citations": cites, "route": "retrieve", "rounds": 1, "abstained": False}


def report(outcomes, questions):
    out = {"answered_correctly": 0, "abstained_wrongly": 0, "abstained_correctly": 0, "answered_unanswerable": 0, "direct_ok": 0}
    for o, q in zip(outcomes, questions):
        if q["answerable"] == "yes":
            out["abstained_wrongly" if o["abstained"] else "answered_correctly"] += 1
        elif q["answerable"] == "no":
            out["abstained_correctly" if o["abstained"] else "answered_unanswerable"] += 1
        elif o["route"] == "direct":
            out["direct_ok"] += 1
    return out


# ---------- model-based decisions (Ollama, Claude or OpenCode) ----------

def make_llm(provider=None, model=None):
    """A function messages -> text. provider: ollama | anthropic | opencode (default: AGENT_PROVIDER)."""
    provider = provider or os.environ.get("AGENT_PROVIDER", "")
    if provider == "ollama":
        import ollama
        model = model or "qwen2.5:7b"
        return lambda msgs: ollama.chat(model=model, messages=msgs, options={"temperature": 0})["message"]["content"]
    if provider == "anthropic":
        import anthropic
        client, model = anthropic.Anthropic(), model or "claude-sonnet-5-5"   # reads ANTHROPIC_API_KEY

        def claude(msgs):
            r = client.messages.create(model=model, max_tokens=500, messages=msgs)
            return "".join(b.text for b in r.content if b.type == "text")
        return claude
    if provider == "opencode":
        if not shutil.which("opencode"):
            raise RuntimeError("opencode is not installed (https://opencode.ai)")
        model = model or "anthropic/claude-sonnet-5-5"
        return lambda msgs: subprocess.run(["opencode", "run", "-m", model, "\n\n".join(m["content"] for m in msgs)],
                                           capture_output=True, text=True, encoding="utf-8", timeout=300).stdout.strip()
    raise ValueError("set AGENT_PROVIDER to ollama, anthropic or opencode")


def ask_json(llm, prompt):
    text = llm([{"role": "user", "content": prompt + "\nAnswer with one JSON object only."}])
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def make_llm_components(llm):
    """The same four decisions, asked to a model. Returns keyword arguments for run_agent."""
    def m_route(q):
        r = ask_json(llm, f'Does this message need the shop FAQ? {{"route": "direct" or "retrieve"}}\nMessage: {q}')
        return "direct" if r.get("route") == "direct" else "retrieve"

    def m_grade(q, c):
        r = ask_json(llm, f'Does the passage help answer the question? {{"relevant": true or false}}\nQuestion: {q}\nPassage: {c["text"]}')
        return bool(r.get("relevant"))

    def m_rewrite(q, tried):
        r = ask_json(llm, f'These searches found nothing useful: {tried}. Give up to 2 different search queries for: {q}\n{{"queries": [...]}}')
        return [x for x in r.get("queries", []) if isinstance(x, str)][:2]

    def m_answer(q, chunks):
        src = "\n".join(f"[{c['id']}] {c['text']}" for c in chunks)
        text = llm([{"role": "user", "content": f"Answer ONLY from the sources and cite them like [returns#0]. If they do not "
                                                f"answer the question, say you do not know.\nSources:\n{src}\n\nQuestion: {q}"}])
        return text, re.findall(r"\[([^\]]+)\]", text)

    def m_verify(a, chunks):
        src = "\n".join(c["text"] for c in chunks)
        r = ask_json(llm, f'Is every claim in the answer supported by the sources? {{"supported": true or false}}\nSources:\n{src}\nAnswer: {a}')
        return bool(r.get("supported"))

    return {"route": m_route, "grade": m_grade, "rewrite": m_rewrite, "answer_fn": m_answer, "verify": m_verify,
            "direct": lambda q: llm([{"role": "user", "content": q}])}
````

مدل در `make_llm` با متغیر محیطی `AGENT_PROVIDER` انتخاب می‌شود: `ollama`، `anthropic` یا `opencode`. بدون آن، فقط نسخه‌ی قاعده‌ای اجرا می‌شود.

<details><summary><b>درک کد: تابع به تابع</b></summary>

- **`route`**: سلام و حساب ساده مستقیم جواب می‌گیرند؛ بقیه به جست‌وجو می‌روند. در تردید، جست‌وجو امن‌تر است. ([درس](../../lessons/p22_agentic_rag/step01_router/lesson.md))
- **`content_words، expand، grade`**: مرتبط بودن = حداقل نصف کلمه‌های محتوایی سؤال در تکه باشد؛ مترادف‌ها (send back → return) قبلش باز می‌شوند. ([درس](../../lessons/p22_agentic_rag/step02_grader/lesson.md))
- **`rewrite و agentic_search`**: اگر شاهد کافی نبود، query تازه (مترادف، فقط کلمه‌های محتوایی) با سقف ۳ دور. grade همیشه با سؤال اصلی. ([درس](../../lessons/p22_agentic_rag/step03_corrective_loop/lesson.md))
- **`verify، run_agent، report`**: هر کلمه‌ی محتوایی جواب باید در شواهد باشد؛ ارجاع باید واقعی باشد؛ وگرنه امتناع. report پنج نوع نتیجه را می‌شمارد. ([درس](../../lessons/p22_agentic_rag/step04_verify_abstain/lesson.md))
- **`plain_rag`**: خط پایه برای مقایسه: همیشه از هر چیزی که جست‌وجو آورد جواب می‌دهد.
- **`make_llm و make_llm_components`**: همان چهار تصمیم را از مدل می‌پرسد (JSON) و به همان حلقه می‌دهد؛ پس قاعده و مدل با یک ارزیابی مقایسه می‌شوند. ([درس](../../lessons/p22_agentic_rag/step05_llm_components/lesson.md))

</details>

## 6. فایل check_setup.py
_GitHub · حدود 2 دقیقه_

**چرا:** یک بررسی کوچک که بعد از نصب روی لپ‌تاپ اجرا می‌کنی تا مطمئن شوی پایتون، داده و توابع اصلی کار می‌کنند، قبل از notebook.

1. **Add file → Create new file**، نام `check_setup.py`. commit: `Add setup check`.

`check_setup.py`

````python
"""Run once after installing: checks Python, the data and one full agent run."""
import sys

from agentic_rag import chunk_all, load_data, make_search, run_agent

print("Python", sys.version.split()[0])
docs, questions = load_data()
chunks = chunk_all(docs)
print(len(chunks), "chunks,", len(questions), "questions")
search = make_search(chunks)
print("answerable:", run_agent("how do I claim the warranty", search)["citations"])
print("unanswerable:", "ABSTAIN" if run_agent("what is the CEO's phone number", search)["abstained"] else "answered")
print("setup ok")
````

## 7. تست‌ها: tests/test_agentic_rag.py
_GitHub · حدود 3 دقیقه_

**چرا:** تست خودکار یعنی هر تغییری بعداً خرابی را فوراً نشان می‌دهد. برای کارفرما هم نشانه‌ی مهندسی جدی است. این تست‌ها به هیچ مدلی نیاز ندارند: به‌جای مدل یک تابع ساختگی می‌دهیم.

1. **Add file → Create new file**، نام `tests/test_agentic_rag.py`. commit: `Add tests`.

`tests/test_agentic_rag.py`

````python
from agentic_rag import (agentic_search, chunk_all, grade, load_data, make_llm_components, make_search, plain_rag, report,
                         rewrite, route, run_agent, verify)

C = [{"id": "returns#0", "heading": "Returns > Return window", "text": "You can return most items within 30 days of delivery."}]


def test_route():
    assert route("Hello!") == "direct" and route("2+2") == "direct" and route("how long to return a sofa") == "retrieve"


def test_grade_uses_ratio_and_synonyms():
    assert grade("how long do I have to send back a sofa", C[0])
    warranty = {"id": "w#1", "heading": "Warranty", "text": "Send a photo of the defect and your order number to support."}
    assert not grade("what is the CEO's phone number", warranty)          # one shared word of three


def test_loop_is_bounded_and_rewrites():
    out = agentic_search("q", lambda s: [], lambda q, c: True, lambda q, t: [f"q{len(t)}"], max_rounds=3)
    assert out["rounds"] == 3 and out["chunks"] == []
    assert rewrite("how to send back a sofa", [])[0] == "how to return a sofa"


def test_verify_rejects_invented_claims():
    assert verify("You can return items within 30 days [returns#0]", C)
    assert not verify("Gold members get free returns [returns#0]", C)


def test_agent_beats_plain_rag_on_unanswerable_questions():
    docs, questions = load_data()
    search = make_search(chunk_all(docs))
    agent = report([run_agent(q["question"], search) for q in questions], questions)
    plain = report([plain_rag(q["question"], search) for q in questions], questions)
    assert agent["answered_unanswerable"] < plain["answered_unanswerable"]
    assert agent["answered_correctly"] >= plain["answered_correctly"] - 1


def test_model_components_with_a_fake_model():
    def fake(msgs):
        p = msgs[-1]["content"]
        if "route" in p:
            return '{"route": "retrieve"}'
        if "relevant" in p:
            return '{"relevant": true}'
        if "supported" in p:
            return '{"supported": true}'
        return "You have 30 days [returns#0] [made_up#1]"
    out = run_agent("how long to return", lambda q: C, **make_llm_components(fake))
    assert not out["abstained"] and out["citations"] == ["returns#0"]
````

## 8. تست خودکار در GitHub (Actions)
_GitHub · حدود 3 دقیقه_

**چرا:** با هر push، GitHub خودش تست‌ها را روی یک ماشین تمیز اجرا می‌کند. تیک سبز کنار commit ها یعنی پروژه روی هر سیستمی کار می‌کند، نه فقط لپ‌تاپ تو.

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

## 9. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
_VS Code · حدود 8 دقیقه_

**چرا:** محیط مجازی (venv) یک پایتون جدا فقط برای این پروژه است تا بسته‌هایش با پروژه‌های دیگر قاطی نشوند.

پیش‌نیاز: Git (از git-scm.com) و Python 3.10 یا جدیدتر، و در VS Code افزونه‌های **Python** و **Jupyter** از Microsoft.

1. VS Code: `Ctrl+Shift+P` → **Git: Clone** → آدرس `https://github.com/<نام-کاربری-تو>/agentic_rag.git` → یک پوشه انتخاب کن → **Open**.
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
13 chunks, 16 questions
answerable: ['warranty#0']
unanswerable: ABSTAIN
setup ok

......                                                                   [100%]
6 passed
```

> **حواست باشد:** اگر PowerShell گفت running scripts is disabled: یک بار `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` و دوباره فعال کن. روی Mac/Linux به‌جای خط دوم: `source .venv/bin/activate`.

## 10. ساختن و اجرای notebook
_VS Code · حدود 15 دقیقه_

**چرا:** notebook داستان پروژه است: داده، روش‌ها، مقایسه با عدد، و جواب‌ها. کسی که repo را در GitHub باز می‌کند، از همین notebook (با خروجی‌هایش) می‌فهمد چه کرده‌ای.

1. VS Code: `Ctrl+Shift+P` → **Create: New Jupyter Notebook** → `Ctrl+S` با نام `01_agentic_rag.ipynb` در پوشه‌ی repo.
2. بالا سمت راست **Select Kernel → Python Environments → .venv**.
3. سلول‌ها را به ترتیب زیر بساز (متن: **+ Markdown**، کد: **+ Code**) و هر سلول کد را با `Shift+Enter` اجرا کن. خروجی را با «باید ببینی» زیرش مقایسه کن.

_سلول متنی (Markdown):_

````markdown
# Agentic RAG: retrieve again when needed, and know when to say "I don't know"

Plain RAG always answers from whatever the search returns. This agent routes the question, grades the evidence,
rewrites the query when nothing relevant is found (at most 3 rounds), verifies the answer against the evidence, and
abstains otherwise. 16 questions: 12 answerable, 3 with no answer on purpose, 1 greeting.
````

_سلول کد 1:_

```python
from agentic_rag import chunk_all, load_data, make_search, plain_rag, report, run_agent

docs, questions = load_data()
search = make_search(chunk_all(docs))
print(len(questions), "questions:", {k: sum(q["answerable"] == k for q in questions) for k in ["yes", "no", "direct"]})
```

داده و جست‌وجو را آماده می‌کند.

**باید ببینی:**

```
16 questions: {'yes': 12, 'no': 3, 'direct': 1}
```

_سلول متنی (Markdown):_

````markdown
## Baseline: plain RAG
Search, take the best sentence, answer. No grading, no verification.
````

_سلول کد 2:_

```python
plain = [plain_rag(q["question"], search) for q in questions]
print(report(plain, questions))
```

پایه: دو تا از سه سؤال بی‌جواب جواب می‌گیرند (`answered_unanswerable: 2`)؛ فقط وقتی جست‌وجو هیچ چیزی پیدا نکند ساکت می‌ماند. این همان مشکل RAG ساده است.

**باید ببینی:**

```
{'answered_correctly': 12, 'abstained_wrongly': 0, 'abstained_correctly': 1, 'answered_unanswerable': 2, 'direct_ok': 0}
```

_سلول متنی (Markdown):_

````markdown
## The agent (rules, no model)
route -> retrieve -> grade -> rewrite (bounded) -> answer -> verify -> abstain.
````

_سلول کد 3:_

```python
agent = [run_agent(q["question"], search) for q in questions]
for q, o in zip(questions, agent):
    shown = "ABSTAIN" if o["abstained"] else (o["answer"] or "")[:55]
    print(f"{q['question'][:40]:40s} {o['route']:8s} rounds={o['rounds']}  {shown}")
print()
print(report(agent, questions))
```

عامل: سؤال‌های بی‌جواب امتناع می‌شوند، «hello» مستقیم جواب می‌گیرد، و «send back a sofa» بعد از بازنویسی (rounds=2) پیدا می‌شود.

**باید ببینی:**

```
how long do I have to send back a sofa   retrieve rounds=2  You can return most items within 30 days of delivery. [
can I return a personalised mirror       retrieve rounds=1  Custom-made and personalised items cannot be returned. 
how do I start a return                  retrieve rounds=1  Open your order in the account page and choose "Return 
when do I get my money back              retrieve rounds=1  If an item comes back damaged or used, we may refund on
what if the item comes back damaged      retrieve rounds=1  If an item comes back damaged or used, we may refund on
how fast is standard delivery            retrieve rounds=1  Standard delivery takes 3 to 5 working days. [shipping#
how much does express shipping cost      retrieve rounds=1  Below that, standard shipping costs 4.90 EUR and expres
is there a tracking link                 retrieve rounds=1  You receive a tracking link by email when the parcel le
is a broken table leg covered            retrieve rounds=1  Damage from misuse or normal wear is not covered. [warr
how do I claim the warranty              retrieve rounds=1  Furniture has a 2-year warranty against manufacturing d
can I pay with PayPal                    retrieve rounds=1  We accept credit cards, PayPal and bank transfer. [paym
where is my invoice                      retrieve rounds=1  The invoice is attached to your order confirmation emai
can I pay by cheque                      retrieve rounds=2  ABSTAIN
what is the CEO's phone number           retrieve rounds=2  ABSTAIN
do you sell gift cards                   retrieve rounds=2  ABSTAIN
hello                                    direct   rounds=0  Hello! How can I help?

{'answered_correctly': 12, 'abstained_wrongly': 0, 'abstained_correctly': 3, 'answered_unanswerable': 0, 'direct_ok': 1}
```

_سلول متنی (Markdown):_

````markdown
## Comparison
````

_سلول کد 4:_

```python
import json, os

rows = {"plain RAG": report(plain, questions), "agentic (rules)": report(agent, questions)}
print(f"{'':16s} {'answered':>8s} {'wrong abstain':>14s} {'right abstain':>14s} {'answered unanswerable':>22s}")
for name, r in rows.items():
    print(f"{name:16s} {r['answered_correctly']:8d} {r['abstained_wrongly']:14d} {r['abstained_correctly']:14d} {r['answered_unanswerable']:22d}")
os.makedirs("results", exist_ok=True)
with open("results/results.json", "w") as f:
    json.dump(rows, f, indent=2)
```

جدول نهایی و ذخیره در `results/results.json` (عددهای README از همین فایل).

**باید ببینی:**

```
                 answered  wrong abstain  right abstain  answered unanswerable
plain RAG              12              0              1                      2
agentic (rules)        12              0              3                      0
```

_سلول متنی (Markdown):_

````markdown
## With a real model (optional)
Set `AGENT_PROVIDER` to `ollama`, `anthropic` or `opencode` before starting the notebook; the same loop then asks the
model for each decision. Without it, this cell only prints how to turn it on.
````

_سلول کد 5:_

```python
import os
from agentic_rag import make_llm, make_llm_components

if os.environ.get("AGENT_PROVIDER"):
    parts = make_llm_components(make_llm())
    llm_agent = [run_agent(q["question"], search, **parts) for q in questions]
    rows["agentic (model)"] = report(llm_agent, questions)
    print(rows["agentic (model)"])
    with open("results/results.json", "w") as f:
        json.dump(rows, f, indent=2)
else:
    print("No model set: AGENT_PROVIDER = ollama | anthropic | opencode (see step 11 of the guide)")
```

بدون مدل فقط راهنما چاپ می‌کند. با مدل، همان پنج شمارنده را برای عامل مدلی می‌بینی؛ با مدل کوچک ممکن است از قاعده‌ها بدتر شود و این هم یک نتیجه است.

**باید ببینی:**

```
No model set: AGENT_PROVIDER = ollama | anthropic | opencode (see step 11 of the guide)
```

_سلول متنی (Markdown):_

````markdown
## Limitations
- 16 questions: enough to see the behaviour, not to claim a precise rate.
- The rule grader is word overlap; it does not understand meaning ("bank transfer" vs "return transfer").
- With a model, the same model answers and verifies; a different or stronger verifier is safer.
````

> **نکته:** اگر نمی‌خواهی سلول‌ها را یکی‌یکی بسازی: دکمه‌ی **دانلود notebook** پایین همین مرحله فایل آماده را می‌دهد؛ آن را در پوشه‌ی repo بگذار و همه‌ی سلول‌ها را اجرا کن (Run All). ولی یک بار دستی ساختن، کد را بهتر در ذهنت می‌نشاند.

## 11. اجرا با مدل زبانی واقعی (اختیاری)
_VS Code · Ollama / Claude / OpenCode · حدود 10 دقیقه_

**چرا:** نسخه‌ی قاعده‌ای معنا را نمی‌فهمد. با مدل، همان چهار تصمیم (مسیر، مرتبط بودن، بازنویسی، راستی‌آزمایی) را مدل می‌گیرد. هر سؤال چند فراخوانی مدل است، پس کندتر و (برای Claude) پولی است؛ با عدد مقایسه کن که ارزشش را دارد یا نه.

1. یکی از سه راه را انتخاب کن و در ترمینال VS Code اجرا کن، بعد سلول «With a real model» در notebook را دوباره اجرا کن (اول **Restart** kernel تا متغیر محیطی خوانده شود).

_Ollama (محلی، رایگان) · از ollama.com نصب کن_

```
ollama pull qwen2.5:7b
pip install ollama
$env:AGENT_PROVIDER = "ollama"
```

_Claude (کلید API از console.anthropic.com؛ اشتراک Claude.ai کلید API نیست)_

```
pip install anthropic
$env:ANTHROPIC_API_KEY = "sk-ant-..."     # فقط در ترمینال؛ هرگز در فایل یا notebook
$env:AGENT_PROVIDER = "anthropic"
```

_OpenCode (اگر نصب داری و وارد یک provider شده‌ای)_

```
opencode models
$env:AGENT_PROVIDER = "opencode"
```

> **حواست باشد:** کلید API را هرگز در notebook یا فایل‌های repo ننویس. اگر اشتباهاً push شد، فوراً در Console باطلش کن؛ پاک کردن commit کافی نیست. در Mac/Linux به‌جای `$env:X = "y"` بنویس `export X=y`.

## 12. commit و push از VS Code
_VS Code · GitHub · حدود 3 دقیقه_

**چرا:** notebook با خروجی‌هایش و فایل نتایج باید در GitHub باشند تا بدون اجرا دیده شوند.

1. پنل Source Control: `Ctrl+Shift+G`. فایل‌های `01_agentic_rag.ipynb` و `results/results.json` را می‌بینی.
2. پیام: `Add notebook: plain RAG vs agentic RAG` → **Commit** → **Sync Changes**.

> **باید ببینی:** در GitHub، `01_agentic_rag.ipynb` را باز کن: جدول‌ها و خروجی‌ها بدون اجرا دیده می‌شوند. تب Actions دوباره سبز است.

> **حواست باشد:** قانون ساده: قبل از هر کار در VS Code اول **Pull** بزن، و یک فایل را هم‌زمان در GitHub و VS Code ویرایش نکن.

## 13. README نهایی
_GitHub · حدود 10 دقیقه_

**چرا:** README صفحه‌ی اول پروژه است. باید در ۳۰ ثانیه بگوید: چه مسئله‌ای، چه روشی، چه عددی، و محدودیت‌ها چیست. عددها را از `results/results.json` خودت بردار، نه از این صفحه.

1. در GitHub روی `README.md` → آیکون مداد → همه‌ی متن را با متن زیر عوض کن و عددهای داخل `{...}` را با عددهای خودت پر کن (یا فایل results.json را پایین paste کن). commit: `Write README`.
2. نام کاربری‌ات را در خط badge جایگزین کن.

````markdown
# Agentic RAG: answer with evidence or abstain

![tests](https://github.com/<your-user>/agentic_rag/actions/workflows/tests.yml/badge.svg)

Plain RAG always answers, even when the search found nothing useful. This agent routes each question, grades the
evidence, rewrites the query when needed (at most 3 rounds), verifies the answer against the evidence and abstains
otherwise. Every decision is a small function with a rule-based and a model-based (Ollama / Claude / OpenCode) version.

## Results (`results/results.json`, 16 questions: 12 answerable, 3 unanswerable, 1 greeting)
| system | answered (answerable) | wrong abstentions | right abstentions | answered unanswerable |
|---|---|---|---|---|
| plain RAG | {plain_correct} | {plain_wrong_abstain} | {plain_right_abstain} | {plain_unanswerable} |
| agentic (rules) | {agent_correct} | {agent_wrong_abstain} | {agent_right_abstain} | {agent_unanswerable} |

## How it works
`route` (direct or retrieve) → `search` → `grade` (half of the question's content words must appear) → `rewrite`
(synonyms, content words) → `answer` (cited) → `verify` (every content word of the answer is in the evidence) → abstain.

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_agentic_rag.ipynb` and run all cells. Optional model: `AGENT_PROVIDER=ollama|anthropic|opencode`.

## Limitations
- Small labelled set; the rule grader is word overlap, not meaning.
- In the model version the same model answers and verifies.

## Licence
MIT
````

## 14. صیقل نهایی repo
_GitHub · حدود 5 دقیقه_

**چرا:** جزئیات کوچکی که repo را حرفه‌ای نشان می‌دهد.

1. صفحه‌ی repo → آیکون چرخ‌دنده کنار **About** → Topics: `rag`, `agentic-rag`, `llm`, `evaluation`, `python`.
2. در پروفایل GitHub: **Customize your pins** → این repo را pin کن.
3. یک خط رزومه از جدول نتایج بنویس (پایین همین مرحله).

**خط رزومه:** Built an agentic RAG loop (routing, evidence grading, bounded query rewriting, verification, abstention) that cut answers to unanswerable questions from {plain} to {agent} versus plain RAG on a labelled set, with rule-based and LLM-based (Ollama / Claude / OpenCode) decisions; tested with pytest and GitHub Actions.

## اگر به خطا خوردی
- **`python` شناخته نمی‌شود**: Python را با تیک «Add to PATH» نصب کن، یا به‌جای `python` بنویس `py`.
- **`No module named agentic_rag` در notebook**: notebook باید در همان پوشه‌ی `agentic_rag.py` باشد و kernel روی `.venv` باشد (بالا سمت راست).
- **`FileNotFoundError: data/faq.json`**: فایل داده را در مرحله‌ی ۴ با مسیر دقیق `data/faq.json` ساخته‌ای؟ notebook را از پوشه‌ی repo اجرا کن.
- **تب Actions قرمز است**: روی اجرای قرمز کلیک کن؛ معمولاً یک فایل با نام یا مسیر اشتباه ساخته شده (مثلاً `test/` به‌جای `tests/`).
- **`ConnectionError` با Ollama**: Ollama را اجرا کن (آیکونش کنار ساعت) و `ollama list` را بزن.
- **Claude خطای 401 می‌دهد**: کلید API اشتباه یا تمام شده؛ اشتراک Claude.ai کلید API نیست.

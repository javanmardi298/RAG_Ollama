# ساختن پروژه‌ی جست‌وجوی FAQ با جواب مستند، از صفر در GitHub

همه‌ی فایل‌ها را خودت در GitHub می‌سازی، همان کد را روی لپ‌تاپ در VS Code اجرا می‌کنی، و آخر یک repo تمیز با README، تست و CI داری که در رزومه می‌گذاری. هیچ GPU و هیچ مدلی لازم نیست؛ مدل واقعی (Ollama، Claude یا OpenCode) در مرحله‌ی ۱۱ اختیاری است.

> نسخه‌ی تعاملی (تیک مراحل، مقایسه‌ی خروجی، پرسیدن از Claude، دانلود notebook): صفحه‌ی «راهنمای ساخت پروژه‌ها» (claude.ai artifact).

**برای فهمیدن بهتر:** [درس قدم‌به‌قدم همین پروژه (۵ گام با تمرین)](../../lessons/p01_faq_search/README.md) · پروژه در نقشه‌ی راه: مرحله‌ها، سؤال مصاحبه، نسخه‌ی پیشرفته (نقشه‌ی راه، پروژه‌ی `p01_faq_search`)

## مراحل
1. ساختن repo در GitHub
2. فایل .gitignore
3. فایل requirements.txt
4. فایل داده: data/faq.json
5. فایل اصلی: faq_search.py
6. فایل check_setup.py
7. تست‌ها: tests/test_faq_search.py
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
2. **Repository name:** `faq_search`
3. **Description:** `FAQ search from scratch: BM25 + typo-tolerant trigram search fused with RRF, evaluated with recall@k / MRR, and LLM answers that cite their sources or abstain`
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

**چرا:** پنج صفحه‌ی FAQ یک فروشگاه (بازگشت کالا، بازپرداخت، ارسال، گارانتی، پرداخت) و ۱۵ سؤال واقعی مشتری با جواب درست. سه سؤال عمداً جواب ندارند تا ببینی سیستم کی باید بگوید «نمی‌دانم». داده ساختگی است و مجوزی لازم ندارد.

1. **Add file → Create new file**، در کادر نام بنویس `data/faq.json` (با تایپ `/` خود GitHub پوشه را می‌سازد).
2. متن زیر را paste کن. commit: `Add FAQ data and labelled questions`.

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
  }
 ]
}
````

## 5. فایل اصلی: faq_search.py
_GitHub · حدود 5 دقیقه_

**چرا:** همه‌ی منطق پروژه در یک فایل: تکه‌کردن سند با حفظ عنوان، BM25 از صفر، جست‌وجوی سه‌حرفی (مقاوم به غلط املایی)، ترکیب با RRF، معیارهای recall@k و MRR، و جواب با ارجاع که اگر شاهد نباشد امتناع می‌کند. هر تکه را در درس‌های p01 قدم‌به‌قدم ساخته‌ای؛ اینجا نسخه‌ی تمیز و یکجای آن است.

1. **Add file → Create new file**، نام `faq_search.py`. commit: `Add FAQ search: chunking, BM25, trigram, RRF, metrics, grounded answers`.

`faq_search.py`

````python
"""FAQ search from scratch: markdown chunks, BM25, character-trigram search, Reciprocal Rank Fusion,
retrieval metrics, and grounded answers with citations that abstain when there is no evidence."""
import json
import math
import os
import re
import shutil
import subprocess
from collections import Counter

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "and", "or", "in", "on", "for", "can", "how",
        "what", "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that"}


# ---------- data ----------

def load_data(path="data/faq.json"):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["docs"], data["questions"]


def chunk_markdown(text, doc_id):
    """One chunk per '## ' section; the heading path ('Returns > Return window') stays with the text."""
    chunks, h1, h2, buf = [], "", "", []

    def flush():
        body = " ".join(" ".join(buf).split())
        if body:
            heading = " > ".join(x for x in (h1, h2) if x)
            chunks.append({"id": f"{doc_id}#{len(chunks)}", "doc_id": doc_id, "heading": heading, "text": body})
        buf.clear()

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            h2 = line[3:].strip()
        elif line.startswith("# "):
            flush()
            h1, h2 = line[2:].strip(), ""
        else:
            buf.append(line)
    flush()
    return chunks


def chunk_all(docs):
    return [c for doc_id, text in docs.items() for c in chunk_markdown(text, doc_id)]


# ---------- search ----------

def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class BM25:
    def __init__(self, texts, k1=1.5, b=0.75):
        toks = [tokenize(t) for t in texts]
        self.k1, self.b = k1, b
        self.tf = [Counter(t) for t in toks]
        self.len = [len(t) for t in toks]
        self.n = len(texts)
        self.avg = sum(self.len) / self.n if self.n else 0.0
        self.df = Counter(w for t in toks for w in set(t))

    def idf(self, term):
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def scores(self, query):
        out = [0.0] * self.n
        for term in tokenize(query):
            if not self.df.get(term):
                continue
            idf = self.idf(term)
            for i in range(self.n):
                tf = self.tf[i].get(term, 0)
                if tf:
                    out[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        return out

    def search(self, query, k=3):
        s = self.scores(query)
        return [i for i in sorted(range(self.n), key=lambda i: (-s[i], i)) if s[i] > 0][:k]


def trigrams(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        p = f" {w} "
        out |= {p[i:i + 3] for i in range(len(p) - 2)}
    return out


def trigram_search(query, texts, k=3):
    """Character-trigram Jaccard similarity: survives typos that break BM25."""
    q = trigrams(query)
    sims = []
    for t in texts:
        g = trigrams(t)
        sims.append(len(q & g) / len(q | g) if q | g else 0.0)
    return [i for i in sorted(range(len(texts)), key=lambda i: (-sims[i], i)) if sims[i] > 0][:k]


def rrf(rankings, k=60):
    """Reciprocal Rank Fusion: combine rankings by rank only, so score scales do not matter."""
    score = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            score[doc] = score.get(doc, 0.0) + 1 / (k + rank)
    return sorted(score, key=lambda d: (-score[d], d))


class Searcher:
    """Index of chunks with three methods: bm25, trigram and hybrid (RRF of both)."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.texts = [c["heading"] + ". " + c["text"] for c in chunks]
        self.bm25 = BM25(self.texts)

    def search(self, query, method="hybrid", k=3):
        n = len(self.texts)
        if method == "bm25":
            idx = self.bm25.search(query, k=n)
        elif method == "trigram":
            idx = trigram_search(query, self.texts, k=n)
        else:
            idx = rrf([self.bm25.search(query, k=n), trigram_search(query, self.texts, k=n)])
        return [self.chunks[i] for i in idx[:k]]


# ---------- evaluation ----------

def recall_at_k(ranked, relevant, k):
    return len(set(ranked[:k]) & relevant) / len(relevant) if relevant else 0.0


def reciprocal_rank(ranked, relevant):
    for i, doc in enumerate(ranked):
        if doc in relevant:
            return 1 / (i + 1)
    return 0.0


def evaluate(searcher, questions, method="hybrid", k=3):
    """Mean recall@k and MRR over answerable questions (document level), plus the questions it missed."""
    rec, rr, misses = [], [], []
    for q in questions:
        if not q["relevant"]:
            continue
        ranked = list(dict.fromkeys(c["doc_id"] for c in searcher.search(q["question"], method, k=len(searcher.chunks))))
        rel = {q["relevant"]}
        r = recall_at_k(ranked, rel, k)
        rec.append(r)
        rr.append(reciprocal_rank(ranked, rel))
        if r == 0:
            misses.append(q["question"])
    n = len(rec)
    return {"method": method, f"recall@{k}": round(sum(rec) / n, 3), "mrr": round(sum(rr) / n, 3), "n": n, "misses": misses}


# ---------- answers ----------

SYSTEM = ("You answer customer questions using ONLY the sources provided. After every claim write the id of its source "
          "in square brackets, like [returns#0]. If the sources do not contain the answer, say you do not know.")


def build_messages(question, chunks):
    sources = "\n".join(f"[{c['id']}] {c['heading']}: {c['text']}" for c in chunks)
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Sources:\n{sources}\n\nQuestion: {question}"}]


def extract_citations(text, allowed_ids):
    seen = []
    for cid in re.findall(r"\[([^\]]+)\]", text):
        if cid in allowed_ids and cid not in seen:
            seen.append(cid)
    return seen


def answer(question, chunks, llm):
    """No evidence -> abstain without calling the model. A reply without a real citation is not trusted."""
    if not chunks:
        return {"answer": None, "citations": [], "abstained": True}
    text = llm(build_messages(question, chunks))
    cites = extract_citations(text, {c["id"] for c in chunks})
    if not cites:
        return {"answer": None, "citations": [], "abstained": True}
    return {"answer": text, "citations": cites, "abstained": False}


# ---------- models (one function: messages -> text) ----------

def offline_llm(messages):
    """No model: quotes the first source with its id. Lets everything run without any install."""
    m = re.search(r"\[([^\]]+)\] [^:]*: ([^\n]+)", messages[-1]["content"])
    return f"{m.group(2)} [{m.group(1)}]" if m else "I do not know."


def make_llm(provider=None, model=None):
    """provider: offline | ollama | anthropic | opencode (default from the FAQ_PROVIDER environment variable)."""
    provider = provider or os.environ.get("FAQ_PROVIDER", "offline")
    if provider == "offline":
        return offline_llm
    if provider == "ollama":
        import ollama
        model = model or "qwen2.5:7b"
        return lambda msgs: ollama.chat(model=model, messages=msgs, options={"temperature": 0})["message"]["content"]
    if provider == "anthropic":
        import anthropic
        client, model = anthropic.Anthropic(), model or "claude-sonnet-5-5"   # reads ANTHROPIC_API_KEY

        def claude(msgs):
            system = "\n".join(m["content"] for m in msgs if m["role"] == "system")
            r = client.messages.create(model=model, max_tokens=400, system=system,
                                       messages=[m for m in msgs if m["role"] != "system"])
            return "".join(b.text for b in r.content if b.type == "text")
        return claude
    if provider == "opencode":
        if not shutil.which("opencode"):
            raise RuntimeError("opencode is not installed (https://opencode.ai)")
        model = model or "anthropic/claude-sonnet-5-5"
        return lambda msgs: subprocess.run(["opencode", "run", "-m", model, "\n\n".join(m["content"] for m in msgs)],
                                           capture_output=True, text=True, encoding="utf-8", timeout=300).stdout.strip()
    raise ValueError(f"unknown provider {provider!r}")
````

ارائه‌دهنده‌ی مدل در `make_llm` با متغیر محیطی `FAQ_PROVIDER` انتخاب می‌شود: `offline` (پیش‌فرض، بدون مدل)، `ollama`، `anthropic` یا `opencode`.

<details><summary><b>درک کد: تابع به تابع</b></summary>

- **`chunk_markdown`**: سند را در هر عنوان `##` می‌بُرد و عنوان کامل («Returns > Return window») را کنار متن نگه می‌دارد؛ تابع داخلی `flush` بخش جاری را می‌بندد. ([درس](../../lessons/p01_faq_search/step01_chunk_markdown/lesson.md))
- **`tokenize و BM25`**: BM25 سه ایده دارد: تکرار کلمه (با اشباع k1)، نادر بودن کلمه (idf) و نرمال‌سازی طول (b). `scores` برای هر سند جمع امتیاز کلمه‌های query را می‌دهد؛ `search` صفرها را حذف می‌کند. ([درس](../../lessons/p01_faq_search/step02_bm25/lesson.md))
- **`trigrams و trigram_search`**: هر کلمه به سه‌حرفی‌های هم‌پوشان شکسته می‌شود و شباهت Jaccard حساب می‌شود؛ یک غلط تایپی فقط چند سه‌حرفی را خراب می‌کند. ([درس](../../lessons/p01_faq_search/step04_hybrid_rrf/lesson.md))
- **`rrf و Searcher`**: RRF فقط رتبه‌ها را جمع می‌کند (1/(60+rank))، پس مقیاس متفاوت امتیاز BM25 و Jaccard مهم نیست. Searcher هر سه روش را پشت یک تابع `search` می‌گذارد. ([درس](../../lessons/p01_faq_search/step04_hybrid_rrf/lesson.md))
- **`recall_at_k، reciprocal_rank، evaluate`**: recall@k: سند درست در k نتیجه‌ی اول هست؟ MRR: چقدر بالا؟ `evaluate` سؤال‌های بی‌جواب را کنار می‌گذارد و سندهای تکراری را یکی می‌کند. ([درس](../../lessons/p01_faq_search/step03_metrics/lesson.md))
- **`build_messages، extract_citations، answer`**: prompt منبع‌ها را با شناسه می‌دهد؛ ارجاع‌ها با شناسه‌های واقعی فیلتر می‌شوند؛ بدون شاهد یا بدون ارجاع معتبر = امتناع. دفاع در کد است، نه در prompt. ([درس](../../lessons/p01_faq_search/step05_answer_citations/lesson.md))
- **`make_llm`**: یک رابط برای همه‌ی مدل‌ها: تابعی که پیام‌ها را می‌گیرد و متن برمی‌گرداند. offline بدون مدل، Ollama محلی، Claude با کلید API، OpenCode با `opencode run`. ([درس](../../lessons/m01_compare_models/step01_provider_config/lesson.md))

</details>

## 6. فایل check_setup.py
_GitHub · حدود 2 دقیقه_

**چرا:** یک بررسی کوچک که بعد از نصب روی لپ‌تاپ اجرا می‌کنی تا مطمئن شوی پایتون، داده و توابع اصلی کار می‌کنند، قبل از notebook.

1. **Add file → Create new file**، نام `check_setup.py`. commit: `Add setup check`.

`check_setup.py`

````python
"""Run once after installing: checks Python, the data file and the core functions."""
import sys

from faq_search import BM25, chunk_all, load_data

print("Python", sys.version.split()[0])
docs, questions = load_data()
chunks = chunk_all(docs)
print(len(docs), "documents,", len(chunks), "chunks,", len(questions), "questions")
bm = BM25([c["text"] for c in chunks])
print("BM25 top hit for 'refund money':", chunks[bm.search("refund money", k=1)[0]]["id"])
print("setup ok")
````

## 7. تست‌ها: tests/test_faq_search.py
_GitHub · حدود 3 دقیقه_

**چرا:** تست خودکار یعنی هر تغییری بعداً خرابی را فوراً نشان می‌دهد. برای کارفرما هم نشانه‌ی مهندسی جدی است. این تست‌ها به هیچ مدلی نیاز ندارند: به‌جای مدل یک تابع ساختگی می‌دهیم.

1. **Add file → Create new file**، نام `tests/test_faq_search.py`. commit: `Add tests`.

`tests/test_faq_search.py`

````python
from faq_search import (BM25, Searcher, answer, chunk_all, chunk_markdown, evaluate, extract_citations, load_data,
                        reciprocal_rank, recall_at_k, rrf, trigram_search)

SAMPLE = "# Returns\n\n## Return window\nYou can return items\nwithin 30 days.\n\n## Exceptions\nCustom items cannot be returned.\n"


def test_chunks_keep_heading_path():
    cs = chunk_markdown(SAMPLE, "returns")
    assert [c["id"] for c in cs] == ["returns#0", "returns#1"]
    assert cs[0]["heading"] == "Returns > Return window" and cs[0]["text"] == "You can return items within 30 days."


def test_bm25_ranks_and_excludes_zero_scores():
    bm = BM25(["refund your money", "standard delivery days", "warranty for defects"])
    assert bm.search("money refund")[0] == 0
    assert bm.search("bitcoin") == []
    assert bm.idf("warranty") > 0


def test_trigram_survives_typos_and_rrf_fuses():
    texts = ["standard delivery takes three days", "we refund the money"]
    assert trigram_search("standrd delivry", texts)[0] == 0
    assert rrf([[2, 0, 1], [2, 1, 0]])[0] == 2 and rrf([[0, 1], [1, 0]]) == [0, 1]


def test_metrics():
    assert recall_at_k(["a", "b"], {"b"}, 2) == 1.0 and recall_at_k(["a", "b"], {"b"}, 1) == 0.0
    assert reciprocal_rank(["x", "y"], {"y"}) == 0.5


def test_hybrid_is_at_least_as_good_as_bm25_on_the_faq():
    docs, questions = load_data()
    s = Searcher(chunk_all(docs))
    assert evaluate(s, questions, "hybrid")["recall@3"] >= evaluate(s, questions, "bm25")["recall@3"] - 0.1


def test_answers_cite_real_sources_or_abstain():
    chunks = [{"id": "returns#0", "heading": "Returns", "text": "30 days."}]
    assert answer("q", [], lambda m: "x [returns#0]")["abstained"]                       # no evidence: model not called
    assert answer("q", chunks, lambda m: "90 days [fake#1]")["abstained"]                # invented citation
    ok = answer("q", chunks, lambda m: "You have 30 days [returns#0].")
    assert ok["citations"] == ["returns#0"] and not ok["abstained"]
    assert extract_citations("[a] [b] [a]", {"a", "b"}) == ["a", "b"]
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

1. VS Code: `Ctrl+Shift+P` → **Git: Clone** → آدرس `https://github.com/<نام-کاربری-تو>/faq_search.git` → یک پوشه انتخاب کن → **Open**.
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
5 documents, 13 chunks, 15 questions
BM25 top hit for 'refund money': refunds#0
setup ok

......                                                                   [100%]
6 passed
```

> **حواست باشد:** اگر PowerShell گفت running scripts is disabled: یک بار `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` و دوباره فعال کن. روی Mac/Linux به‌جای خط دوم: `source .venv/bin/activate`.

## 10. ساختن و اجرای notebook
_VS Code · حدود 15 دقیقه_

**چرا:** notebook داستان پروژه است: داده، روش‌ها، مقایسه با عدد، و جواب‌ها. کسی که repo را در GitHub باز می‌کند، از همین notebook (با خروجی‌هایش) می‌فهمد چه کرده‌ای.

1. VS Code: `Ctrl+Shift+P` → **Create: New Jupyter Notebook** → `Ctrl+S` با نام `01_faq_search.ipynb` در پوشه‌ی repo.
2. بالا سمت راست **Select Kernel → Python Environments → .venv**.
3. سلول‌ها را به ترتیب زیر بساز (متن: **+ Markdown**، کد: **+ Code**) و هر سلول کد را با `Shift+Enter` اجرا کن. خروجی را با «باید ببینی» زیرش مقایسه کن.

_سلول متنی (Markdown):_

````markdown
# FAQ search with grounded answers

Questions from customers of a furniture shop are answered from five FAQ pages.
Search is built from scratch (BM25, character trigrams, Reciprocal Rank Fusion) and measured with recall@3 and MRR
on 15 labelled questions (3 of them have no answer on purpose). Answers must cite their sources or abstain.
````

_سلول کد 1:_

```python
from faq_search import Searcher, answer, chunk_all, evaluate, load_data, make_llm

docs, questions = load_data()
chunks = chunk_all(docs)
print(len(docs), "documents,", len(chunks), "chunks,", len(questions), "questions")
```

داده را می‌خواند و سندها را به تکه‌ها می‌شکند.

**باید ببینی:**

```
5 documents, 13 chunks, 15 questions
```

_سلول متنی (Markdown):_

````markdown
## Chunks
One chunk per `##` section; the heading path travels with the text so a chunk never loses its context.
````

_سلول کد 2:_

```python
for c in chunks[:4]:
    print(c["id"], "|", c["heading"], "|", c["text"][:60])
```

چهار تکه‌ی اول با شناسه و عنوان کامل.

**باید ببینی:**

```
payment#0 | Payment > Methods | We accept credit cards, PayPal and bank transfer. We do not 
payment#1 | Payment > Invoices | The invoice is attached to your order confirmation email and
refunds#0 | Refunds > Timing | We send your money back to the original payment method withi
refunds#1 | Refunds > Partial refunds | If an item comes back damaged or used, we may refund only pa
```

_سلول متنی (Markdown):_

````markdown
## Three search methods
BM25 matches exact words; character trigrams survive typos; hybrid fuses both rankings with RRF (ranks only, so the
different score scales do not matter).
````

_سلول کد 3:_

```python
s = Searcher(chunks)
for query in ["how fast is standard delivery", "how fast is standrd delivry"]:
    print(query)
    for method in ["bm25", "trigram", "hybrid"]:
        print(f"  {method:8s}", [c["id"] for c in s.search(query, method)])
```

یک سؤال درست و همان سؤال با غلط املایی. ببین BM25 در دومی چه می‌کند و hybrid چطور جبران می‌کند.

**باید ببینی:**

```
how fast is standard delivery
  bm25     ['shipping#0', 'returns#0', 'shipping#1']
  trigram  ['shipping#0', 'shipping#1', 'returns#0']
  hybrid   ['shipping#0', 'returns#0', 'shipping#1']
how fast is standrd delivry
  bm25     []
  trigram  ['shipping#0', 'shipping#1', 'returns#0']
  hybrid   ['shipping#0', 'shipping#1', 'returns#0']
```

_سلول متنی (Markdown):_

````markdown
## Evaluation
Document-level recall@3 and MRR over the 12 answerable questions. The misses show where each method fails.
````

_سلول کد 4:_

```python
import json, os

results = [evaluate(s, questions, m) for m in ["bm25", "trigram", "hybrid"]]
print(f"{'method':8s} {'recall@3':>9s} {'mrr':>6s}  misses")
for r in results:
    print(f"{r['method']:8s} {r['recall@3']:9.3f} {r['mrr']:6.3f}  {r['misses']}")
os.makedirs("results", exist_ok=True)
with open("results/results.json", "w") as f:
    json.dump(results, f, indent=2)
```

جدول مقایسه‌ی سه روش و ذخیره در `results/results.json` (عددهای README از همین فایل می‌آید).

**باید ببینی:**

```
method    recall@3    mrr  misses
bm25         0.917  0.917  ['how long do I have to send back a sofa']
trigram      1.000  0.944  []
hybrid       1.000  0.944  []
```

_سلول متنی (Markdown):_

````markdown
## Answers with citations
The model sees the top 3 chunks and must cite them as `[id]`. Invented citations are removed; no valid citation
means no answer. `FAQ_PROVIDER` chooses the model: offline (default, no model), ollama, anthropic or opencode.
````

_سلول کد 5:_

```python
llm = make_llm()
abstained_unanswerable = answered_unanswerable = 0
for q in questions:
    out = answer(q["question"], s.search(q["question"], k=3), llm)
    if not q["relevant"]:
        abstained_unanswerable += out["abstained"]
        answered_unanswerable += not out["abstained"]
    shown = "ABSTAIN" if out["abstained"] else out["answer"][:60]
    print(f"{q['question'][:38]:38s} -> {shown}")
print("\nunanswerable questions: answered", answered_unanswerable, "| abstained", abstained_unanswerable)
```

با مدل offline، سؤال‌های بی‌جواب هم جواب می‌گیرند چون جست‌وجو همیشه چیزی پیدا می‌کند و مدل ساختگی همیشه ارجاع می‌دهد. این محدودیت واقعی RAG ساده است؛ پروژه‌ی p22 (Agentic RAG) با نمره‌دهی به شواهد آن را حل می‌کند. با مدل واقعی ببین آیا «I do not know» می‌گوید.

**باید ببینی:**

```
how long do I have to send back a sofa -> We send your money back to the original payment method withi
can I return a personalised mirror     -> You can return most items within 30 days of delivery. Return
how do I start a return                -> Open your order in the account page and choose "Return item"
when do I get my money back            -> We send your money back to the original payment method withi
what if the item comes back damaged    -> If an item comes back damaged or used, we may refund only pa
how fast is standard delivery          -> Standard delivery takes 3 to 5 working days. Express deliver
how much does express shipping cost    -> Shipping is free above 50 EUR. Below that, standard shipping
is there a tracking link               -> You receive a tracking link by email when the parcel leaves 
is a broken table leg covered          -> Furniture has a 2-year warranty against manufacturing defect
how do I claim the warranty            -> Send a photo of the defect and your order number to support.
can I pay with PayPal                  -> We accept credit cards, PayPal and bank transfer. We do not 
where is my invoice                    -> The invoice is attached to your order confirmation email and
can I pay by cheque                    -> The invoice is attached to your order confirmation email and
what is the CEO's phone number         -> Send a photo of the defect and your order number to support.
do you sell gift cards                 -> Refunds for gift orders go to the buyer, not to the recipien

unanswerable questions: answered 3 | abstained 0
```

_سلول متنی (Markdown):_

````markdown
## Limitations
- 15 questions are enough to learn the method, not to compare methods with confidence.
- Plain RAG answers unanswerable questions when retrieval returns something; evidence grading and abstention
  (agentic RAG) are the next step.
- English only; tokenisation is a simple regular expression.
````

> **نکته:** اگر نمی‌خواهی سلول‌ها را یکی‌یکی بسازی: دکمه‌ی **دانلود notebook** پایین همین مرحله فایل آماده را می‌دهد؛ آن را در پوشه‌ی repo بگذار و همه‌ی سلول‌ها را اجرا کن (Run All). ولی یک بار دستی ساختن، کد را بهتر در ذهنت می‌نشاند.

## 11. اجرا با مدل زبانی واقعی (اختیاری)
_VS Code · Ollama / Claude / OpenCode · حدود 10 دقیقه_

**چرا:** مدل `offline` فقط اولین منبع را با شناسه‌اش برمی‌گرداند تا ساختار را ببینی. با مدل واقعی می‌بینی جواب چطور نوشته می‌شود و آیا ارجاع‌ها را رعایت می‌کند.

1. یکی از سه راه را انتخاب کن و در ترمینال VS Code اجرا کن، بعد سلول «جواب‌ها» در notebook را دوباره اجرا کن (اول **Restart** kernel تا متغیر محیطی خوانده شود).

_Ollama (محلی، رایگان) · از ollama.com نصب کن_

```
ollama pull qwen2.5:7b
pip install ollama
$env:FAQ_PROVIDER = "ollama"
```

_Claude (کلید API از console.anthropic.com؛ اشتراک Claude.ai کلید API نیست)_

```
pip install anthropic
$env:ANTHROPIC_API_KEY = "sk-ant-..."     # فقط در ترمینال؛ هرگز در فایل یا notebook
$env:FAQ_PROVIDER = "anthropic"
```

_OpenCode (اگر نصب داری و وارد یک provider شده‌ای)_

```
opencode models
$env:FAQ_PROVIDER = "opencode"
```

> **حواست باشد:** کلید API را هرگز در notebook یا فایل‌های repo ننویس. اگر اشتباهاً push شد، فوراً در Console باطلش کن؛ پاک کردن commit کافی نیست. در Mac/Linux به‌جای `$env:X = "y"` بنویس `export X=y`.

## 12. commit و push از VS Code
_VS Code · GitHub · حدود 3 دقیقه_

**چرا:** notebook با خروجی‌هایش و فایل نتایج باید در GitHub باشند تا بدون اجرا دیده شوند.

1. پنل Source Control: `Ctrl+Shift+G`. فایل‌های `01_faq_search.ipynb` و `results/results.json` را می‌بینی.
2. پیام: `Add notebook with search comparison and grounded answers` → **Commit** → **Sync Changes**.

> **باید ببینی:** در GitHub، `01_faq_search.ipynb` را باز کن: جدول‌ها و خروجی‌ها بدون اجرا دیده می‌شوند. تب Actions دوباره سبز است.

> **حواست باشد:** قانون ساده: قبل از هر کار در VS Code اول **Pull** بزن، و یک فایل را هم‌زمان در GitHub و VS Code ویرایش نکن.

## 13. README نهایی
_GitHub · حدود 10 دقیقه_

**چرا:** README صفحه‌ی اول پروژه است. باید در ۳۰ ثانیه بگوید: چه مسئله‌ای، چه روشی، چه عددی، و محدودیت‌ها چیست. عددها را از `results/results.json` خودت بردار، نه از این صفحه.

1. در GitHub روی `README.md` → آیکون مداد → همه‌ی متن را با متن زیر عوض کن و عددهای داخل `{...}` را با عددهای خودت پر کن. commit: `Write README`.
2. نام کاربری‌ات را در خط badge جایگزین کن.

````markdown
# FAQ search with grounded answers

![tests](https://github.com/<your-user>/faq_search/actions/workflows/tests.yml/badge.svg)

Customer questions are answered from a shop's FAQ pages. Search is built from scratch and measured on labelled questions;
answers must cite their sources or abstain.

## What it does
- **Chunking** by markdown section, keeping the heading path (`Returns > Return window`) with every chunk.
- **Search**: BM25 (exact words), character trigrams (typos), and a **hybrid** that fuses both with Reciprocal Rank Fusion.
- **Evaluation**: recall@3 and MRR on 12 answerable questions; 3 more questions have no answer on purpose.
- **Grounded answers**: the model sees the top 3 chunks and must cite them; invented citations are removed and an
  answer without a valid citation is not returned.
- Any model through one function: offline (no model), Ollama, Claude API or OpenCode (`FAQ_PROVIDER`).

## Results (`results/results.json`)
| method | recall@3 | MRR |
|---|---|---|
| BM25 | {bm25_recall} | {bm25_mrr} |
| trigram | {trigram_recall} | {trigram_mrr} |
| hybrid (RRF) | {hybrid_recall} | {hybrid_mrr} |

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Then open `01_faq_search.ipynb` and run all cells.

## Limitations
- 15 labelled questions: enough to learn and compare roughly, not to claim small differences.
- Plain RAG still answers unanswerable questions when retrieval returns something; evidence grading and abstention
  (agentic RAG) is the next step.
- English only, regular-expression tokenisation.

## Licence
MIT
````

## 14. صیقل نهایی repo
_GitHub · حدود 5 دقیقه_

**چرا:** جزئیات کوچکی که repo را حرفه‌ای نشان می‌دهد.

1. صفحه‌ی repo → آیکون چرخ‌دنده کنار **About** → Topics: `information-retrieval`, `bm25`, `rag`, `llm`, `python`.
2. در پروفایل GitHub: **Customize your pins** → این repo را pin کن.
3. یک خط رزومه از جدول نتایج بنویس (پایین همین مرحله).

**خط رزومه:** Built an FAQ search engine from scratch (markdown chunking, BM25, typo-tolerant trigram search fused with RRF) with recall@3 {recall} / MRR {mrr} on labelled questions, and LLM answers that cite their sources or abstain; tested with pytest and GitHub Actions.

## اگر به خطا خوردی
- **`python` شناخته نمی‌شود**: Python را با تیک «Add to PATH» نصب کن، یا به‌جای `python` بنویس `py`.
- **`No module named faq_search` در notebook**: notebook باید در همان پوشه‌ی `faq_search.py` باشد و kernel روی `.venv` باشد (بالا سمت راست).
- **`FileNotFoundError: data/faq.json`**: فایل داده را در مرحله‌ی ۴ با مسیر دقیق `data/faq.json` ساخته‌ای؟ notebook را از پوشه‌ی repo اجرا کن.
- **تب Actions قرمز است**: روی اجرای قرمز کلیک کن؛ معمولاً یک فایل با نام یا مسیر اشتباه ساخته شده (مثلاً `test/` به‌جای `tests/`).
- **`ConnectionError` با Ollama**: Ollama را اجرا کن (آیکونش کنار ساعت) و `ollama list` را بزن.
- **Claude خطای 401 می‌دهد**: کلید API اشتباه یا تمام شده؛ اشتراک Claude.ai کلید API نیست.

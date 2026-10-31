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

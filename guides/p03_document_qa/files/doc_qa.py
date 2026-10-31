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

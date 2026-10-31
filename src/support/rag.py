"""Stage 2: answering policy questions from the store's documents, with citations.

The corpus is small (12 documents, two languages), so the interesting parts are not scale but:
chunking with context, hybrid retrieval, answering only from sources, and checking the answer.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np

from .config import POLICY_DIR
from .guardrails import allowed_numbers, check_output

_TOKEN = re.compile(r"[a-zA-ZäöüÄÖÜß0-9]+")


@dataclass
class Chunk:
    chunk_id: str      # e.g. "returns#2"
    doc_id: str
    lang: str
    title: str
    text: str

    @property
    def indexed_text(self) -> str:
        # The title travels with every paragraph: "30 days" alone does not say *what* is 30 days.
        return f"{self.title}. {self.text}"


def load_chunks(langs=("en", "de")) -> list[Chunk]:
    chunks = []
    for lang in langs:
        for path in sorted((POLICY_DIR / lang).glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            meta_block, body = raw.split("---", 2)[1:]
            meta = dict(line.split(": ", 1) for line in meta_block.strip().splitlines())
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.startswith("#")]
            for i, p in enumerate(paragraphs, 1):
                chunks.append(Chunk(f"{meta['id']}#{i}", meta["id"], lang, meta["title"], p.replace("**", "")))
    return chunks


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


class BM25:
    """Okapi BM25 written out, so every term of the formula is visible.

    score(q, d) = sum over query terms t of
        idf(t) * tf(t,d) * (k1 + 1) / (tf(t,d) + k1 * (1 - b + b * |d| / avgdl))
    """

    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tfs = [Counter(tokenize(d)) for d in docs]
        self.lens = np.array([sum(tf.values()) for tf in self.tfs], float)
        self.avgdl = self.lens.mean()
        df = Counter(t for tf in self.tfs for t in tf)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> np.ndarray:
        s = np.zeros(len(self.tfs))
        for t in tokenize(query):
            if t not in self.idf:
                continue
            tf = np.array([d.get(t, 0) for d in self.tfs], float)
            s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.lens / self.avgdl))
        return s


def rrf(rankings: list[list[int]], k: int = 60) -> list[int]:
    """Reciprocal Rank Fusion: combine rankings using only positions, so scores on different scales can be merged."""
    score = Counter()
    for ranking in rankings:
        for pos, idx in enumerate(ranking):
            score[idx] += 1 / (k + pos + 1)
    return [idx for idx, _ in score.most_common()]


class Retriever:
    def __init__(self, chunks: list[Chunk], encoder=None, k1: float = 1.5, b: float = 0.75, rrf_k: int = 60):
        """encoder: any object with .encode(list[str], normalize_embeddings=True) (sentence-transformers)."""
        self.chunks = chunks
        self.bm25 = BM25([c.indexed_text for c in chunks], k1=k1, b=b)
        self.rrf_k = rrf_k
        self.encoder = encoder
        self.emb = (encoder.encode([c.indexed_text for c in chunks], normalize_embeddings=True)
                    if encoder is not None else None)

    def search(self, query: str, lang: str | None = None, k: int = 3, mode: str = "hybrid") -> list[Chunk]:
        allowed = np.array([lang is None or c.lang == lang for c in self.chunks])
        rankings = []
        if mode in ("bm25", "hybrid"):
            s = np.where(allowed, self.bm25.scores(query), -np.inf)
            rankings.append([i for i in np.argsort(-s) if allowed[i]])
        if mode in ("dense", "hybrid") and self.emb is not None:
            q = self.encoder.encode([query], normalize_embeddings=True)[0]
            s = np.where(allowed, self.emb @ q, -np.inf)
            rankings.append([i for i in np.argsort(-s) if allowed[i]])
        order = rankings[0] if len(rankings) == 1 else rrf(rankings, self.rrf_k)
        return [self.chunks[i] for i in order[:k]]


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {"answerable": {"type": "boolean"}, "answer": {"type": "string"},
                   "citations": {"type": "array", "items": {"type": "string"}}},
    "required": ["answerable", "answer", "citations"],
}


def answer_question(llm, question: str, chunks: list[Chunk], lang: str) -> dict:
    sources = "\n\n".join(f"[{c.chunk_id}] {c.indexed_text}" for c in chunks)
    prompt = (f"Answer the customer's question using ONLY the sources. Answer in "
              f"{'German' if lang == 'de' else 'English'}, in 1-3 sentences.\n"
              f"Cite the source ids you used. If the sources do not answer the question, "
              f"set answerable=false.\n\nSources:\n{sources}\n\nQuestion: {question}")
    out = llm.json([{"role": "user", "content": prompt}], ANSWER_SCHEMA)
    ids = {c.chunk_id for c in chunks}
    out["citations_valid"] = bool(out["citations"]) and set(out["citations"]) <= ids
    verdict = check_output(out["answer"], allowed_numbers({"s": sources}, {"q": question}))
    out["numbers_supported"] = verdict.ok
    out["ok"] = out["answerable"] and out["citations_valid"] and verdict.ok
    return out


def make_policy_answerer(llm, retriever: Retriever, k: int = 3, mode: str = "hybrid"):
    """The function the agent calls on the RAG route. Returns no answer when any check fails -> handoff."""
    def answer(question: str, lang: str) -> dict:
        out = answer_question(llm, question, retriever.search(question, lang, k, mode), lang)
        return {"answer": out["answer"] if out["ok"] else None, "sources": out["citations"]}
    return answer


# ---------- retrieval evaluation ----------

def retrieval_metrics(retriever: Retriever, qa: list[dict], k: int = 3, mode: str = "hybrid") -> dict:
    """recall@k: gold document among the top k. MRR: 1 / rank of the first gold chunk."""
    hits, rr = [], []
    for item in qa:
        ranked = retriever.search(item["question"], item["lang"], k=len(retriever.chunks), mode=mode)
        docs = [c.doc_id for c in ranked]
        rank = docs.index(item["doc"]) + 1 if item["doc"] in docs else None
        hits.append(rank is not None and rank <= k)
        rr.append(1 / rank if rank else 0.0)
    return {"mode": mode, f"recall@{k}": float(np.mean(hits)), "mrr": float(np.mean(rr)), "n": len(qa)}

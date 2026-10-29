"""Step 4: character-trigram search and Reciprocal Rank Fusion."""
from __future__ import annotations

import math
import re
from collections import Counter


def trigrams(text: str) -> set[str]:
    out: set[str] = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        p = f" {w} "
        out |= {p[i:i + 3] for i in range(len(p) - 2)}
    return out


def trigram_rank(query: str, texts: list[str]) -> list[int]:
    q = trigrams(query)
    sims = []
    for t in texts:
        g = trigrams(t)
        sims.append(len(q & g) / len(q | g) if q | g else 0.0)
    return [i for i in sorted(range(len(texts)), key=lambda i: (-sims[i], i)) if sims[i] > 0]


def rrf(rankings: list[list[int]], k: int = 60) -> list[int]:
    score: dict[int, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            score[doc] = score.get(doc, 0.0) + 1 / (k + rank)
    return sorted(score, key=lambda d: (-score[d], d))


def hybrid(query: str, bm25, texts: list[str], top: int = 3) -> list[int]:
    return rrf([bm25.search(query, k=len(texts)), trigram_rank(query, texts)])[:top]


# ---- helper so the demo below runs: a compact BM25 (you wrote the real one in step 2) ----
class SimpleBM25:
    def __init__(self, docs):
        self.toks = [re.findall(r"[a-z0-9]+", d.lower()) for d in docs]
        self.df = Counter(w for t in self.toks for w in set(t))
        self.n, self.avg = len(docs), sum(map(len, self.toks)) / max(len(docs), 1)

    def search(self, query, k=3):
        q = re.findall(r"[a-z0-9]+", query.lower())
        sc = []
        for t in self.toks:
            tf = Counter(t)
            s = 0.0
            for w in q:
                if tf[w]:
                    idf = math.log(1 + (self.n - self.df[w] + .5) / (self.df[w] + .5))
                    s += idf * tf[w] * 2.5 / (tf[w] + 1.5 * (.25 + .75 * len(t) / self.avg))
            sc.append(s)
        return [i for i in sorted(range(self.n), key=lambda i: (-sc[i], i)) if sc[i] > 0][:k]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from learn.data import faq_docs, faq_questions
    texts, owner = [], []
    for name, doc in faq_docs().items():
        for part in doc.split("\n## ")[1:]:
            texts.append(part), owner.append(name)
    bm = SimpleBM25(texts)
    qs = faq_questions() + [{"question": "how fast is standrd delivry", "relevant": "shipping", "answerable": "yes"}]
    for label, fn in [("bm25", lambda q: bm.search(q, k=len(texts))), ("trigram", lambda q: trigram_rank(q, texts)),
                      ("hybrid", lambda q: hybrid(q, bm, texts, top=len(texts)))]:
        hit = [q for q in qs if q["relevant"] and q["relevant"] in {owner[i] for i in fn(q["question"])[:3]}]
        print(f"{label:8s} recall@3 = {len(hit) / sum(1 for q in qs if q['relevant']):.2f}")

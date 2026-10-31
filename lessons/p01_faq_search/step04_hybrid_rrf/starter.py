"""Step 4: character-trigram search and Reciprocal Rank Fusion."""
from __future__ import annotations

import math
import re
from collections import Counter


def trigrams(text: str) -> set[str]:
    # TODO 1: for every word of the lowercase text, pad it as f" {word} " and collect all 3-character windows
    raise NotImplementedError("TODO 1: trigrams")


def trigram_rank(query: str, texts: list[str]) -> list[int]:
    # TODO 2: Jaccard similarity |A & B| / |A | B| between trigrams(query) and each text; indices by similarity
    #         descending, ties by smaller index, similarity 0 excluded
    raise NotImplementedError("TODO 2: trigram ranking")


def rrf(rankings: list[list[int]], k: int = 60) -> list[int]:
    # TODO 3: score(doc) = sum over rankings of 1 / (k + rank), rank starting at 1; only docs that appear somewhere;
    #         best first, ties by smaller index
    raise NotImplementedError("TODO 3: reciprocal rank fusion")


def hybrid(query: str, bm25, texts: list[str], top: int = 3) -> list[int]:
    # TODO 4: ranking from bm25.search(query, k=len(texts)) and from trigram_rank, fused with rrf, first `top`
    raise NotImplementedError("TODO 4: hybrid search")


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

"""Step 2: BM25 from scratch."""
from __future__ import annotations

import math
import re
from collections import Counter

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "and", "or", "in", "on", "for", "can", "how", "what",
        "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that"}


def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        toks = [tokenize(d) for d in docs]
        self.tf = [Counter(t) for t in toks]
        self.len = [len(t) for t in toks]
        self.n = len(docs)
        self.avg = sum(self.len) / self.n if self.n else 0.0
        self.df = Counter(w for t in toks for w in set(t))

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def scores(self, query: str) -> list[float]:
        out = [0.0] * self.n
        for term in tokenize(query):
            if self.df.get(term, 0) == 0:
                continue
            idf = self.idf(term)
            for i in range(self.n):
                tf = self.tf[i].get(term, 0)
                if tf:
                    out[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        return out

    def search(self, query: str, k: int = 3) -> list[int]:
        s = self.scores(query)
        return [i for i in sorted(range(self.n), key=lambda i: (-s[i], i)) if s[i] > 0][:k]

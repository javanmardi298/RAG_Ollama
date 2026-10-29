"""Step 2: BM25 from scratch."""
from __future__ import annotations

import math
import re
from collections import Counter

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "and", "or", "in", "on", "for", "can", "how", "what",
        "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that"}


def tokenize(text: str) -> list[str]:
    # TODO 1: lowercase, keep only letters/digits (re.findall(r"[a-z0-9]+", ...)) and drop the words in STOP
    raise NotImplementedError("TODO 1: tokenize")


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        # TODO 2: self.tf = one Counter of tokens per doc; self.len = token count per doc; self.avg = mean length;
        #         self.df = Counter: in how many docs each token appears (count each doc once per token); self.n = number of docs
        raise NotImplementedError("TODO 2: index the documents")

    def idf(self, term: str) -> float:
        # TODO 3: ln(1 + (N - df + 0.5) / (df + 0.5))
        raise NotImplementedError("TODO 3: idf")

    def scores(self, query: str) -> list[float]:
        # TODO 4: for every doc add idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len / avg)) for each query token
        #         that appears in the corpus (df > 0). Return one float per doc.
        raise NotImplementedError("TODO 4: score every document")

    def search(self, query: str, k: int = 3) -> list[int]:
        # TODO 5: indices of the k best documents, best first, ties by smaller index, score 0 excluded
        raise NotImplementedError("TODO 5: top-k")

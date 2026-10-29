"""Step 3: retrieval metrics."""
from __future__ import annotations


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(ranked[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for i, doc in enumerate(ranked):
        if doc in relevant:
            return 1 / (i + 1)
    return 0.0


def evaluate(search, questions: list[dict], k: int = 3) -> dict:
    rec, rr, misses = [], [], []
    for q in questions:
        if not q["relevant"]:
            continue
        ranked = list(dict.fromkeys(search(q["question"])))
        rel = {q["relevant"]}
        r = recall_at_k(ranked, rel, k)
        rec.append(r)
        rr.append(reciprocal_rank(ranked, rel))
        if r == 0:
            misses.append(q["question"])
    n = len(rec)
    return {f"recall@{k}": sum(rec) / n if n else 0.0, "mrr": sum(rr) / n if n else 0.0, "misses": misses, "n": n}

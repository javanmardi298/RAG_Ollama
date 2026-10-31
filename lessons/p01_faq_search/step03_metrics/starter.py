"""Step 3: retrieval metrics."""
from __future__ import annotations


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    # TODO 1: fraction of `relevant` that appears in ranked[:k]; 0.0 when relevant is empty
    raise NotImplementedError("TODO 1: recall@k")


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    # TODO 2: 1 / (rank of the first relevant item), rank starting at 1; 0.0 if none
    raise NotImplementedError("TODO 2: reciprocal rank")


def evaluate(search, questions: list[dict], k: int = 3) -> dict:
    """search(question) -> ranked list of doc ids (may contain duplicates).
    questions: [{"question": str, "relevant": "returns" or ""}] ("" = unanswerable, skip it)."""
    # TODO 3: for every answerable question: dedupe the ranking keeping first occurrences, compute both metrics,
    #         collect the question text in `misses` when recall@k == 0. Return the means.
    raise NotImplementedError("TODO 3: evaluate")

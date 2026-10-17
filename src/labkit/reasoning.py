"""Test-time compute patterns that are cheap to add and easy to measure.

* self_consistency: sample n answers at temperature > 0 and take the majority. Agreement is also a free
  confidence signal (low agreement -> hand off / ask), which connects to the decision layer in stage 4.
* best_of_n with a verifier: generate n, keep the one a checker (code or a validated judge) scores highest.
Both multiply cost by n: report accuracy AND cost per answer, and stop when the curve flattens.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable


def self_consistency(generate: Callable[[], str], n: int = 5, normalize: Callable[[str], str] = lambda s: s.strip().lower()):
    """Returns (majority answer, agreement share, all normalized answers)."""
    answers = [normalize(generate()) for _ in range(n)]
    counts = Counter(a for a in answers if a)
    if not counts:
        return None, 0.0, answers
    top, c = counts.most_common(1)[0]
    return top, c / n, answers


def best_of_n(generate: Callable[[], str], score: Callable[[str], float], n: int = 4):
    """Returns (best candidate, its score, all (candidate, score) pairs)."""
    cands = [(g, score(g)) for g in (generate() for _ in range(n))]
    best = max(cands, key=lambda x: x[1])
    return best[0], best[1], cands

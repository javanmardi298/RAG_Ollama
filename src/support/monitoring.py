"""Stage 8: traces, latency and drift.

Drift = the live traffic no longer looks like the data we evaluated on. We watch three signals:
* the intent mix (new campaign -> many more refund questions),
* the classifier's confidence (new kinds of messages -> lower confidence),
* outcome rates (handoff rate jumping is often the first visible symptom).
"""
from __future__ import annotations

import json
import threading
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import chi2_contingency


class TraceWriter:
    """Append-only JSONL log. Callers pass already-masked text (guardrails.mask_pii)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def __call__(self, event: dict) -> None:
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]


def latency_summary(latencies_s) -> dict:
    x = np.asarray(latencies_s, float)
    return {"n": int(len(x)), "p50_ms": float(np.percentile(x, 50) * 1000),
            "p95_ms": float(np.percentile(x, 95) * 1000), "p99_ms": float(np.percentile(x, 99) * 1000)}


def psi(reference: dict[str, float], current: dict[str, float], eps: float = 1e-4) -> float:
    """Population Stability Index between two category distributions.

    PSI = sum (cur - ref) * ln(cur / ref). Rule of thumb: < 0.1 stable, 0.1-0.25 watch, > 0.25 investigate.
    """
    keys = set(reference) | set(current)
    ref = np.array([reference.get(k, 0) for k in keys], float) + eps
    cur = np.array([current.get(k, 0) for k in keys], float) + eps
    ref, cur = ref / ref.sum(), cur / cur.sum()
    return float(np.sum((cur - ref) * np.log(cur / ref)))


def binned_distribution(values, bins=np.linspace(0, 1, 11)) -> dict[str, float]:
    counts, _ = np.histogram(np.clip(values, 0, 1), bins=bins)
    return {f"{bins[i]:.1f}": c / max(counts.sum(), 1) for i, c in enumerate(counts)}


def intent_drift(reference_intents: list[str], current_intents: list[str]) -> dict:
    ref, cur = Counter(reference_intents), Counter(current_intents)
    keys = sorted(set(ref) | set(cur))
    table = np.array([[ref.get(k, 0) for k in keys], [cur.get(k, 0) for k in keys]]) + 1
    _, p, _, _ = chi2_contingency(table)
    n_ref, n_cur = sum(ref.values()), sum(cur.values())
    share = {k: (cur.get(k, 0) / n_cur) - (ref.get(k, 0) / n_ref) for k in keys}
    return {"psi": psi({k: v / n_ref for k, v in ref.items()}, {k: v / n_cur for k, v in cur.items()}),
            "chi2_p": float(p),
            "biggest_changes": dict(sorted(share.items(), key=lambda kv: -abs(kv[1]))[:5])}


def drift_report(reference: list[dict], current: list[dict]) -> dict:
    """Compare two windows of traces (each trace has intent, confidence, route)."""
    rep = intent_drift([t["intent"] for t in reference if t.get("intent")],
                       [t["intent"] for t in current if t.get("intent")])
    if all("confidence" in t for t in reference + current):
        rep["confidence_psi"] = psi(binned_distribution([t["confidence"] for t in reference]),
                                    binned_distribution([t["confidence"] for t in current]))
    rate = lambda ts: np.mean([t.get("route") == "handoff" for t in ts]) if ts else 0.0  # noqa: E731
    rep["handoff_rate"] = {"reference": float(rate(reference)), "current": float(rate(current))}
    rep["alert"] = rep["psi"] > 0.25 or rep.get("confidence_psi", 0) > 0.25 or \
        rep["handoff_rate"]["current"] > 1.5 * max(rep["handoff_rate"]["reference"], 0.01)
    return rep

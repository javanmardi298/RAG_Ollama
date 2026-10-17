"""Evaluation metrics used across the presets: retrieval (binary and graded) and structured extraction."""
from __future__ import annotations

import math
import re
import unicodedata
from math import comb


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return len(set(ranked[:k]) & relevant) / len(relevant) if relevant else 0.0


def precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return len(set(ranked[:k]) & relevant) / k if k else 0.0


def hit_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return float(bool(set(ranked[:k]) & relevant))


def mrr(ranked: list[str], relevant: set[str]) -> float:
    return next((1 / (i + 1) for i, d in enumerate(ranked) if d in relevant), 0.0)


def ndcg_at_k(ranked: list[str], gains: dict[str, float], k: int) -> float:
    """Graded relevance (e.g. WANDS: exact=2, partial=1, irrelevant=0). gain = 2^rel - 1, log2 discount."""
    dcg = sum((2 ** gains.get(d, 0) - 1) / math.log2(i + 2) for i, d in enumerate(ranked[:k]))
    ideal = sorted(gains.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def retrieval_report(runs: list[tuple[list[str], set[str]]], k: int = 5) -> dict:
    """runs: (ranked doc ids, relevant ids) per query."""
    n = len(runs) or 1
    return {f"recall@{k}": sum(recall_at_k(r, g, k) for r, g in runs) / n,
            f"hit@{k}": sum(hit_at_k(r, g, k) for r, g in runs) / n,
            "mrr": sum(mrr(r, g) for r, g in runs) / n, "n": len(runs)}


# ---------- reliability over repeated trials (agents) ----------

def pass_at_k(n: int, c: int, k: int) -> float:
    """Chance that at least one of k attempts succeeds, from n trials with c successes (unbiased)."""
    if k > n:
        raise ValueError("k must be <= n")
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench): chance that ALL k attempts succeed. What a customer meeting the agent k times
    experiences; it falls fast when the agent is only sometimes right, even if pass@1 looks fine."""
    if k > n:
        raise ValueError("k must be <= n")
    return comb(c, k) / comb(n, k)


def reliability_report(successes: dict[str, list[bool]]) -> dict:
    """successes: task id -> list of outcomes over repeated runs (same number per task). Mean over tasks."""
    if not successes:
        return {}
    n = min(len(v) for v in successes.values())
    out = {}
    for k in range(1, n + 1):
        out[f"pass^{k}"] = sum(pass_hat_k(n, sum(v[:n]), k) for v in successes.values()) / len(successes)
        out[f"pass@{k}"] = sum(pass_at_k(n, sum(v[:n]), k) for v in successes.values()) / len(successes)
    out["n_tasks"], out["trials"] = len(successes), n
    return out


# ---------- structured extraction ----------

def normalize_value(v) -> str:
    """Compare values the way a human would: case, accents, spacing, thousands separators, trailing zeros."""
    if v is None:
        return ""
    s = unicodedata.normalize("NFKC", str(v)).strip().lower()
    s = re.sub(r"\s+", " ", s)
    if re.fullmatch(r"[-+]?[\d.,]+", s):
        digits = s.replace(",", "") if s.count(".") <= 1 and ("," not in s or s.rfind(",") < s.rfind(".")) \
            else s.replace(".", "").replace(",", ".")
        try:
            s = f"{float(digits):.2f}"
        except ValueError:
            pass
    return s


def field_scores(pred: dict, gold: dict) -> dict:
    """Per field: tp (correct), fp (predicted but wrong or not in gold), fn (gold field missed)."""
    out = {}
    for f in set(pred) | set(gold):
        p, g = normalize_value(pred.get(f)), normalize_value(gold.get(f))
        out[f] = {"tp": int(bool(p) and p == g), "fp": int(bool(p) and p != g), "fn": int(bool(g) and p != g)}
    return out


def extraction_report(pairs: list[tuple[dict, dict]]) -> dict:
    """Micro precision/recall/F1 over all fields, per-field F1, and document-level exact match."""
    tot = {"tp": 0, "fp": 0, "fn": 0}
    per: dict[str, dict] = {}
    exact = 0
    for pred, gold in pairs:
        fs = field_scores(pred, gold)
        exact += all(v["fp"] == 0 and v["fn"] == 0 for v in fs.values())
        for f, v in fs.items():
            per.setdefault(f, {"tp": 0, "fp": 0, "fn": 0})
            for key in tot:
                tot[key] += v[key]; per[f][key] += v[key]

    def prf(c):
        p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0
        r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0
        return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0}

    return {**prf(tot), "exact_match": exact / len(pairs) if pairs else 0.0, "n": len(pairs),
            "per_field": {f: prf(c)["f1"] for f, c in sorted(per.items())}}

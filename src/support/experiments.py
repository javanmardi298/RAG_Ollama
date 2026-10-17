"""Stage 9: A/B experiments done properly.

* Deterministic assignment: hash(session_id) -> arm. Same user, same arm, no database needed.
* Sample size BEFORE the test: how many conversations to detect the change we care about.
* Sample ratio mismatch (SRM) check: if a 50/50 split comes out 53/47, assignment is broken; do not read results.
* Two-proportion z-test on the primary metric, plus guardrail metrics that must not get worse.
"""
from __future__ import annotations

import hashlib
import math

from scipy.stats import chisquare, norm


def assign(session_id: str, experiment: str, arms=("control", "treatment"), weights=(0.5, 0.5)) -> str:
    """Stable bucketing: the experiment name is part of the hash so different experiments are independent."""
    h = int(hashlib.sha256(f"{experiment}:{session_id}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    edge = 0.0
    for arm, w in zip(arms, weights):
        edge += w
        if h <= edge:
            return arm
    return arms[-1]


def sample_size_per_arm(p_base: float, min_detectable_lift: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Conversations per arm to detect an absolute change of `min_detectable_lift` in a rate."""
    p2 = p_base + min_detectable_lift
    z_a, z_b = norm.ppf(1 - alpha / 2), norm.ppf(power)
    p_bar = (p_base + p2) / 2
    n = ((z_a * math.sqrt(2 * p_bar * (1 - p_bar)) + z_b * math.sqrt(p_base * (1 - p_base) + p2 * (1 - p2))) ** 2
         / (p2 - p_base) ** 2)
    return math.ceil(n)


def srm_check(counts: dict[str, int], weights: dict[str, float] | None = None, threshold: float = 0.001) -> dict:
    arms = list(counts)
    total = sum(counts.values())
    weights = weights or {a: 1 / len(arms) for a in arms}
    _, p = chisquare([counts[a] for a in arms], [total * weights[a] for a in arms])
    return {"p_value": float(p), "mismatch": bool(p < threshold)}


def two_proportion_test(success_a: int, n_a: int, success_b: int, n_b: int) -> dict:
    p_a, p_b = success_a / n_a, success_b / n_b
    pooled = (success_a + success_b) / (n_a + n_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = (p_b - p_a) / se if se else 0.0
    se_diff = math.sqrt(p_a * (1 - p_a) / n_a + p_b * (1 - p_b) / n_b)
    return {"rate_a": p_a, "rate_b": p_b, "diff": p_b - p_a, "z": z,
            "p_value": float(2 * (1 - norm.cdf(abs(z)))),
            "ci95": (p_b - p_a - 1.96 * se_diff, p_b - p_a + 1.96 * se_diff)}


def readout(arms: dict[str, dict], primary: str, guardrails: dict[str, float]) -> dict:
    """arms: {"control": {"n": .., "automated": .., "false_automation": ..}, "treatment": {...}}.

    Ship only if the primary metric improves significantly AND no guardrail metric gets worse
    by more than its allowed margin.
    """
    srm = srm_check({a: v["n"] for a, v in arms.items()})
    c, t = arms["control"], arms["treatment"]
    main = two_proportion_test(c[primary], c["n"], t[primary], t["n"])
    checks = {}
    for metric, max_increase in guardrails.items():
        res = two_proportion_test(c[metric], c["n"], t[metric], t["n"])
        checks[metric] = {**res, "ok": res["ci95"][1] <= max_increase}
    ship = (not srm["mismatch"]) and main["p_value"] < 0.05 and main["diff"] > 0 and all(v["ok"] for v in checks.values())
    return {"srm": srm, "primary": main, "guardrails": checks, "ship": ship}

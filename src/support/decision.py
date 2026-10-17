"""Stage 4: when may the bot act alone, when must it ask, when must a human take over.

Two parts:
1. `decide()` turns intent, confidence, risk and red flags into one of five actions.
2. Threshold tuning on the dev set: pick confidence thresholds from data, not from gut feeling.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from .config import intent_map, rules


class Action(str, Enum):
    AUTO = "auto"            # answer / act without asking
    CONFIRM = "confirm"      # act only after the customer says yes
    CLARIFY = "clarify"      # ask a question, the bot is not sure what is meant
    HANDOFF = "handoff"      # a human takes over
    DECLINE = "decline"      # out of scope, polite redirect


# Minimum confidence per risk level. Defaults; tune them on dev with `choose_threshold`.
DEFAULT_THRESHOLDS = {"low": 0.50, "medium": 0.70, "high": 0.85}
RED_FLAGS = {"human_request", "legal_threat", "account_security"}


@dataclass
class DecisionInput:
    intent: str
    confidence: float
    flags: tuple[str, ...] = ()
    failed_turns: int = 0
    clarifications_asked: int = 0


def decide(x: DecisionInput, thresholds: dict | None = None) -> tuple[Action, str]:
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    if RED_FLAGS & set(x.flags):
        return Action.HANDOFF, "red_flag:" + ",".join(sorted(RED_FLAGS & set(x.flags)))
    if x.failed_turns >= rules()["handoff"]["max_failed_turns"]:
        return Action.HANDOFF, "too_many_failed_turns"

    info = intent_map().get(x.intent, {"route": "out_of_scope", "risk": "low"})
    if x.intent == "oos":
        info = {"route": "out_of_scope", "risk": "low"}
    if x.confidence < thresholds[info["risk"]]:
        # Ask once; if still unclear, a human is cheaper than a wrong action.
        if x.clarifications_asked == 0:
            return Action.CLARIFY, "low_confidence"
        return Action.HANDOFF, "still_unclear"

    if info["route"] == "handoff":
        return Action.HANDOFF, "intent_needs_human"
    if info["route"] == "out_of_scope":
        return Action.DECLINE, "out_of_scope"
    if info["risk"] == "high":
        return Action.CONFIRM, "high_risk_action"
    return Action.AUTO, "confident"


# ---------- threshold tuning (selective classification) ----------

def risk_coverage(confidence: np.ndarray, correct: np.ndarray) -> list[dict]:
    """For every threshold: how many cases the bot keeps (coverage) and how many of those are wrong (risk)."""
    confidence, correct = np.asarray(confidence), np.asarray(correct, bool)
    rows = []
    for t in np.unique(np.round(confidence, 3)):
        keep = confidence >= t
        if keep.sum() == 0:
            continue
        rows.append({"threshold": float(t), "coverage": float(keep.mean()),
                     "error": float(1 - correct[keep].mean()), "n_kept": int(keep.sum())})
    return rows


def choose_threshold(confidence, correct, max_error: float) -> dict:
    """Lowest threshold (= highest coverage) whose error on the kept cases is at most `max_error`."""
    ok = [r for r in risk_coverage(confidence, correct) if r["error"] <= max_error]
    if not ok:
        return {"threshold": 1.01, "coverage": 0.0, "error": 0.0, "n_kept": 0}
    return min(ok, key=lambda r: r["threshold"])


def choose_threshold_by_cost(confidence, correct, cost_wrong: float, cost_handoff: float) -> dict:
    """Alternative: minimise expected cost. Wrong automation costs `cost_wrong`, each handoff `cost_handoff`."""
    best = None
    for r in risk_coverage(confidence, correct):
        cost = r["coverage"] * r["error"] * cost_wrong + (1 - r["coverage"]) * cost_handoff
        if best is None or cost < best["cost"]:
            best = {**r, "cost": cost}
    return best

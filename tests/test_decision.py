import numpy as np

from support.decision import Action, DecisionInput, choose_threshold, decide


def test_red_flags_win():
    assert decide(DecisionInput("track_order", 0.99, ("legal_threat",)))[0] is Action.HANDOFF


def test_high_risk_needs_confirmation():
    assert decide(DecisionInput("cancel_order", 0.95))[0] is Action.CONFIRM
    assert decide(DecisionInput("track_order", 0.95))[0] is Action.AUTO


def test_low_confidence_asks_then_hands_off():
    assert decide(DecisionInput("cancel_order", 0.6))[0] is Action.CLARIFY
    assert decide(DecisionInput("cancel_order", 0.6, clarifications_asked=1))[0] is Action.HANDOFF


def test_tuned_thresholds_are_used():
    assert decide(DecisionInput("track_order", 0.55), {"low": 0.6})[0] is Action.CLARIFY


def test_choose_threshold_respects_error_budget():
    conf = np.array([0.95, 0.9, 0.8, 0.7, 0.6, 0.5])
    correct = np.array([1, 1, 1, 0, 1, 0], bool)
    t = choose_threshold(conf, correct, max_error=0.0)
    assert t["threshold"] == 0.8 and t["coverage"] == 0.5

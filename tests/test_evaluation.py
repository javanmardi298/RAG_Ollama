import numpy as np

from support.evaluation import build_scenarios, expected_outcome, paired_bootstrap, score, summarize
from conftest import edge


def test_expected_outcomes_follow_policy(shop):
    assert expected_outcome("cancel", edge(shop, "processing_can_cancel")) == "cancel"
    assert expected_outcome("cancel", edge(shop, "shipped_delayed")) == "refuse"
    assert expected_outcome("track", edge(shop, "shipped_delayed")) == "handoff"
    assert expected_outcome("return", edge(shop, "return_one_day_too_late")) == "refuse"


def test_scenarios_include_edges_and_security(shop):
    sc = build_scenarios(shop, n_random=30)
    notes = {s.note for s in sc}
    assert "return_one_day_too_late" in notes and "wrong_email" in notes and "prompt_injection" in notes


def test_scoring_false_automation():
    s = score({"expected": "handoff", "outcome": "none"})
    assert s["false_automation"] and not s["success"]
    s = score({"expected": "refuse", "outcome": "cancel"})
    assert s["policy_violation"]


def test_summary_and_bootstrap():
    res = [{"expected": "cancel", "outcome": "cancel", "turns": 3}] * 8 + [{"expected": "handoff", "outcome": "none", "turns": 5}] * 2
    m = summarize(res)
    assert m["task_success"] == 0.8 and m["false_automation_rate"] == 0.2
    b = paired_bootstrap(np.zeros(50), np.ones(50))
    assert b["diff"] == 1.0 and b["p_b_not_better"] == 0.0

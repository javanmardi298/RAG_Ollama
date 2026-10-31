from collections import Counter

from support.experiments import assign, readout, sample_size_per_arm, srm_check
from support.monitoring import intent_drift, psi


def test_psi_zero_for_same_and_large_for_shift():
    assert psi({"a": .5, "b": .5}, {"a": .5, "b": .5}) < 1e-6
    assert psi({"a": .9, "b": .1}, {"a": .2, "b": .8}) > 0.25


def test_intent_drift_flags_new_mix():
    ref = ["track"] * 80 + ["refund"] * 20
    cur = ["track"] * 40 + ["refund"] * 60
    r = intent_drift(ref, cur)
    assert r["chi2_p"] < 0.001 and r["psi"] > 0.25


def test_assignment_stable_and_balanced():
    arms = [assign(f"s{i}", "exp") for i in range(4000)]
    assert arms == [assign(f"s{i}", "exp") for i in range(4000)]
    assert not srm_check(Counter(arms))["mismatch"]


def test_sample_size_is_sensible():
    n = sample_size_per_arm(0.60, 0.03)
    assert 3000 < n < 5000


def test_guardrail_blocks_ship():
    arms = {"control": {"n": 5000, "automated": 3000, "fa": 50},
            "treatment": {"n": 5000, "automated": 3200, "fa": 150}}
    assert not readout(arms, "automated", {"fa": 0.005})["ship"]

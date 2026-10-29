def check_recall_single(m):
    """recall@k with one relevant document"""
    assert m.recall_at_k(["a", "b", "c"], {"b"}, 2) == 1.0
    assert m.recall_at_k(["a", "b", "c"], {"c"}, 2) == 0.0


def check_recall_multiple(m):
    """recall@k is a fraction when several are relevant"""
    assert m.recall_at_k(["a", "b", "c"], {"a", "c"}, 2) == 0.5
    assert m.recall_at_k(["a"], set(), 3) == 0.0


def check_reciprocal_rank(m):
    """rank 1 -> 1.0, rank 2 -> 0.5, missing -> 0"""
    assert m.reciprocal_rank(["x", "y"], {"x"}) == 1.0
    assert m.reciprocal_rank(["x", "y"], {"y"}) == 0.5
    assert m.reciprocal_rank(["x", "y"], {"z"}) == 0.0


def check_evaluate_means(m):
    """evaluate averages over answerable questions only"""
    qs = [{"question": "q1", "relevant": "a"}, {"question": "q2", "relevant": "b"}, {"question": "q3", "relevant": ""}]
    ranks = {"q1": ["a", "b"], "q2": ["x", "y", "b"], "q3": ["a"]}
    out = m.evaluate(lambda q: ranks[q], qs, k=2)
    assert out["n"] == 2, out
    assert out["recall@2"] == 0.5, out
    assert abs(out["mrr"] - (1 + 1 / 3) / 2) < 1e-9, out
    assert out["misses"] == ["q2"], out


def check_duplicates_collapse(m):
    """several chunks of one document count once, in first-seen order"""
    qs = [{"question": "q", "relevant": "b"}]
    out = m.evaluate(lambda q: ["a", "a", "a", "b"], qs, k=2)
    assert out["recall@2"] == 1.0, f"duplicates pushed the answer out of the top 2: {out}"
    assert out["mrr"] == 0.5, out


def check_empty_is_safe(m):
    """no answerable question -> zeros, no crash"""
    out = m.evaluate(lambda q: [], [{"question": "q", "relevant": ""}], k=3)
    assert out["n"] == 0 and out["mrr"] == 0.0

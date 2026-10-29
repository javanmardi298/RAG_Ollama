def check_rewrite_order(m):
    """rewrite: expanded question, then content words, then single words"""
    out = m.rewrite("is a broken table leg covered", [])
    assert out[0] == "is a damage defect table leg covered", out
    assert out[1] == "damage defect table leg covered", out
    assert "table" in out and "leg" in out, out


def check_rewrite_skips_tried(m):
    """rewrite never repeats a tried query"""
    first = m.rewrite("how to send back a sofa", [])
    again = m.rewrite("how to send back a sofa", first[:2])
    assert not set(again) & set(first[:2]), again
    assert len(set(again)) == len(again), "duplicates in the rewrite output"


def _chunks(*ids):
    return [{"id": i, "text": i} for i in ids]


def check_stops_when_enough(m):
    """one good first search needs a single round and no rewrite"""
    calls = []
    out = m.agentic_search("q", lambda s: calls.append(s) or _chunks("a"), lambda q, c: True, lambda q, t: ["never"], max_rounds=3)
    assert out["rounds"] == 1 and out["queries"] == ["q"] and calls == ["q"], out


def check_retries_with_rewrite(m):
    """nothing relevant -> rewrite -> second round finds it"""
    def search(q):
        return _chunks("hit") if q == "better" else _chunks("miss")
    out = m.agentic_search("q", search, lambda q, c: c["id"] == "hit", lambda q, t: ["better"] if "better" not in t else [], max_rounds=3)
    assert [c["id"] for c in out["chunks"]] == ["hit"], out
    assert out["rounds"] == 2 and out["queries"] == ["q", "better"], out


def check_round_budget(m):
    """max_rounds is a hard limit"""
    n = []

    def rw(q, tried):
        n.append(1)
        return [f"q{len(tried)}"]
    out = m.agentic_search("q", lambda s: [], lambda q, c: True, rw, max_rounds=3)
    assert out["rounds"] == 3 and len(out["queries"]) == 3 and out["chunks"] == [], out


def check_stops_without_new_ideas(m):
    """empty rewrite ends the loop early"""
    out = m.agentic_search("q", lambda s: [], lambda q, c: True, lambda q, t: [], max_rounds=5)
    assert out["rounds"] == 1, out


def check_no_duplicate_chunks(m):
    """the same chunk found twice is kept once"""
    out = m.agentic_search("q", lambda s: _chunks("a", "a"), lambda q, c: True, lambda q, t: [], min_relevant=5, max_rounds=1)
    assert [c["id"] for c in out["chunks"]] == ["a"], out

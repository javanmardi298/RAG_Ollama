C = [{"id": "returns#0", "heading": "Returns", "text": "You can return most items within 30 days of delivery."}]
NO_REWRITE = lambda q, t: []  # noqa: E731


def _answer(text="You can return items within 30 days [returns#0]", cites=("returns#0",)):
    return lambda q, cs: (text, list(cites))


def _search(q):
    return C


def check_verify_accepts_supported(m):
    """verify accepts an answer built from the sources"""
    assert m.verify("You can return items within 30 days [returns#0]", C) is True


def check_verify_rejects_invented(m):
    """verify rejects words the sources do not contain"""
    assert m.verify("Returns are free for gold members [returns#0]", C) is False
    assert m.verify("", C) is False


def check_direct_route(m):
    """hello is answered without searching"""
    called = []
    out = m.run_agent("hello", lambda q: called.append(q) or C, lambda q, c: True, NO_REWRITE, _answer())
    assert out["route"] == "direct" and out["rounds"] == 0 and not out["abstained"] and called == [], (out, called)


def check_good_answer(m):
    """a supported, cited answer is returned"""
    out = m.run_agent("how long to return", _search, lambda q, c: True, NO_REWRITE, _answer())
    assert out["abstained"] is False and out["citations"] == ["returns#0"] and out["rounds"] == 1, out


def check_abstain_without_evidence(m):
    """no relevant chunk -> abstain"""
    out = m.run_agent("ceo phone", _search, lambda q, c: False, NO_REWRITE, _answer())
    assert out["abstained"] and out["answer"] is None, out


def check_abstain_on_fake_citation_or_failed_verify(m):
    """invented citation or unsupported answer -> abstain"""
    a = m.run_agent("q", _search, lambda q, c: True, NO_REWRITE, _answer(cites=("fake#1",)))
    b = m.run_agent("q", _search, lambda q, c: True, NO_REWRITE, _answer("Gold members get free returns [returns#0]"))
    assert a["abstained"] and b["abstained"], (a, b)


def check_report_counts(m):
    """report counts the five categories"""
    ok = {"answer": "x", "citations": ["a"], "route": "retrieve", "rounds": 1, "abstained": False}
    ab = {"answer": None, "citations": [], "route": "retrieve", "rounds": 2, "abstained": True}
    d = {"answer": "hi", "citations": [], "route": "direct", "rounds": 0, "abstained": False}
    qs = [{"answerable": "yes"}, {"answerable": "yes"}, {"answerable": "no"}, {"answerable": "no"}, {"answerable": "direct"}]
    assert m.report([ok, ab, ab, ok, d], qs) == {"answered_correctly": 1, "abstained_wrongly": 1, "abstained_correctly": 1,
                                                  "answered_unanswerable": 1, "direct_ok": 1}

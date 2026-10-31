from support.robustness import detect_language, noisify


def test_language():
    assert detect_language("Wo ist meine Bestellung?") == "de"
    assert detect_language("Where is my order please") == "en"
    assert detect_language("HH-100001") is None


def test_noise_is_deterministic_and_grows():
    t = "I would like to cancel my order please, it was a mistake."
    assert noisify(t, 2) == noisify(t, 2) and noisify(t, 0) == t
    diff = lambda a, b: sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))  # noqa: E731
    assert diff(t, noisify(t, 3)) > diff(t, noisify(t, 1))

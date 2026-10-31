import numpy as np
import pandas as pd

from support.intents import apply_temperature, evaluate, expected_calibration_error, fit_temperature, make_tfidf_model


def toy():
    rows = []
    for intent, words in {"cancel_order": "cancel stop order", "track_order": "where track parcel",
                          "get_refund": "refund money back"}.items():
        for i in range(40):
            w = words.split()
            rows.append({"text": f"{w[i % 3]} my {w[(i + 1) % 3]} please {i}", "intent": intent})
    return pd.DataFrame(rows)


def test_tfidf_learns_and_tolerates_typos():
    df = toy()
    m = make_tfidf_model().fit(df.text, df.intent)
    assert m.predict(["I want to cancle my order"])[0] == "cancel_order"
    assert m.predict(["where is my parcle"])[0] == "track_order"


def test_temperature_reduces_overconfidence():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 3, 500)
    proba = np.full((500, 3), 0.01)
    proba[np.arange(500), np.where(rng.random(500) < 0.7, y, (y + 1) % 3)] = 0.98   # 98 % sure, 70 % right
    proba /= proba.sum(1, keepdims=True)
    T = fit_temperature(proba, y)
    before = expected_calibration_error(proba.max(1), proba.argmax(1) == y)
    after = expected_calibration_error(apply_temperature(proba, T).max(1), proba.argmax(1) == y)
    assert T > 1 and after < before


def test_evaluate_reports_oos():
    r = evaluate(["a", "oos", "oos", "b"], ["a", "oos", "a", "b"])
    assert r["oos_recall"] == 0.5 and r["in_scope_accuracy"] == 1.0

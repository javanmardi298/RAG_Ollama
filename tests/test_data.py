import pandas as pd

from support.data import clean_intents, normalize, split_intents


def test_normalize_masks_placeholders_and_punctuation():
    assert normalize("Cancel order {{Order Number}}!!") == normalize("cancel  order {{Order ID}}")


def test_split_has_no_leakage_and_keeps_all_intents():
    rows = []
    for intent in ("cancel_order", "track_order", "get_refund"):
        for i in range(120):
            text = f"{intent.replace('_', ' ')} please {i % 40}"   # forces repeated keys
            rows.append({"instruction": text, "intent": intent, "category": "X", "flags": "B"})
    df, report = clean_intents(pd.DataFrame(rows))
    assert report["exact_duplicates_dropped"] > 0
    splits = split_intents(df)   # asserts no shared keys internally
    for part in splits.values():
        assert set(part["intent"]) == {"cancel_order", "track_order", "get_refund"}


def test_conflicting_labels_are_dropped():
    df = pd.DataFrame({"instruction": ["where is my money", "where is my money", "hi"],
                       "intent": ["track_refund", "get_refund", "greet"],
                       "category": "X", "flags": "B"})
    clean, report = clean_intents(df)
    assert report["conflicting_keys"] == 1
    assert list(clean["text"]) == ["hi"]

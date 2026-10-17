"""Loading, cleaning and splitting the intent data (Bitext) and the product catalog (WANDS)."""
from __future__ import annotations

import re
import string
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from .config import RAW_DIR, SEED

BITEXT_HF = "bitext/Bitext-customer-support-llm-chatbot-training-dataset"
WANDS_URL = "https://raw.githubusercontent.com/wayfair/WANDS/main/dataset/product.csv"

_PLACEHOLDER = re.compile(r"\{\{.*?\}\}")
_PUNCT = str.maketrans({c: " " for c in string.punctuation})


# ---------- Bitext ----------

def load_bitext(local_csv: str | Path | None = None) -> pd.DataFrame:
    """Load Bitext from a local CSV, the cache, or the Hugging Face Hub (in that order)."""
    cache = RAW_DIR / "bitext.csv"
    for path in (local_csv, cache):
        if path and Path(path).exists():
            return pd.read_csv(path)

    from datasets import load_dataset  # imported lazily: only needed for the first download

    df = load_dataset(BITEXT_HF, split="train").to_pandas()
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False)
    return df


def normalize(text: str) -> str:
    """Key for finding duplicates: lowercase, placeholders masked, punctuation and extra spaces removed.

    "Cancel order {{Order Number}}!!" and "cancel order {{Order Number}}" get the same key.
    """
    text = _PLACEHOLDER.sub(" ph ", str(text).lower())
    return " ".join(text.translate(_PUNCT).split())


def clean_intents(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Keep the columns we need, drop empty rows, exact duplicates and contradictory labels."""
    df = df[["instruction", "intent", "category", "flags"]].rename(columns={"instruction": "text"})
    df = df.dropna(subset=["text", "intent"])
    df["text"] = df["text"].str.strip()
    df = df[df["text"] != ""].copy()
    df["key"] = df["text"].map(normalize)

    report = {"rows_in": len(df)}

    # Same key with more than one intent = the label itself is ambiguous. Drop those keys.
    labels_per_key = df.groupby("key")["intent"].nunique()
    conflicting = labels_per_key[labels_per_key > 1].index
    report["conflicting_keys"] = len(conflicting)
    df = df[~df["key"].isin(conflicting)]

    before = len(df)
    df = df.drop_duplicates(subset=["text", "intent"])
    report["exact_duplicates_dropped"] = before - len(df)
    report["rows_out"] = len(df)
    report["unique_keys"] = df["key"].nunique()
    return df.reset_index(drop=True), report


def split_intents(df: pd.DataFrame, seed: int = SEED) -> dict[str, pd.DataFrame]:
    """~70/15/15 split, stratified by intent and grouped by `key`.

    Grouping keeps every copy of a near-identical sentence in ONE split, so the
    test set never contains a sentence the model has effectively seen in training.
    """
    outer = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=seed)
    rest_idx, test_idx = next(outer.split(df, df["intent"], groups=df["key"]))
    rest, test = df.iloc[rest_idx], df.iloc[test_idx]

    inner = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=seed)
    train_idx, dev_idx = next(inner.split(rest, rest["intent"], groups=rest["key"]))
    splits = {
        "train": rest.iloc[train_idx],
        "dev": rest.iloc[dev_idx],
        "test": test,
    }
    assert_no_leakage(splits)
    return {name: part.reset_index(drop=True) for name, part in splits.items()}


def assert_no_leakage(splits: dict[str, pd.DataFrame]) -> None:
    names = list(splits)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = set(splits[a]["key"]) & set(splits[b]["key"])
            assert not shared, f"{len(shared)} keys shared between {a} and {b}"


# ---------- WANDS ----------

def load_wands_products(wands_dir: str | Path | None = None) -> pd.DataFrame:
    """Load WANDS product.csv (tab-separated). Reuses the copy from the product-search project if given."""
    candidates = [Path(wands_dir) / "product.csv"] if wands_dir else []
    candidates.append(RAW_DIR / "wands_product.csv")
    for path in candidates:
        if path.exists():
            return pd.read_csv(path, sep="\t")

    df = pd.read_csv(WANDS_URL, sep="\t")
    df.to_csv(RAW_DIR / "wands_product.csv", sep="\t", index=False)
    return df

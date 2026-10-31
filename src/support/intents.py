"""Stage 1: intent classification, three ways, one evaluation.

1. TF-IDF (words + character n-grams) + logistic regression   -> fast, strong baseline
2. Sentence embeddings + logistic regression                   -> understands paraphrases, multilingual
3. LLM with dynamic few-shot examples                          -> no training, slow, no free confidence
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import FeatureUnion, Pipeline

from .config import PROCESSED_DIR, RAW_DIR, SEED

CLINC_URL = "https://raw.githubusercontent.com/clinc/oos-eval/master/data/data_full.json"


# ---------- data ----------

def load_splits() -> dict[str, pd.DataFrame]:
    return {n: pd.read_csv(PROCESSED_DIR / f"intents_{n}.csv") for n in ("train", "dev", "test")}


def load_clinc_oos(path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Out-of-scope messages from CLINC150 (keys oos_train / oos_val / oos_test)."""
    path = Path(path) if path else RAW_DIR / "clinc_data_full.json"
    if not path.exists():
        import urllib.request
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(CLINC_URL, path)
    data = json.loads(path.read_text())
    mapping = {"oos_train": "train", "oos_val": "dev", "oos_test": "test"}
    return {ours: pd.DataFrame({"text": [t for t, _ in data[key]], "intent": "oos", "flags": ""})
            for key, ours in mapping.items()}


def with_oos(splits: dict, oos: dict, test_oos_max: int = 300, seed: int = SEED) -> dict:
    out = {}
    for name, df in splits.items():
        extra = oos[name]
        if name == "test" and len(extra) > test_oos_max:
            extra = extra.sample(test_oos_max, random_state=seed)
        out[name] = pd.concat([df[["text", "intent", "flags"]], extra], ignore_index=True)
    return out


# ---------- model 1: TF-IDF ----------

def make_tfidf_model(C: float = 5.0) -> Pipeline:
    features = FeatureUnion([
        ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)),
        # character n-grams inside word boundaries: robust to typos ("cancle", "ordr")
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2)),
    ])
    clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced")
    return Pipeline([("features", features), ("clf", clf)])


# ---------- model 2: embeddings ----------

class EmbeddingClassifier:
    """Frozen multilingual sentence encoder + logistic regression on top."""

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                 C: float = 10.0, device: str | None = None):
        from sentence_transformers import SentenceTransformer
        self.encoder = SentenceTransformer(model_name, device=device)
        self.clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced")

    def encode(self, texts, batch_size: int = 128) -> np.ndarray:
        return self.encoder.encode(list(texts), batch_size=batch_size, normalize_embeddings=True,
                                   show_progress_bar=False)

    def fit(self, texts, labels, X: np.ndarray | None = None):
        self.clf.fit(self.encode(texts) if X is None else X, labels)
        self.classes_ = self.clf.classes_
        return self

    def predict_proba(self, texts, X: np.ndarray | None = None) -> np.ndarray:
        return self.clf.predict_proba(self.encode(texts) if X is None else X)


# ---------- model 3: LLM ----------

class LLMClassifier:
    """Zero/few-shot classification with constrained JSON output.

    Dynamic few-shot: for each message, the k most similar training examples (TF-IDF cosine)
    are put into the prompt. This is retrieval used for prompting.
    """

    def __init__(self, llm, train: pd.DataFrame, labels: list[str], k: int = 8):
        self.llm, self.labels, self.k = llm, sorted(labels), k
        self.train = train.reset_index(drop=True)
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(self.train["text"])
        self.train_X = self.vec.transform(self.train["text"])
        self.schema = {"type": "object", "properties": {"intent": {"type": "string", "enum": self.labels}},
                       "required": ["intent"]}

    def _examples(self, text: str) -> str:
        if self.k == 0:
            return ""
        sims = (self.train_X @ self.vec.transform([text]).T).toarray().ravel()
        idx = np.argsort(-sims)[: self.k]
        lines = [f'"{self.train.text[i]}" -> {self.train.intent[i]}' for i in idx]
        return "Examples:\n" + "\n".join(lines) + "\n\n"

    def predict_one(self, text: str) -> str:
        prompt = (f"Classify the customer message into exactly one intent.\n"
                  f"Intents: {', '.join(self.labels)}\n"
                  f"Use 'oos' if the message is not about this online store's orders, delivery, payment, "
                  f"refunds or account.\n\n{self._examples(text)}Message: \"{text}\"")
        return self.llm.json([{"role": "user", "content": prompt}], self.schema)["intent"]

    def predict(self, texts) -> list[str]:
        return [self.predict_one(t) for t in texts]


# ---------- calibration ----------

def fit_temperature(proba: np.ndarray, y_idx: np.ndarray) -> float:
    """Temperature scaling: one number T that makes probabilities honest, fitted on dev (NLL)."""
    logits = np.log(np.clip(proba, 1e-12, 1))

    def nll(T):
        z = logits / T
        z = z - z.max(axis=1, keepdims=True)
        logp = z - np.log(np.exp(z).sum(axis=1, keepdims=True))
        return -logp[np.arange(len(y_idx)), y_idx].mean()

    return float(minimize_scalar(nll, bounds=(0.05, 20), method="bounded").x)


def apply_temperature(proba: np.ndarray, T: float) -> np.ndarray:
    z = np.log(np.clip(proba, 1e-12, 1)) / T
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def expected_calibration_error(confidence, correct, n_bins: int = 15) -> float:
    """Average gap between how sure the model is and how often it is right, weighted by bin size."""
    confidence, correct = np.asarray(confidence), np.asarray(correct, float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (confidence > lo) & (confidence <= hi)
        if m.any():
            ece += m.mean() * abs(confidence[m].mean() - correct[m].mean())
    return float(ece)


# ---------- evaluation ----------

def evaluate(y_true, y_pred, confidence=None, flags=None) -> dict:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    out = {"n": int(len(y_true)), "accuracy": accuracy_score(y_true, y_pred),
           "macro_f1": f1_score(y_true, y_pred, average="macro")}
    if (y_true == "oos").any():
        is_oos, pred_oos = y_true == "oos", y_pred == "oos"
        out["oos_recall"] = float((pred_oos & is_oos).sum() / is_oos.sum())
        out["in_scope_accuracy"] = float((y_pred[~is_oos] == y_true[~is_oos]).mean())
    if confidence is not None:
        out["ece"] = expected_calibration_error(confidence, y_true == y_pred)
    if flags is not None:
        f = pd.Series(np.asarray(flags)).fillna("")
        out["accuracy_by_flag"] = {flag: float((y_true[f.str.contains(flag)] == y_pred[f.str.contains(flag)]).mean())
                                   for flag in "BZQKNWLP" if f.str.contains(flag).sum() >= 30}
    out["per_intent"] = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    return out


def timed_predict(predict_fn, texts) -> tuple[list, float]:
    """Predictions plus milliseconds per message: speed is part of the comparison."""
    start = time.perf_counter()
    preds = predict_fn(texts)
    return preds, 1000 * (time.perf_counter() - start) / max(len(texts), 1)

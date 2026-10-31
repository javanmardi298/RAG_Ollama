"""Support-ticket triage: TF-IDF + logistic regression, a leakage-free split by template, calibration (ECE), and a
selective decision: route automatically only when the model is confident enough, otherwise send to a human."""
import json
import os
import re
import shutil
import subprocess

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline, make_union


def load_tickets(path="data/tickets.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["tickets"]


def split(tickets, seed=42):
    """train / dev / test by TEMPLATE: the same wording never appears on both sides (that would be leakage)."""
    groups = [t["template"] for t in tickets]
    idx = np.arange(len(tickets))
    rest, test = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(idx, groups=groups))
    tr, dev = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(rest, groups=[groups[i] for i in rest]))
    pick = lambda ids: [tickets[i] for i in ids]  # noqa: E731
    return pick(rest[tr]), pick(rest[dev]), pick(test)


def random_split(tickets, seed=42):
    """The naive split for comparison: rows shuffled, so near-identical tickets land in train and test."""
    rng = np.random.default_rng(seed)
    ids = rng.permutation(len(tickets))
    n = len(ids)
    return [tickets[i] for i in ids[: n // 2]], [tickets[i] for i in ids[n // 2: 3 * n // 4]], [tickets[i] for i in ids[3 * n // 4:]]


def train(tickets, C=4.0):
    """Word and character n-grams (typos!) into a logistic regression."""
    features = make_union(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                          TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True))
    model = make_pipeline(features, LogisticRegression(C=C, max_iter=2000))
    return model.fit([t["text"] for t in tickets], [t["label"] for t in tickets])


def predict(model, tickets, temperature=1.0):
    """Labels and calibrated confidences (temperature > 1 softens over-confident probabilities)."""
    logits = model.decision_function([t["text"] for t in tickets]) / temperature
    p = np.exp(logits - logits.max(axis=1, keepdims=True))
    p /= p.sum(axis=1, keepdims=True)
    return model.classes_[p.argmax(axis=1)], p.max(axis=1)


def scores(tickets, labels):
    y = [t["label"] for t in tickets]
    return {"accuracy": round(accuracy_score(y, labels), 3), "macro_f1": round(f1_score(y, labels, average="macro"), 3)}


def ece(correct, confidence, bins=10):
    """Expected calibration error: how far the confidence is from the real accuracy, averaged over confidence bins."""
    correct, confidence = np.asarray(correct, float), np.asarray(confidence)
    edges, total = np.linspace(0, 1, bins + 1), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (confidence > lo) & (confidence <= hi)
        if m.any():
            total += m.mean() * abs(correct[m].mean() - confidence[m].mean())
    return round(float(total), 4)


def fit_temperature(model, dev):
    """The temperature that minimises the negative log-likelihood on dev (simple grid search)."""
    y = [t["label"] for t in dev]
    logits = model.decision_function([t["text"] for t in dev])
    cls = list(model.classes_)
    best = (1e9, 1.0)
    for T in np.linspace(0.3, 5, 48):
        z = logits / T
        logp = z - np.log(np.exp(z - z.max(1, keepdims=True)).sum(1, keepdims=True)) - z.max(1, keepdims=True)
        nll = -np.mean([logp[i, cls.index(lab)] for i, lab in enumerate(y)])
        best = min(best, (nll, float(T)))
    return round(best[1], 2)


def choose_threshold(correct, confidence, target_accuracy=0.9, min_auto=5):
    """Sort tickets by confidence, most confident first; return the lowest threshold whose automated set still reaches the
    target accuracy on dev (largest coverage), with at least `min_auto` automated tickets. Nothing safe -> 1.01 (all human)."""
    correct, confidence = np.asarray(correct, float), np.asarray(confidence)
    order = np.argsort(-confidence)
    running = np.cumsum(correct[order]) / np.arange(1, len(order) + 1)
    ok = [i for i in range(min_auto - 1, len(order)) if running[i] >= target_accuracy]
    return float(confidence[order][max(ok)]) if ok else 1.01


def selective(correct, confidence, threshold):
    """Coverage = share routed automatically; error among those is what customers feel."""
    correct, confidence = np.asarray(correct, float), np.asarray(confidence)
    auto = confidence >= threshold
    return {"threshold": round(threshold, 3), "coverage": round(float(auto.mean()), 3),
            "accuracy_automated": round(float(correct[auto].mean()), 3) if auto.any() else None,
            "to_human": int((~auto).sum())}


def confusion(tickets, labels, classes):
    return confusion_matrix([t["label"] for t in tickets], labels, labels=classes)


# ---------- optional: zero-shot LLM classifier for comparison ----------

def llm_classifier(classes, provider=None, model=None):
    """ticket text -> label, asked to Ollama, Claude or OpenCode (TRIAGE_PROVIDER)."""
    provider = provider or os.environ.get("TRIAGE_PROVIDER", "")

    def prompt(text):
        return f"Classify this support ticket into exactly one of: {', '.join(classes)}. Answer with the label only.\nTicket: {text}"
    if provider == "ollama":
        import ollama
        model = model or "qwen2.5:7b"
        ask = lambda text: ollama.chat(model=model, messages=[{"role": "user", "content": prompt(text)}], options={"temperature": 0})["message"]["content"]  # noqa: E731
    elif provider == "anthropic":
        import anthropic
        client, model = anthropic.Anthropic(), model or "claude-sonnet-5-5"
        ask = lambda text: "".join(b.text for b in client.messages.create(model=model, max_tokens=20, messages=[{"role": "user", "content": prompt(text)}]).content if b.type == "text")  # noqa: E731
    elif provider == "opencode":
        if not shutil.which("opencode"):
            raise RuntimeError("opencode is not installed (https://opencode.ai)")
        model = model or "anthropic/claude-sonnet-5-5"
        ask = lambda text: subprocess.run(["opencode", "run", "-m", model, prompt(text)], capture_output=True, text=True, encoding="utf-8", timeout=300).stdout  # noqa: E731
    else:
        raise ValueError("set TRIAGE_PROVIDER to ollama, anthropic or opencode")

    def classify(text):
        out = ask(text).lower()
        return next((c for c in classes if re.search(rf"\b{c}\b", out)), "unknown")
    return classify

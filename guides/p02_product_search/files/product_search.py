"""Product search for an online furniture shop: product text (basic vs rich), BM25, character-trigram search,
optional dense embeddings, hybrid fusion with RRF, and graded evaluation (nDCG@10, recall@10, MRR) with a bootstrap test."""
import json
import math
import re
from collections import Counter

import numpy as np

STOP = {"a", "an", "the", "and", "or", "for", "of", "to", "in", "on", "with", "by", "is", "it", "this"}
GRADE = {"Exact": 2, "Partial": 1, "Irrelevant": 0}


# ---------- data ----------

def load_data(path="data/products.json"):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    qrels = {}
    for lab in d["labels"]:
        qrels.setdefault(lab["query_id"], {})[lab["product_id"]] = GRADE[lab["label"]]
    return d["products"], {q["query_id"]: q["query"] for q in d["queries"]}, qrels


def features_to_text(raw):
    return "; ".join(f"{k}: {v}" for k, v in (p.split(":", 1) for p in raw.split("|") if ":" in p))


def product_text(p, rich=True):
    """basic = name + description; rich adds the class, the category and the structured features."""
    if not rich:
        return p["product_name"] + ". " + p["description"]
    return (f"{p['product_name']}\nCategory: {p['product_class']} ({p['category']})\n"
            f"Features: {features_to_text(p['features'])}\nDescription: {p['description']}")


# ---------- search ----------

def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class BM25:
    def __init__(self, texts, k1=1.5, b=0.75):
        toks = [tokenize(t) for t in texts]
        self.k1, self.b, self.n = k1, b, len(texts)
        self.tf = [Counter(t) for t in toks]
        self.len = [len(t) for t in toks]
        self.avg = sum(self.len) / self.n
        self.df = Counter(w for t in toks for w in set(t))

    def scores(self, query):
        s = np.zeros(self.n)
        for w in tokenize(query):
            df = self.df.get(w, 0)
            if not df:
                continue
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            for i in range(self.n):
                tf = self.tf[i].get(w, 0)
                if tf:
                    s[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        return s


def trigram_scores(query, texts):
    def grams(t):
        out = set()
        for w in re.findall(r"[a-z0-9]+", t.lower()):
            w = f" {w} "
            out |= {w[i:i + 3] for i in range(len(w) - 2)}
        return out
    q = grams(query)
    return np.array([len(q & g) / len(q | g) if q | g else 0.0 for g in map(grams, texts)])


def top_k(scores, ids, k=10):
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    return [ids[i] for i in order if scores[i] > 0][:k]


def rrf(lists, k=60):
    score = {}
    for lst in lists:
        for rank, pid in enumerate(lst, start=1):
            score[pid] = score.get(pid, 0.0) + 1 / (k + rank)
    return sorted(score, key=lambda p: (-score[p], p))


class Dense:
    """Embedding search with sentence-transformers (optional; only if the package is installed)."""

    def __init__(self, texts, model="sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)
        self.emb = self.model.encode(texts, normalize_embeddings=True)

    def scores(self, query):
        return self.emb @ self.model.encode(query, normalize_embeddings=True)


# ---------- evaluation ----------

def dcg(gains):
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg(ranked, rel, k=10):
    best = dcg(sorted(rel.values(), reverse=True)[:k])
    return dcg([rel.get(p, 0) for p in ranked[:k]]) / best if best else float("nan")


def recall(ranked, rel, k=10):
    exact = {p for p, g in rel.items() if g == 2}
    return len(exact & set(ranked[:k])) / len(exact) if exact else float("nan")


def mrr(ranked, rel):
    return next((1 / (i + 1) for i, p in enumerate(ranked) if rel.get(p) == 2), 0.0)


def evaluate(run, qrels):
    """run: query_id -> ranked product ids. Returns per-query metrics (for the bootstrap) and their means."""
    per_query = {q: {"ndcg@10": ndcg(r, qrels[q]), "recall@10": recall(r, qrels[q]), "mrr": mrr(r, qrels[q])} for q, r in run.items()}
    means = {m: round(float(np.nanmean([v[m] for v in per_query.values()])), 3) for m in ["ndcg@10", "recall@10", "mrr"]}
    return per_query, means


def bootstrap(a, b, n=10000, seed=42):
    """Is b better than a on the same queries? Mean difference, 95% interval and the share of resamples where b <= a."""
    diff = np.array([b[q] - a[q] for q in a])
    rng = np.random.default_rng(seed)
    means = diff[rng.integers(0, len(diff), size=(n, len(diff)))].mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    return {"diff": round(float(diff.mean()), 3), "low": round(float(low), 3), "high": round(float(high), 3),
            "p": round(float((means <= 0).mean()), 4)}

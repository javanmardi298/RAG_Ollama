"""One retrieval index for any chunks: BM25, dense, hybrid (RRF), optional reranker and MMR diversity.

Generalises support.rag.Retriever (which is tied to the store's policy files) to any corpus.
The encoder is any object with .encode(list[str], normalize_embeddings=True) (sentence-transformers);
the reranker is any callable (query, [texts]) -> [scores] (e.g. a cross-encoder's .predict on pairs).
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from support.rag import BM25, rrf

from .chunking import Chunk


class Index:
    def __init__(self, chunks: list[Chunk], encoder=None, k1: float = 1.5, b: float = 0.75, rrf_k: int = 60):
        if not chunks:
            raise ValueError("no chunks to index")
        self.chunks, self.encoder, self.rrf_k = chunks, encoder, rrf_k
        self.bm25 = BM25([c.indexed_text for c in chunks], k1=k1, b=b)
        self.emb = (encoder.encode([c.indexed_text for c in chunks], normalize_embeddings=True)
                    if encoder is not None else None)

    def _ranked(self, query: str, mode: str, allowed: np.ndarray) -> list[int]:
        rankings = []
        if mode in ("bm25", "hybrid"):
            raw = self.bm25.scores(query)
            s = np.where(allowed, raw, -np.inf)
            # a chunk sharing no word with the query is not a BM25 hit; ranking it anyway only adds noise to RRF
            rankings.append([i for i in np.argsort(-s, kind="stable") if allowed[i] and raw[i] > 0])
        if mode in ("dense", "hybrid"):
            if self.emb is None:
                raise ValueError(f"mode={mode} needs an encoder")
            q = self.encoder.encode([query], normalize_embeddings=True)[0]
            s = np.where(allowed, self.emb @ q, -np.inf)
            rankings.append([i for i in np.argsort(-s) if allowed[i]])
        return rankings[0] if len(rankings) == 1 else rrf(rankings, self.rrf_k)

    def search(self, query: str, k: int = 5, mode: str = "hybrid", where: Callable[[Chunk], bool] | None = None,
               reranker: Callable[[str, list[str]], list[float]] | None = None, rerank_top: int = 20,
               mmr_lambda: float | None = None) -> list[Chunk]:
        """where: metadata filter (language, access rights, date) applied BEFORE ranking, never after."""
        allowed = np.array([where(c) if where else True for c in self.chunks])
        order = self._ranked(query, mode, allowed)
        if reranker is not None:
            cand = order[:rerank_top]
            scores = reranker(query, [self.chunks[i].indexed_text for i in cand])
            order = [cand[j] for j in np.argsort(-np.asarray(scores))] + order[rerank_top:]
        if mmr_lambda is not None:
            order = self._mmr(query, order[:max(rerank_top, k)], k, mmr_lambda)
        return [self.chunks[i] for i in order[:k]]

    def _mmr(self, query: str, cand: list[int], k: int, lam: float) -> list[int]:
        """Maximal Marginal Relevance: relevant but not redundant (needs the encoder)."""
        if self.emb is None:
            raise ValueError("MMR needs an encoder")
        q = self.encoder.encode([query], normalize_embeddings=True)[0]
        rel = {i: float(self.emb[i] @ q) for i in cand}
        chosen: list[int] = []
        while cand and len(chosen) < k:
            best = max(cand, key=lambda i: lam * rel[i] - (1 - lam) * max((float(self.emb[i] @ self.emb[j]) for j in chosen),
                                                                            default=0.0))
            chosen.append(best)
            cand = [i for i in cand if i != best]
        return chosen


def multi_query_search(index: Index, query: str, rewrite: Callable[[str], list[str]], k: int = 5,
                       mode: str = "hybrid", **kw) -> list[Chunk]:
    """Query rewriting: search the original question and its rewrites (synonyms, translation, decomposition),
    then fuse the rankings with RRF. Fixes 'send back' vs 'return' style misses without touching the index."""
    queries = [query] + [q for q in rewrite(query) if q and q != query]
    pos = {id(c): i for i, c in enumerate(index.chunks)}
    rankings = [[pos[id(c)] for c in index.search(q, k=max(k * 3, 10), mode=mode, **kw)] for q in queries]
    return [index.chunks[i] for i in rrf(rankings, index.rrf_k)[:k]]

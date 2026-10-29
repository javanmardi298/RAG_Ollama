"""Step 3: detect representation collapse from a batch of embeddings."""
from __future__ import annotations

import numpy as np


def collapse_stats(z: np.ndarray) -> dict:
    """z: (N, D) embeddings of N different inputs."""
    z = np.asarray(z, dtype=float)
    mean_std = float(z.std(axis=0).mean())
    s = np.linalg.svd(z - z.mean(axis=0), compute_uv=False)
    total = s.sum()
    if total == 0:
        rank = 0.0
    else:
        p = np.clip(s / total, 1e-12, None)
        rank = float(np.exp(-(p * np.log(p)).sum()))
    return {"mean_std": mean_std, "effective_rank": rank, "dim": int(z.shape[1])}


def diagnose(stats: dict, std_tol: float = 0.01, low_rank_ratio: float = 0.1) -> str:
    if stats["mean_std"] < std_tol or stats["effective_rank"] < 1.5:
        return "collapsed"
    if stats["effective_rank"] < low_rank_ratio * stats["dim"]:
        return "low_rank"
    return "healthy"


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    cases = {"constant": np.ones((200, 16)) + 1e-4 * rng.normal(size=(200, 16)),
             "gaussian": rng.normal(size=(200, 16)),
             "low rank": rng.normal(size=(200, 3)) @ rng.normal(size=(3, 64))}
    for name, z in cases.items():
        st = collapse_stats(z)
        print(f"{name:9s} std={st['mean_std']:.4f} rank={st['effective_rank']:.2f}/{st['dim']} -> {diagnose(st)}")

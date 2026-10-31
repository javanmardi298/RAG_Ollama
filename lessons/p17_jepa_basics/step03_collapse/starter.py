"""Step 3: detect representation collapse from a batch of embeddings."""
from __future__ import annotations

import numpy as np


def collapse_stats(z: np.ndarray) -> dict:
    """z: (N, D) embeddings of N different inputs."""
    # TODO 1: mean_std = mean over the D dimensions of the std ACROSS samples (axis 0)
    # TODO 2: effective_rank: centre z, s = singular values (np.linalg.svd(..., compute_uv=False)), p = s / s.sum()
    #         (if s.sum() == 0 the rank is 0), effective_rank = exp(-sum(p * log(clip(p, 1e-12))))
    raise NotImplementedError("TODO 1-2: collapse_stats")


def diagnose(stats: dict, std_tol: float = 0.01, low_rank_ratio: float = 0.1) -> str:
    # TODO 3: "collapsed" if mean_std < std_tol or effective_rank < 1.5; "low_rank" if effective_rank < low_rank_ratio * dim; else "healthy"
    raise NotImplementedError("TODO 3: diagnose")


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    cases = {"constant": np.ones((200, 16)) + 1e-4 * rng.normal(size=(200, 16)),
             "gaussian": rng.normal(size=(200, 16)),
             "low rank": rng.normal(size=(200, 3)) @ rng.normal(size=(3, 64))}
    for name, z in cases.items():
        st = collapse_stats(z)
        print(f"{name:9s} std={st['mean_std']:.4f} rank={st['effective_rank']:.2f}/{st['dim']} -> {diagnose(st)}")

"""Step 1: patches and block masks for a mini I-JEPA (8x8 digits -> 4x4 grid of 2x2 patches)."""
from __future__ import annotations

import numpy as np

GRID, PATCH = 4, 2


def patchify(img: np.ndarray) -> np.ndarray:
    """(8, 8) image -> (16, 4): patches row by row, pixels inside a patch row by row."""
    # TODO 1: reshape to (GRID, PATCH, GRID, PATCH), swap the two middle axes, flatten to (16, 4)
    raise NotImplementedError("TODO 1: patchify")


def block_mask(rng: np.random.Generator, block: int = 2) -> np.ndarray:
    """keep mask (16,) bool: True = patch is visible. One random block x block square of the 4x4 patch grid is hidden."""
    # TODO 2: keep = np.ones((GRID, GRID), bool); pick a top-left corner r, c with rng.integers(0, GRID - block + 1);
    #         set the block to False; return keep.reshape(-1)
    raise NotImplementedError("TODO 2: block_mask")


if __name__ == "__main__":
    from sklearn.datasets import load_digits
    img = load_digits().images[3] / 16.0
    print("\n".join("".join("#" if v > 0.4 else "." for v in row) for row in img))
    keep = block_mask(np.random.default_rng(0)).reshape(GRID, GRID)
    print("\nmask (X = hidden target):")
    print("\n".join("".join("." if k else "X" for k in row) for row in keep))
    print("patches:", patchify(img).shape)

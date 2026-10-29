import numpy as np

IMG = np.arange(64).reshape(8, 8)


def check_patchify_shape(m):
    """(8, 8) -> (16, 4)"""
    assert m.patchify(IMG).shape == (16, 4), m.patchify(IMG).shape


def check_first_patches(m):
    """patch 0 is the top-left 2x2, patch 1 its right neighbour"""
    p = m.patchify(IMG)
    assert p[0].tolist() == [0, 1, 8, 9], p[0].tolist()
    assert p[1].tolist() == [2, 3, 10, 11], p[1].tolist()
    assert p[4].tolist() == [16, 17, 24, 25], p[4].tolist()


def check_patchify_is_lossless(m):
    """no pixel is lost or duplicated"""
    assert sorted(m.patchify(IMG).reshape(-1).tolist()) == list(range(64))


def check_mask_hides_one_block(m):
    """exactly four patches are hidden"""
    keep = m.block_mask(np.random.default_rng(0))
    assert keep.dtype == bool and keep.shape == (16,), (keep.dtype, keep.shape)
    assert (~keep).sum() == 4, f"{(~keep).sum()} patches hidden"


def check_hidden_block_is_a_square(m):
    """the hidden patches form a 2x2 square in the grid"""
    for seed in range(20):
        hidden = np.argwhere(~m.block_mask(np.random.default_rng(seed)).reshape(4, 4))
        assert hidden[:, 0].max() - hidden[:, 0].min() == 1 and hidden[:, 1].max() - hidden[:, 1].min() == 1, f"seed {seed}: {hidden.tolist()}"


def check_mask_varies_and_block_size(m):
    """different seeds hide different blocks; block=3 hides nine"""
    masks = {m.block_mask(np.random.default_rng(s)).tobytes() for s in range(30)}
    assert len(masks) > 3, "the mask never changes"
    assert (~m.block_mask(np.random.default_rng(1), block=3)).sum() == 9

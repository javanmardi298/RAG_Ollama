import numpy as np

RNG = np.random.default_rng(0)


def check_stats_keys(m):
    """collapse_stats returns mean_std, effective_rank and dim"""
    st = m.collapse_stats(RNG.normal(size=(50, 8)))
    assert set(st) >= {"mean_std", "effective_rank", "dim"} and st["dim"] == 8, st


def check_std_is_across_samples(m):
    """mean_std is measured across samples (axis 0)"""
    z = np.tile(np.arange(5.0), (10, 1))                    # every sample identical, dimensions differ
    assert m.collapse_stats(z)["mean_std"] == 0.0, "std must be taken across samples, not across dimensions"


def check_constant_is_collapsed(m):
    """identical embeddings are collapsed"""
    z = np.ones((100, 16))
    st = m.collapse_stats(z)
    assert st["effective_rank"] == 0.0 or st["effective_rank"] < 1.5, st
    assert m.diagnose(st) == "collapsed", m.diagnose(st)


def check_random_is_healthy(m):
    """isotropic Gaussian embeddings are healthy with rank close to D"""
    st = m.collapse_stats(RNG.normal(size=(500, 16)))
    assert st["effective_rank"] > 12, st
    assert m.diagnose(st) == "healthy", st


def check_low_rank(m):
    """a 3-dimensional cloud inside 64 dimensions is low_rank, not collapsed"""
    z = RNG.normal(size=(400, 3)) @ RNG.normal(size=(3, 64))
    st = m.collapse_stats(z)
    assert 2 < st["effective_rank"] < 4, st
    assert m.diagnose(st) == "low_rank", (m.diagnose(st), st)


def check_one_direction_is_collapsed(m):
    """everything on one line: dimensional collapse"""
    z = RNG.normal(size=(200, 1)) @ RNG.normal(size=(1, 32))
    assert m.diagnose(m.collapse_stats(z)) == "collapsed"

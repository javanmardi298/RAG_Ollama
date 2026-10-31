"""JEPA lab: tiny runs that check the mechanics (shapes, collapse diagnostics, planning beats random)."""
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("sklearn")

from jepa_lab.sigreg import collapse_stats, sigreg  # noqa: E402
from jepa_lab.ssl import Encoder, linear_probe, load_digits_patches, sample_masks, train  # noqa: E402
from jepa_lab.world_model import DotWorld, evaluate_planning, surprise_auc, train_world_model  # noqa: E402


def test_sigreg_prefers_gaussian_over_collapsed():
    g = torch.Generator().manual_seed(0)
    gauss = torch.randn(512, 16, generator=g)
    collapsed = torch.zeros(512, 16) + 0.01 * torch.randn(512, 16, generator=g)
    assert sigreg(gauss, generator=g) < sigreg(collapsed, generator=g)
    assert collapse_stats(gauss)["effective_rank"] > 10 > collapse_stats(collapsed[:, :1] * torch.ones(1, 16))["effective_rank"]


def test_masks_and_encoder_shapes():
    keep = sample_masks(5, torch.Generator().manual_seed(0))
    assert keep.shape == (5, 16) and (keep.sum(1) == 12).all()          # one 2x2 block of 16 patches hidden
    x = load_digits_patches()[0][:5]
    assert Encoder(32)(x, keep).shape == (5, 16, 32)


def test_ssl_variants_train_and_probe():
    data = load_digits_patches()
    small = (data[0][:256], data[1][:256], data[2][:128], data[3][:128])
    for v in ["ema", "sigreg", "naive", "pixel"]:
        r = train(v, epochs=1, dim=32, data=small)
        assert r["history"][0]["loss"] >= 0
    assert 0.0 <= linear_probe(r["encoder"], small) <= 1.0
    with pytest.raises(ValueError):
        train("nope")


def test_world_model_plans_and_detects_surprise():
    r = train_world_model(n=1500, epochs=15, seed=0)
    m, w = r["model"], r["world"]
    cem = evaluate_planning(m, w, episodes=6, planner="cem")["success_rate"]
    rnd = evaluate_planning(m, w, episodes=6, planner="random")["success_rate"]
    assert cem > rnd
    assert surprise_auc(m, DotWorld(seed=5), n=400)["auc"] > 0.8

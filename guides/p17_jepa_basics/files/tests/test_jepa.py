import torch

from jepa import Encoder, collapse_stats, linear_probe, load_digits_patches, sample_masks, sigreg, train


def test_masks_hide_one_block():
    keep = sample_masks(5, torch.Generator().manual_seed(0))
    assert keep.shape == (5, 16) and (keep.sum(1) == 12).all()


def test_encoder_shape():
    x = load_digits_patches()[0][:3]
    assert Encoder(32)(x).shape == (3, 16, 32)


def test_sigreg_prefers_gaussian_and_stats_detect_collapse():
    g = torch.Generator().manual_seed(0)
    gauss = torch.randn(512, 16, generator=g)
    flat = 0.01 * torch.randn(512, 16, generator=g)
    assert sigreg(gauss, generator=g) < sigreg(flat, generator=g)
    assert collapse_stats(gauss)["mean_std"] > 0.5 > collapse_stats(flat)["mean_std"]


def test_every_variant_trains_one_epoch():
    data = load_digits_patches()
    small = (data[0][:256], data[1][:256], data[2][:128], data[3][:128])
    for v in ["ema", "sigreg", "naive", "pixel"]:
        assert train(v, epochs=1, dim=32, data=small)["history"][0]["loss"] >= 0
    assert 0 <= linear_probe(None, small) <= 1

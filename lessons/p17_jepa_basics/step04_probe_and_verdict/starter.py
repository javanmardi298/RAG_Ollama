"""Step 4: summarise runs over several seeds and give a rule-based verdict."""
from __future__ import annotations

BASELINES = {"raw_pixels", "random_encoder"}


def summarize(rows: list[dict]) -> dict:
    """rows: [{"run": "ema", "probe": 0.81}, ...] (one row per run and seed) -> {"ema": {"mean", "min", "max", "n"}, ...}"""
    # TODO 1: group the probe values by run name and compute mean, min, max and the count n
    raise NotImplementedError("TODO 1: summarize")


def verdict(summary: dict, margin: float = 0.02, max_range: float = 0.1) -> dict:
    """{"best_learned": name | None, "pixels_win": bool, "beats_random": [names], "unstable": [names]}"""
    # TODO 2: learned = runs that are not in BASELINES; best_learned = the learned run with the highest mean (None if none)
    #         pixels_win = raw_pixels exists and its mean >= the best learned mean (False when raw_pixels is missing)
    #         beats_random = learned runs with mean >= random_encoder mean + margin (empty when random_encoder is missing)
    #         unstable = learned runs with max - min > max_range
    raise NotImplementedError("TODO 2: verdict")


if __name__ == "__main__":
    import torch

    from jepa_lab.ssl import Encoder, linear_probe, load_digits_patches, train

    rows = []
    for seed in (7, 8):
        data = load_digits_patches(seed)
        torch.manual_seed(seed)
        rows += [{"run": "raw_pixels", "probe": linear_probe(None, data)},
                 {"run": "random_encoder", "probe": linear_probe(Encoder(64).eval(), data)}]
        for variant in ("ema", "sigreg", "pixel"):
            rows.append({"run": variant, "probe": linear_probe(train(variant, epochs=15, seed=seed, data=data)["encoder"], data)})
            print("seed", seed, variant, round(rows[-1]["probe"], 3), flush=True)
    summ = summarize(rows)
    for name, s in sorted(summ.items(), key=lambda kv: -kv[1]["mean"]):
        print(f"{name:15s} {s['mean']:.3f}  [{s['min']:.3f}, {s['max']:.3f}]  n={s['n']}")
    print("verdict:", verdict(summ))

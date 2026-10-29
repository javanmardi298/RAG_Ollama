"""Step 4: summarise runs over several seeds and give a rule-based verdict."""
from __future__ import annotations

BASELINES = {"raw_pixels", "random_encoder"}


def summarize(rows: list[dict]) -> dict:
    """rows: [{"run": "ema", "probe": 0.81}, ...] (one row per run and seed) -> {"ema": {"mean", "min", "max", "n"}, ...}"""
    groups: dict[str, list[float]] = {}
    for r in rows:
        groups.setdefault(r["run"], []).append(r["probe"])
    return {k: {"mean": sum(v) / len(v), "min": min(v), "max": max(v), "n": len(v)} for k, v in groups.items()}


def verdict(summary: dict, margin: float = 0.02, max_range: float = 0.1) -> dict:
    """{"best_learned": name | None, "pixels_win": bool, "beats_random": [names], "unstable": [names]}"""
    learned = {k: v for k, v in summary.items() if k not in BASELINES}
    best = max(learned, key=lambda k: learned[k]["mean"]) if learned else None
    pixels_win = "raw_pixels" in summary and best is not None and summary["raw_pixels"]["mean"] >= learned[best]["mean"]
    rand = summary.get("random_encoder")
    beats = [k for k, v in learned.items() if rand and v["mean"] >= rand["mean"] + margin]
    unstable = [k for k, v in learned.items() if v["max"] - v["min"] > max_range]
    return {"best_learned": best, "pixels_win": pixels_win, "beats_random": beats, "unstable": unstable}


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

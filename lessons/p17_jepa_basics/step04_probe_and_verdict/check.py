ROWS = [{"run": "raw_pixels", "probe": 0.96}, {"run": "raw_pixels", "probe": 0.97},
        {"run": "random_encoder", "probe": 0.80}, {"run": "random_encoder", "probe": 0.82},
        {"run": "ema", "probe": 0.84}, {"run": "ema", "probe": 0.86},
        {"run": "sigreg", "probe": 0.70}, {"run": "sigreg", "probe": 0.93}]


def check_summarize(m):
    """mean, min, max and n per run"""
    s = m.summarize(ROWS)
    assert set(s) == {"raw_pixels", "random_encoder", "ema", "sigreg"}, set(s)
    assert abs(s["ema"]["mean"] - 0.85) < 1e-9 and s["ema"]["min"] == 0.84 and s["ema"]["max"] == 0.86 and s["ema"]["n"] == 2, s["ema"]


def check_best_learned_ignores_baselines(m):
    """the best learned run is not a baseline"""
    v = m.verdict(m.summarize(ROWS))
    assert v["best_learned"] == "ema", v          # sigreg mean 0.815 < ema 0.85 ; raw_pixels is a baseline


def check_pixels_win(m):
    """raw pixels beat the best learned run here"""
    assert m.verdict(m.summarize(ROWS))["pixels_win"] is True


def check_beats_random(m):
    """only runs at least `margin` above the random encoder"""
    v = m.verdict(m.summarize(ROWS), margin=0.02)
    assert v["beats_random"] == ["ema"], v
    assert m.verdict(m.summarize(ROWS), margin=0.0)["beats_random"] == ["ema", "sigreg"]


def check_unstable(m):
    """a run with a wide range across seeds is flagged"""
    v = m.verdict(m.summarize(ROWS), max_range=0.1)
    assert v["unstable"] == ["sigreg"], v


def check_missing_baselines_do_not_crash(m):
    """no baselines -> pixels_win False, beats_random empty"""
    v = m.verdict(m.summarize([{"run": "ema", "probe": 0.9}]))
    assert v == {"best_learned": "ema", "pixels_win": False, "beats_random": [], "unstable": []}, v
    assert m.verdict({})["best_learned"] is None

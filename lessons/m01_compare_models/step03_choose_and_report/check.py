ROWS = [{"model": "local", "accuracy": 0.75, "mean_latency_s": 1.2, "errors": 0, "n": 4},
        {"model": "cloud_fast", "accuracy": 1.0, "mean_latency_s": 0.9, "errors": 0, "n": 4},
        {"model": "cloud_slow", "accuracy": 1.0, "mean_latency_s": 3.0, "errors": 0, "n": 4},
        {"model": "flaky", "accuracy": 1.0, "mean_latency_s": 0.1, "errors": 1, "n": 4},
        {"model": "dead", "accuracy": 0.0, "mean_latency_s": None, "errors": 4, "n": 4}]


def check_choose_fastest_qualified(m):
    """fastest among models that meet the rule (flaky and local are out)"""
    assert m.choose(ROWS) == "cloud_fast", m.choose(ROWS)


def check_choose_none(m):
    """nobody qualifies -> None"""
    assert m.choose(ROWS, min_accuracy=1.1) is None
    assert m.choose([]) is None


def check_choose_threshold_parameters(m):
    """thresholds are parameters"""
    assert m.choose(ROWS, min_accuracy=0.7) == "cloud_fast"
    assert m.choose(ROWS, min_accuracy=1.0, max_errors=1) == "flaky"


def check_tie_breaks(m):
    """tie on latency: higher accuracy, then name"""
    rows = [{"model": "b", "accuracy": 0.9, "mean_latency_s": 1.0, "errors": 0, "n": 1},
            {"model": "a", "accuracy": 0.9, "mean_latency_s": 1.0, "errors": 0, "n": 1},
            {"model": "c", "accuracy": 1.0, "mean_latency_s": 1.0, "errors": 0, "n": 1}]
    assert m.choose(rows) == "c"
    assert m.choose(rows[:2]) == "a"


def check_table_format(m):
    """header, separator, sorted rows, 2 decimals, '-' for missing latency"""
    t = m.markdown_table(ROWS).splitlines()
    assert t[0] == "| model | accuracy | latency (s) | errors |" and t[1] == "|---|---|---|---|", t[:2]
    assert t[2] == "| cloud_fast | 1.00 | 0.90 | 0 |", t[2]
    assert t[-1] == "| dead | 0.00 | - | 4 |", t[-1]


def check_table_sorting(m):
    """sorted by accuracy descending, ties by name"""
    names = [line.split("|")[1].strip() for line in m.markdown_table(ROWS).splitlines()[2:]]
    assert names == ["cloud_fast", "cloud_slow", "flaky", "local", "dead"], names

"""Step 3: choose a model with a rule fixed in advance, and print a report table."""
from __future__ import annotations


def choose(rows: list[dict], min_accuracy: float = 0.8, max_errors: int = 0):
    """Among rows with accuracy >= min_accuracy, errors <= max_errors and a measured latency, return the NAME of the fastest
    (ties: higher accuracy, then name). None if no row qualifies."""
    ok = [r for r in rows if r["accuracy"] >= min_accuracy and r["errors"] <= max_errors and r["mean_latency_s"] is not None]
    if not ok:
        return None
    return min(ok, key=lambda r: (r["mean_latency_s"], -r["accuracy"], r["model"]))["model"]


def markdown_table(rows: list[dict]) -> str:
    """'| model | accuracy | latency (s) | errors |' header, separator, then rows sorted by accuracy descending (ties: name).
    accuracy with 2 decimals; latency with 2 decimals or '-' when None."""
    lines = ["| model | accuracy | latency (s) | errors |", "|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (-r["accuracy"], r["model"])):
        lat = "-" if r["mean_latency_s"] is None else f"{r['mean_latency_s']:.2f}"
        lines.append(f"| {r['model']} | {r['accuracy']:.2f} | {lat} | {r['errors']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    rows = [{"model": "ollama:qwen2.5:7b", "accuracy": 0.75, "mean_latency_s": 1.2, "errors": 0, "n": 4},
            {"model": "anthropic:claude", "accuracy": 1.0, "mean_latency_s": 0.9, "errors": 0, "n": 4},
            {"model": "opencode:x/y", "accuracy": 1.0, "mean_latency_s": 3.0, "errors": 0, "n": 4}]
    print(markdown_table(rows))
    print("chosen:", choose(rows))

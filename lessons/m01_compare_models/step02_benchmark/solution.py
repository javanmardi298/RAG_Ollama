"""Step 2: the same cases on every model: accuracy, latency, errors."""
from __future__ import annotations

import os
import time

CASES = [
    {"prompt": "What is 17 + 25? Answer with the number only.", "check": lambda a: "42" in a},
    {"prompt": "What is the capital of France? One word.", "check": lambda a: "paris" in a.lower()},
    {"prompt": "Translate 'good morning' to German. Two words.", "check": lambda a: "guten morgen" in a.lower()},
    {"prompt": "Return only the word YES if 9 is greater than 3, otherwise NO.", "check": lambda a: a.strip().upper().startswith("YES")},
]


def run_benchmark(models: dict, cases: list[dict], repeats: int = 1) -> list[dict]:
    """models: name -> object with .chat(messages).content. Returns one row per model:
    {"model", "accuracy", "mean_latency_s", "errors", "n"}"""
    rows = []
    for name, llm in models.items():
        correct = errors = 0
        times: list[float] = []
        n = 0
        for case in cases:
            for _ in range(repeats):
                n += 1
                start = time.perf_counter()
                try:
                    answer = llm.chat([{"role": "user", "content": case["prompt"]}]).content
                except Exception:
                    errors += 1
                    continue
                times.append(time.perf_counter() - start)
                correct += bool(case["check"](answer))
        rows.append({"model": name, "accuracy": correct / n if n else 0.0, "mean_latency_s": sum(times) / len(times) if times else None,
                     "errors": errors, "n": n})
    return rows


def build_models(spec: str) -> dict:
    """'offline,ollama:qwen2.5:7b,anthropic:claude-sonnet-5-5' -> {name: llm}; unavailable ones are skipped with a reason."""
    from learn import llm as learn_llm
    out = {}
    for item in filter(None, (x.strip() for x in spec.split(","))):
        provider, _, model = item.partition(":")
        try:
            out[item] = learn_llm.get(provider, model)
        except Exception as e:
            print(f"skipped {item}: {e}")
    return out


if __name__ == "__main__":
    models = build_models(os.environ.get("COMPARE", "offline"))
    for r in run_benchmark(models, CASES):
        print(r)

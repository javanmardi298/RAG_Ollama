"""Prompt optimisation in the style of GEPA (Genetic-Pareto reflective prompt evolution, ICLR 2026) and DSPy.

Idea: treat the prompt as a parameter. Run it on training examples, collect per-example scores AND textual
feedback (why it failed), ask an LLM to reflect on the failures and propose an edited prompt, keep every
candidate that is best on at least one example (the Pareto front), and repeat within a budget.

What practice added: optimisers overfit. One case study saw train accuracy rise to 95% while test fell to 85%
and the prompt grew from ~2,400 to ~8,800 characters. So this implementation
* selects the final prompt on a separate VALIDATION set, never on the training examples,
* penalises length (a longer prompt must earn its tokens),
* returns the whole history, so you can see when it started to overfit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

Example = dict
Score = tuple[float, str]                       # (0..1, feedback text)


@dataclass
class Candidate:
    prompt: str
    train_scores: list[float]
    val_score: float | None = None
    parent: int | None = None
    feedback: list[str] = field(default_factory=list)

    @property
    def train_mean(self) -> float:
        return sum(self.train_scores) / len(self.train_scores) if self.train_scores else 0.0


def pareto_front(cands: list[Candidate]) -> list[int]:
    """Candidates that are best (ties allowed) on at least one training example."""
    n = len(cands[0].train_scores)
    best = [max(c.train_scores[i] for c in cands) for i in range(n)]
    return [j for j, c in enumerate(cands) if any(c.train_scores[i] >= best[i] for i in range(n))]


def optimize(seed_prompt: str, train: list[Example], val: list[Example],
             evaluate: Callable[[str, Example], Score],
             propose: Callable[[str, list[tuple[Example, float, str]]], str],
             budget: int = 8, length_penalty: float = 0.02, pick: Callable[[list[int], int], int] | None = None) -> dict:
    """evaluate(prompt, example) -> (score, feedback); propose(prompt, failures) -> new prompt (LLM reflection).

    budget = number of new candidates. Returns {"best": Candidate, "history": [...], "seed": Candidate}."""
    def run(prompt: str) -> tuple[list[float], list[str]]:
        res = [evaluate(prompt, ex) for ex in train]
        return [s for s, _ in res], [f for _, f in res]

    def val_score(prompt: str) -> float:
        mean = sum(evaluate(prompt, ex)[0] for ex in val) / max(len(val), 1)
        growth = max(0.0, len(prompt) / max(len(seed_prompt), 1) - 1.0)
        return mean - length_penalty * growth

    s, f = run(seed_prompt)
    cands = [Candidate(seed_prompt, s, val_score(seed_prompt), None, f)]
    for step in range(budget):
        front = pareto_front(cands)
        parent = pick(front, step) if pick else front[step % len(front)]
        p = cands[parent]
        failures = [(ex, sc, fb) for ex, sc, fb in zip(train, p.train_scores, p.feedback) if sc < 1.0]
        if not failures:
            break
        child = propose(p.prompt, failures[:5])
        if not child or child in {c.prompt for c in cands}:
            continue
        s, f = run(child)
        cands.append(Candidate(child, s, val_score(child), parent, f))
    best = max(cands, key=lambda c: (c.val_score, -len(c.prompt)))
    return {"best": best, "seed": cands[0], "history": cands}


def llm_proposer(llm) -> Callable[[str, list[tuple[Example, float, str]]], str]:
    """Reflection step: the LLM reads failures with their feedback and rewrites the instruction."""
    def propose(prompt: str, failures: list[tuple[Example, float, str]]) -> str:
        cases = "\n".join(f"- input: {ex.get('input')} | expected: {ex.get('expected')} | feedback: {fb}"
                          for ex, _, fb in failures)
        msg = (f"Current instruction:\n<<<\n{prompt}\n>>>\nIt failed on these cases:\n{cases}\n\n"
               "Write an improved instruction that fixes the general cause of these failures (not each case one by one). "
               "Keep it short. Return only the new instruction.")
        return llm.chat([{"role": "user", "content": msg}]).content.strip()
    return propose

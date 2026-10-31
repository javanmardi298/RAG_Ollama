"""Context engineering: deciding what goes into the model's window, in what order, within a token budget.

Established practice (2025-2026):
* Treat the window as a budget. Rank pieces by priority, never silently drop the system rules or the task.
* Keep the prefix STABLE (system prompt, tool definitions, older turns) so prompt caching hits; put volatile
  material (retrieved chunks, timestamps) at the end. A summary that rewrites the prefix breaks the cache.
* Cheap, deterministic cuts first: truncate huge tool outputs, clear stale tool results, keep ids and numbers.
  Summarise (compaction) only when the cheap cuts are not enough, and check rules survive it.
* Keep memory outside the window (files, a store) and pull it back on demand.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .ops import approx_tokens


@dataclass
class Piece:
    name: str
    text: str
    priority: int             # higher = kept first
    required: bool = False    # system rules, the user's task: never dropped, error if they do not fit
    stable: bool = True       # part of the cacheable prefix (True) or volatile tail (False)
    meta: dict = field(default_factory=dict)


def truncate_tool_output(text: str, max_tokens: int = 400, keep_tail: int = 80) -> str:
    """Head + tail of a long tool result, with a marker saying how much was cut (the model must know)."""
    if approx_tokens(text) <= max_tokens:
        return text
    head_chars, tail_chars = (max_tokens - keep_tail) * 4, keep_tail * 4
    cut = len(text) - head_chars - tail_chars
    return f"{text[:head_chars]}\n[... {cut} characters cut ...]\n{text[-tail_chars:]}"


def clear_stale_tool_results(messages: list[dict], keep_last: int = 3,
                             placeholder: str = "[tool result cleared: re-run the tool if needed]") -> list[dict]:
    """Older tool results are replaced by a short placeholder; the last `keep_last` stay verbatim."""
    idx = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    stale = set(idx[:-keep_last]) if keep_last else set(idx)
    return [{**m, "content": placeholder} if i in stale else m for i, m in enumerate(messages)]


def pack(pieces: list[Piece], budget_tokens: int) -> tuple[list[Piece], dict]:
    """Choose pieces by priority within the budget, then order: stable prefix first, volatile last.

    Returns (kept pieces in send order, report with tokens used and what was dropped)."""
    required = [p for p in pieces if p.required]
    used = sum(approx_tokens(p.text) for p in required)
    if used > budget_tokens:
        raise ValueError(f"required pieces need {used} tokens, budget is {budget_tokens}")
    kept, dropped = list(required), []
    for p in sorted((p for p in pieces if not p.required), key=lambda p: -p.priority):
        t = approx_tokens(p.text)
        if used + t <= budget_tokens:
            kept.append(p)
            used += t
        else:
            dropped.append(p.name)
    order = {id(p): i for i, p in enumerate(pieces)}            # inside each group keep the caller's order
    kept.sort(key=lambda p: (not p.stable, order[id(p)]))
    return kept, {"tokens": used, "budget": budget_tokens, "dropped": dropped}

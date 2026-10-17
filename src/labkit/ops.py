"""Production plumbing for LLM calls: response cache, usage/cost ledger, versioned prompts.

Wrap any LLM with `Metered(llm, ledger, cache, price)`: every call is timed, its tokens and cost recorded,
and identical deterministic calls (temperature 0) are answered from the cache.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import string
import threading
import time
from dataclasses import dataclass
from typing import Callable


def _key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


class Cache:
    """SQLite response cache. Only use it for deterministic calls; a TTL keeps answers from going stale."""

    def __init__(self, path: str = ":memory:", ttl_s: float | None = None):
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.con.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT, ts REAL)")
        self.ttl_s, self.hits, self.misses = ttl_s, 0, 0
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            row = self.con.execute("SELECT v, ts FROM cache WHERE k = ?", (key,)).fetchone()
        if row and (self.ttl_s is None or time.time() - row[1] < self.ttl_s):
            self.hits += 1
            return json.loads(row[0])
        self.misses += 1
        return None

    def put(self, key: str, value) -> None:
        with self._lock, self.con:
            self.con.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)", (key, json.dumps(value), time.time()))


@dataclass
class Price:
    """USD per million tokens (input, output). Local models: 0, but track tokens anyway (latency, capacity)."""
    input_per_m: float = 0.0
    output_per_m: float = 0.0

    def cost(self, tokens_in: int, tokens_out: int) -> float:
        return tokens_in * self.input_per_m / 1e6 + tokens_out * self.output_per_m / 1e6


class Ledger:
    """One row per LLM call: who (feature), which model, tokens, cost, latency, cache hit."""

    def __init__(self, path: str = ":memory:"):
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.con.execute("CREATE TABLE IF NOT EXISTS calls (ts REAL, feature TEXT, model TEXT, tokens_in INTEGER, "
                         "tokens_out INTEGER, cost REAL, latency_s REAL, cached INTEGER)")
        self._lock = threading.Lock()

    def record(self, feature: str, model: str, tokens_in: int, tokens_out: int, cost: float, latency_s: float,
               cached: bool = False) -> None:
        with self._lock, self.con:
            self.con.execute("INSERT INTO calls VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                             (time.time(), feature, model, tokens_in, tokens_out, cost, latency_s, int(cached)))

    def summary(self, by: str = "feature") -> list[dict]:
        if by not in ("feature", "model"):
            raise ValueError("by must be feature or model")
        rows = self.con.execute(f"SELECT {by}, COUNT(*), SUM(tokens_in), SUM(tokens_out), SUM(cost), AVG(latency_s), "
                                f"AVG(cached) FROM calls GROUP BY {by} ORDER BY SUM(cost) DESC")
        return [{by: r[0], "calls": r[1], "tokens_in": r[2], "tokens_out": r[3], "cost": round(r[4], 6),
                 "avg_latency_s": round(r[5], 3), "cache_hit_rate": round(r[6], 3)} for r in rows]


def approx_tokens(text: str) -> int:
    """~4 characters per token for English; good enough for budgeting when the API does not report usage."""
    return max(1, len(text) // 4)


class Metered:
    """Wraps an LLM with .chat(messages, ...) -> reply(.content). Adds cache, ledger and latency."""

    def __init__(self, llm, ledger: Ledger, cache: Cache | None = None, price: Price = Price(),
                 feature: str = "default"):
        self.llm, self.ledger, self.cache, self.price, self.feature = llm, ledger, cache, price, feature
        self.model = getattr(llm, "model", "unknown")

    def chat(self, messages: list[dict], **kw):
        deterministic = getattr(self.llm, "temperature", 0) == 0 and not kw.get("tools")
        key = _key(self.model, messages, kw) if self.cache and deterministic else None
        if key and (hit := self.cache.get(key)) is not None:
            self.ledger.record(self.feature, self.model, 0, 0, 0.0, 0.0, cached=True)
            return type("Reply", (), {"content": hit, "tool_calls": [], "latency_s": 0.0})()
        start = time.perf_counter()
        reply = self.llm.chat(messages, **kw)
        latency = time.perf_counter() - start
        t_in = approx_tokens(" ".join(str(m.get("content", "")) for m in messages))
        t_out = approx_tokens(reply.content or "")
        self.ledger.record(self.feature, self.model, t_in, t_out, self.price.cost(t_in, t_out), latency)
        if key and reply.content and not getattr(reply, "tool_calls", None):
            self.cache.put(key, reply.content)
        return reply


class PromptRegistry:
    """Prompts as versioned templates. The version is a hash of the text, so results can name the exact prompt."""

    def __init__(self):
        self._prompts: dict[str, dict[str, str]] = {}

    def register(self, name: str, template: str) -> str:
        version = hashlib.sha256(template.encode()).hexdigest()[:8]
        self._prompts.setdefault(name, {})[version] = template
        return version

    def render(self, name: str, version: str | None = None, **values) -> tuple[str, str]:
        versions = self._prompts[name]
        version = version or list(versions)[-1]
        fields = {f for _, f, _, _ in string.Formatter().parse(versions[version]) if f}
        missing = fields - set(values)
        if missing:
            raise KeyError(f"prompt {name}@{version} needs: {', '.join(sorted(missing))}")
        return versions[version].format(**values), version

    def versions(self, name: str) -> list[str]:
        return list(self._prompts.get(name, {}))


class Router:
    """Cheap model first, strong model only when needed (cost and latency vs quality).

    `accept(reply)` decides if the cheap answer is good enough: valid JSON, a confidence above a threshold,
    passing the output guardrail... Record escalation rate: if most calls escalate, the cheap model is not worth it.
    """

    def __init__(self, cheap, strong, accept: Callable[[object], bool], ledger: Ledger | None = None):
        self.cheap, self.strong, self.accept, self.ledger = cheap, strong, accept, ledger
        self.calls = self.escalations = 0

    def chat(self, messages: list[dict], **kw):
        self.calls += 1
        try:
            reply = self.cheap.chat(messages, **kw)
            if self.accept(reply):
                return reply
        except Exception:
            pass                                   # a failing cheap model is also a reason to escalate
        self.escalations += 1
        return self.strong.chat(messages, **kw)

    @property
    def escalation_rate(self) -> float:
        return self.escalations / self.calls if self.calls else 0.0

"""Prompt-injection defence by design (in the spirit of CaMeL, Debenedetti et al. 2025).

Filters that try to SPOT injected text fail against adaptive attacks. The design-level defence:
* a privileged planner sees only the trusted user request and decides WHICH tools to call;
* untrusted content (emails, web pages, documents, tool results) is processed by a quarantined step with no
  tools, and every value it produces carries its provenance ("tainted");
* before each tool call, a policy written in CODE checks the arguments' provenance: e.g. a payment recipient
  or an email address must come from the user or a trusted record, never from a web page.

This module gives the provenance-tracking values and the policy check. Known limits: it protects control
and data flow, not the quality of the text; and it costs extra calls (CaMeL reported ~2.8x tokens).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Value:
    value: Any
    sources: frozenset = field(default_factory=frozenset)   # e.g. {"user"}, {"web:example.com"}, {"db:orders"}

    @property
    def trusted(self) -> bool:
        return bool(self.sources) and all(s == "user" or s.startswith(("db:", "system")) for s in self.sources)


def from_user(v) -> Value:
    return Value(v, frozenset({"user"}))


def from_untrusted(v, source: str) -> Value:
    return Value(v, frozenset({source}))


def derive(fn: Callable, *inputs: Value) -> Value:
    """Any value computed from others inherits ALL their sources (taint propagates)."""
    return Value(fn(*[i.value for i in inputs]), frozenset().union(*[i.sources for i in inputs]))


class PolicyViolation(Exception):
    pass


@dataclass
class Policy:
    """tool name -> argument names that must be trusted (come from the user or a trusted store)."""
    trusted_args: dict[str, set[str]]
    needs_confirmation: set[str] = field(default_factory=set)

    def check(self, tool: str, args: dict[str, Value], confirmed: bool = False) -> None:
        for name in self.trusted_args.get(tool, set()):
            v = args.get(name)
            if v is None or not v.trusted:
                src = sorted(v.sources) if v else "missing"
                raise PolicyViolation(f"{tool}.{name} must come from the user or a trusted record (got {src})")
        if tool in self.needs_confirmation and not confirmed:
            raise PolicyViolation(f"{tool} needs the user's explicit confirmation")


def call_tool(policy: Policy, tool: str, fn: Callable, args: dict[str, Value], confirmed: bool = False):
    """Check the policy, then call the real tool with plain values; the result is tainted as tool output."""
    policy.check(tool, args, confirmed)
    return Value(fn(**{k: v.value for k, v in args.items()}), frozenset({f"tool:{tool}"}))

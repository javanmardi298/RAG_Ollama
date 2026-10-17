"""Routing logic of the LangGraph graph, as plain functions.

LangGraph calls these to choose the next node (conditional edges). Keeping them free of
LangGraph imports means they are unit-tested like any other function (tests/test_lc_routing.py),
and the same decision code serves both the plain agent and the graph.
"""
from __future__ import annotations

from ..config import intent_map
from ..decision import Action, DecisionInput, decide
from ..tools import NEEDS_CONFIRMATION

END = "__end__"           # same value as langgraph.graph.END
MAX_AGENT_STEPS = 5
MAX_OUTPUT_RETRIES = 1


def decide_route(intent: str, confidence: float, flags: list[str], failed_turns: int,
                 clarifications: int, thresholds: dict | None = None) -> tuple[str, str]:
    """Map the stage-4 decision onto a node name."""
    action, reason = decide(DecisionInput(intent, confidence, tuple(flags), failed_turns, clarifications), thresholds)
    if action is Action.HANDOFF:
        return "handoff", reason
    if action is Action.DECLINE:
        return "decline", reason
    if action is Action.CLARIFY:
        return "clarify", reason
    route = intent_map().get(intent, {}).get("route")
    return ("rag" if route == "rag" else "agent"), reason


def _tool_calls(message) -> list[dict]:
    calls = getattr(message, "tool_calls", None)
    if calls is None and isinstance(message, dict):
        calls = message.get("tool_calls")
    return list(calls or [])


def after_decide(state: dict) -> str:
    return state["route"]


def after_agent(state: dict) -> str:
    calls = _tool_calls(state["messages"][-1])
    if not calls:
        return "guard_output"
    if any(c["name"] in NEEDS_CONFIRMATION for c in calls):
        return "confirm"
    return "tools"


def after_tools(state: dict) -> str:
    if state.get("handoff_reason"):
        return "handoff"
    if state.get("steps", 0) >= MAX_AGENT_STEPS:
        return "handoff"
    return "agent"


def after_output(state: dict) -> str:
    if state.get("output_ok"):
        return END
    if state.get("output_retries", 0) <= MAX_OUTPUT_RETRIES:
        return "agent"
    return "handoff"


def after_rag(state: dict) -> str:
    return END if state.get("answered") else "handoff"

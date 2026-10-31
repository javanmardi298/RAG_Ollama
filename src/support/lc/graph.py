"""Stages 3-5 with LangGraph: the support agent as an explicit state graph.

                    ┌────────────┐
   user message ──▶ │ guard_input│──▶ classify ──▶ decide ──┬──▶ rag ───────────────┬──▶ END
                    └────────────┘                          ├──▶ clarify ──▶ END     └──▶ handoff
                                                            ├──▶ decline ──▶ END
                                                            ├──▶ handoff ──▶ END
                                                            └──▶ agent ──┬──▶ guard_output ──▶ END / agent / handoff
                                                                  ▲      ├──▶ confirm (interrupt) ──▶ tools
                                                                  └──────┴──▶ tools ──▶ agent / handoff

Same behaviour as support.agent.SupportAgent, but:
* the control flow is data (nodes + edges) that LangGraph can draw, stream, trace and resume,
* conversation state lives in a checkpointer (memory, SQLite, Postgres) keyed by thread_id,
* the confirmation step uses interrupt(): the graph pauses, the API returns the question,
  and the next customer message resumes the graph with Command(resume=...).
"""
from __future__ import annotations

import json
import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Callable

from langchain_core.messages import (AIMessage, AnyMessage, HumanMessage, RemoveMessage, SystemMessage,
                                     ToolMessage)
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
from typing_extensions import TypedDict

from ..agent import SLOT_ONLY, SYSTEM_PROMPT, TEXT, YES
from ..config import DB_PATH
from ..guardrails import allowed_numbers, check_input, check_output, mask_pii
from ..robustness import detect_language
from ..tools import NEEDS_CONFIRMATION, TOOL_SCHEMAS, ToolBox, connect
from . import routing


class SupportState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]   # reducer: new messages are appended
    facts: Annotated[list[dict], operator.add]            # reducer: tool results accumulate
    language: str
    intent: str | None
    confidence: float
    flags: list[str]
    blocked: bool
    route: str
    reason: str
    customer_id: str | None          # set only after verify_customer succeeded
    customer_email: str | None
    clarifications: int
    failed_turns: int
    steps: int                       # agent steps in this turn
    confirmed: bool
    output_ok: bool
    output_retries: int
    output_feedback: str | None
    answered: bool
    handoff_reason: str | None
    handoff_order: str | None
    ticket_id: int | None
    closed: bool


@dataclass
class Deps:
    """Everything the nodes need from outside. Passed in, so tests can use fakes."""
    model: Any                                   # a LangChain chat model (ChatOllama or a fake)
    classify: Callable[[str], tuple[str, float]]
    answer_policy: Callable[[str, str], dict] | None = None
    db_path: str | Path = DB_PATH
    thresholds: dict | None = None
    tools_schema: list = field(default_factory=lambda: TOOL_SCHEMAS)


def _last_human(state) -> str:
    return next(m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage))


def build_graph(deps: Deps, checkpointer=None):
    def toolbox(state) -> ToolBox:
        tb = ToolBox(connect(deps.db_path))
        tb.customer_id = state.get("customer_id")      # identity comes from saved state, not from the LLM
        return tb

    # ---------- nodes: each returns only the keys it changes ----------
    def guard_input(state):
        text = _last_human(state)
        verdict = check_input(text)
        return {"flags": verdict.flags, "blocked": verdict.blocked,
                "language": detect_language(text) or state.get("language") or "en",
                "steps": 0, "output_retries": 0, "output_feedback": None, "output_ok": False,
                "handoff_reason": None, "confirmed": False, "answered": False}

    def classify(state):
        text = _last_human(state)
        intent, conf = deps.classify(text)
        if state.get("intent") and SLOT_ONLY.search(text) and len(text.split()) <= 8:
            intent, conf = state["intent"], max(conf, 0.9)
        return {"intent": intent, "confidence": conf}

    def decide(state):
        if state.get("blocked"):
            return {"route": "clarify", "reason": "blocked_input"}
        route, reason = routing.decide_route(state["intent"], state["confidence"], state.get("flags", []),
                                             state.get("failed_turns", 0), state.get("clarifications", 0),
                                             deps.thresholds)
        if route == "handoff":
            return {"route": route, "reason": reason, "handoff_reason": reason}
        return {"route": route, "reason": reason}

    def rag(state):
        res = deps.answer_policy(_last_human(state), state["language"]) if deps.answer_policy else {"answer": None}
        if res.get("answer"):
            return {"messages": [AIMessage(res["answer"])], "answered": True}
        return {"answered": False, "handoff_reason": "no_policy_answer"}

    def clarify(state):
        return {"messages": [AIMessage(TEXT["clarify"][state["language"]])],
                "clarifications": state.get("clarifications", 0) + 1}

    def decline(state):
        return {"messages": [AIMessage(TEXT["decline"][state["language"]])]}

    def agent(state):
        lang = "German" if state["language"] == "de" else "English"
        model = deps.model
        if "prompt_injection" not in state.get("flags", []):        # injection turn: no tools at all
            model = model.bind_tools(deps.tools_schema)
        msgs = [SystemMessage(SYSTEM_PROMPT.format(language=lang))] + state["messages"]
        if state.get("output_feedback"):
            msgs.append(HumanMessage(state["output_feedback"]))
        return {"messages": [model.invoke(msgs)], "steps": state.get("steps", 0) + 1}

    def confirm(state):
        # Nothing with side effects before interrupt(): on resume this node runs again from the top.
        call = next(c for c in state["messages"][-1].tool_calls if c["name"] in NEEDS_CONFIRMATION)
        what = TEXT["what"][call["name"]][state["language"]]
        question = TEXT["confirm"][state["language"]].format(what=what, order_id=call["args"].get("order_id", "?"))
        reply = interrupt({"question": question, "tool": call["name"], "args": call["args"]})
        return {"confirmed": bool(YES.search(str(reply)))}

    def tools(state):
        tb = toolbox(state)
        update, messages, facts = {}, [], []
        for call in state["messages"][-1].tool_calls:
            if call["name"] in NEEDS_CONFIRMATION and not state.get("confirmed"):
                result = {"ok": False, "reason": "customer_declined", "facts": {}}
            else:
                result = tb.call(call["name"], call["args"])
            if call["name"] == "verify_customer" and result["ok"]:
                update.update(customer_id=tb.customer_id, customer_email=call["args"].get("email"))
            if call["name"] == "handoff" and result["ok"]:
                update.update(ticket_id=result["facts"]["ticket_id"], handoff_reason=call["args"].get("reason", "agent"))
            if result["facts"].get("needs_human"):
                update.update(handoff_reason=result["reason"], handoff_order=call["args"].get("order_id"))
            facts.append(result)
            messages.append(ToolMessage(json.dumps(result, ensure_ascii=False), tool_call_id=call["id"], name=call["name"]))
        if state.get("steps", 0) >= routing.MAX_AGENT_STEPS and not update.get("handoff_reason"):
            update.update(handoff_reason="tool_step_limit", failed_turns=state.get("failed_turns", 0) + 1)
        return {**update, "messages": messages, "facts": facts, "confirmed": False}

    def guard_output(state):
        answer = state["messages"][-1]
        users = " ".join(m.content for m in state["messages"] if isinstance(m, HumanMessage))
        verdict = check_output(answer.content, allowed_numbers(*state.get("facts", []), {"t": users}),
                               state.get("customer_email"))
        if verdict.ok:
            return {"output_ok": True, "output_feedback": None}
        retries = state.get("output_retries", 0) + 1
        update = {"output_ok": False, "output_retries": retries,
                  "output_feedback": "[system] Your answer contained facts not supported by tool results "
                                     f"({', '.join(verdict.problems)}). Rewrite it using only tool results.",
                  "messages": [RemoveMessage(id=answer.id)]}      # drop the bad answer from the history
        if retries > routing.MAX_OUTPUT_RETRIES:
            update.update(handoff_reason="output_check_failed", failed_turns=state.get("failed_turns", 0) + 1)
        return update

    def handoff(state):
        ticket = state.get("ticket_id")
        if not ticket:
            transcript = "\n".join(f"{m.type}: {mask_pii(str(m.content))}" for m in state["messages"][-10:])
            ticket = toolbox(state).handoff(reason=state.get("handoff_reason") or "unknown",
                                            summary=f"intent={state.get('intent')}\n{transcript}",
                                            order_id=state.get("handoff_order"))["facts"]["ticket_id"]
        return {"messages": [AIMessage(TEXT["handoff"][state["language"]].format(ticket_id=ticket))],
                "ticket_id": ticket, "closed": True}

    # ---------- wiring ----------
    g = StateGraph(SupportState)
    for name, fn in [("guard_input", guard_input), ("classify", classify), ("decide", decide), ("rag", rag),
                     ("clarify", clarify), ("decline", decline), ("agent", agent), ("confirm", confirm),
                     ("tools", tools), ("guard_output", guard_output), ("handoff", handoff)]:
        g.add_node(name, fn)
    g.add_edge(START, "guard_input")
    g.add_edge("guard_input", "classify")
    g.add_edge("classify", "decide")
    g.add_conditional_edges("decide", routing.after_decide,
                            {"rag": "rag", "agent": "agent", "clarify": "clarify", "decline": "decline", "handoff": "handoff"})
    g.add_conditional_edges("rag", routing.after_rag, {routing.END: END, "handoff": "handoff"})
    g.add_conditional_edges("agent", routing.after_agent,
                            {"guard_output": "guard_output", "confirm": "confirm", "tools": "tools"})
    g.add_edge("confirm", "tools")
    g.add_conditional_edges("tools", routing.after_tools, {"agent": "agent", "handoff": "handoff"})
    g.add_conditional_edges("guard_output", routing.after_output, {routing.END: END, "agent": "agent", "handoff": "handoff"})
    for terminal in ("clarify", "decline", "handoff"):
        g.add_edge(terminal, END)
    return g.compile(checkpointer=checkpointer)


class GraphSupportAgent:
    """Same interface as SupportAgent.reply(session, text), so stage-6 evaluation runs unchanged."""

    def __init__(self, graph, trace: Callable[[dict], None] | None = None):
        self.graph = graph
        self.trace = trace or (lambda e: None)

    def reply(self, session, text: str) -> str:
        config = {"configurable": {"thread_id": session.session_id}}
        paused = bool(self.graph.get_state(config).next)          # waiting at confirm (interrupt)?
        inp = Command(resume=text) if paused else {"messages": [HumanMessage(text)]}
        result = self.graph.invoke(inp, config)
        if result.get("__interrupt__"):
            out = result["__interrupt__"][0].value["question"]
        else:
            out = next(m.content for m in reversed(result["messages"]) if isinstance(m, AIMessage) and m.content)
        session.closed = bool(result.get("closed"))
        session.facts = result.get("facts", [])
        session.customer_email = result.get("customer_email")
        session.intent = result.get("intent")
        self.trace({"session": session.session_id, "user": mask_pii(text), "bot": mask_pii(out),
                    "route": result.get("route"), "intent": result.get("intent"), "flags": result.get("flags")})
        return out

"""Stage 3 baseline with LangChain's create_agent: one LLM, all tools, no router.

This is the "single agent" design from the comparison table: fewer lines, the model decides
everything. Human-in-the-loop middleware pauses before state-changing tools.
Run it on the same stage-6 scenarios as the graph to see what the router actually buys.
"""
from __future__ import annotations

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from ..agent import SYSTEM_PROMPT, YES
from ..tools import NEEDS_CONFIRMATION, ToolBox, connect
from .tools_lc import make_lc_tools


def make_baseline_agent(model, db_path, language: str = "English"):
    toolbox = ToolBox(connect(db_path))                 # one ToolBox (and identity) per conversation
    agent = create_agent(
        model=model,
        tools=make_lc_tools(toolbox),
        system_prompt=SYSTEM_PROMPT.format(language=language),
        middleware=[HumanInTheLoopMiddleware(
            interrupt_on={name: {"allowed_decisions": ["approve", "reject"]} for name in NEEDS_CONFIRMATION})],
        checkpointer=InMemorySaver(),                   # interrupts need a checkpointer
    )
    return agent, toolbox


class BaselineAgent:
    """Adapter with the same .reply(session, text) interface as the other two agents."""

    def __init__(self, agent):
        self.agent = agent

    def reply(self, session, text: str) -> str:
        config = {"configurable": {"thread_id": session.session_id}}
        if self.agent.get_state(config).next:           # paused by the human-in-the-loop middleware
            decision = {"type": "approve"} if YES.search(text) else {"type": "reject", "message": "Customer said no."}
            result = self.agent.invoke(Command(resume={"decisions": [decision]}), config)
        else:
            result = self.agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
        if result.get("__interrupt__"):
            action = result["__interrupt__"][0].value["action_requests"][0]
            return f"Shall I run {action['name']} with {action['args']}? (yes/no)"
        return result["messages"][-1].content

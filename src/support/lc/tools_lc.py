"""Stage 3 with LangChain: the same ToolBox exposed as LangChain tools.

Two ways to give tools to a model:
1. JSON schemas only (support.tools.TOOL_SCHEMAS) + our own executor  -> used by the LangGraph graph,
   because confirmation and identity are handled by our nodes.
2. Real LangChain Tool objects (below) -> needed by create_agent / ToolNode, which execute tools themselves.
"""
from __future__ import annotations

import json

from langchain_core.tools import StructuredTool
from pydantic import Field, create_model

from ..tools import TOOL_SCHEMAS, ToolBox


def make_lc_tools(toolbox: ToolBox) -> list[StructuredTool]:
    """Wrap every ToolBox method as a StructuredTool bound to this (per-conversation) ToolBox.

    The argument schema (a Pydantic model) is generated from TOOL_SCHEMAS, so both versions describe tools identically.
    Results are returned as JSON strings: that is what the model sees in the ToolMessage.
    """
    tools = []
    for schema in TOOL_SCHEMAS:
        fn = schema["function"]
        name = fn["name"]

        def run(_name=name, **kwargs) -> str:
            return json.dumps(toolbox.call(_name, kwargs), ensure_ascii=False)

        props = fn["parameters"]["properties"]
        args = create_model(f"{name}_args", **{p: (str, Field(description=d["description"])) for p, d in props.items()})
        tools.append(StructuredTool.from_function(func=run, name=name, description=fn["description"], args_schema=args))
    return tools

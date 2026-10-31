"""MCP server: gives Claude Desktop the same tools as the panel.   python -m support.panel.mcp_server

Claude Desktop starts this process itself (see claude_desktop.py) and talks to it over stdin/stdout, so nothing
here may print to stdout. Every tool call is recorded in the registry; the panel shows when Claude last used it.
"""
from __future__ import annotations

import functools
import inspect
from typing import get_type_hints

try:                                                   # mcp >= 2
    from mcp.server.mcpserver import MCPServer
except ImportError:                                    # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

from . import envfile, registry, service
from .guide import GUIDE


def _as_tool(fn):
    """Hide the internal 'origin' parameter, log the call, and turn errors into readable results."""
    hints = get_type_hints(fn)
    params = [p.replace(annotation=hints.get(name, p.annotation))
              for name, p in inspect.signature(fn).parameters.items() if name != "origin"]
    takes_origin = "origin" in inspect.signature(fn).parameters

    @functools.wraps(fn)
    def tool(**kwargs):
        registry.log_event("mcp", "tool_call", {"tool": fn.__name__, "args": kwargs})
        try:
            return fn(**kwargs, **({"origin": "mcp"} if takes_origin else {}))
        except Exception as e:                         # the model gets the reason instead of a stack trace
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    tool.__signature__ = inspect.Signature(params, return_annotation=hints.get("return", inspect.Signature.empty))
    tool.__annotations__ = {p.name: p.annotation for p in params}
    tool.__wrapped__ = None
    del tool.__wrapped__                               # stop inspect from following back to the original signature
    return tool


def build() -> MCPServer:
    server = MCPServer("support-agent", instructions=GUIDE)
    for fn in service.ALL_TOOLS:
        server.add_tool(_as_tool(fn), name=fn.__name__, description=inspect.getdoc(fn))
    return server


def main() -> None:
    envfile.load_into_environ()
    registry.log_event("mcp", "server_started", {})
    build().run("stdio")


if __name__ == "__main__":
    main()

# Starter: a least-privilege MCP server (notes in a sandbox folder) for Claude Desktop / Claude Code / any MCP client.
#   python run.py          self-test of the tools without MCP + prints the Claude Desktop config to paste
#   python run.py serve    runs the server over stdio (pip install "mcp>=1.2"; works with mcp 1.x FastMCP and 2.x)
# Security model (same as support.panel): only files inside notes/, no path tricks, .env never readable,
# writes need confirm=true, and nothing here can widen its own permissions.
import os, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
(HERE / "results").mkdir(exist_ok=True)
NOTES = HERE / "notes"
NOTES.mkdir(exist_ok=True)
MAX_CHARS = int(cfg.get("max_chars", 20000))


def _safe(name: str) -> Path:
    p = (NOTES / name).resolve()
    if NOTES.resolve() not in p.parents or p.name.startswith(".") or p.suffix not in (".md", ".txt"):
        raise ValueError("only .md/.txt files directly inside notes/ are allowed")
    return p


def list_notes() -> list[str]:
    """List the note files."""
    return sorted(p.name for p in NOTES.glob("*") if p.suffix in (".md", ".txt"))


def read_note(name: str) -> str:
    """Read one note."""
    return _safe(name).read_text(encoding="utf-8")[:MAX_CHARS]


def search_notes(query: str) -> list[dict]:
    """Case-insensitive search across notes; returns file and matching line."""
    q = query.lower()
    return [{"file": n, "line": line.strip()} for n in list_notes() for line in read_note(n).splitlines() if q in line.lower()][:50]


def write_note(name: str, text: str, confirm: bool = False) -> dict:
    """Create or overwrite a note. The client must ask the user and pass confirm=true."""
    if not confirm and cfg.get("write_tools_need_confirmation", True):
        return {"ok": False, "error": "ask the user first, then call again with confirm=true"}
    if len(text) > MAX_CHARS:
        return {"ok": False, "error": f"note longer than {MAX_CHARS} characters"}
    _safe(name).write_text(text, encoding="utf-8")
    return {"ok": True, "file": name}


TOOLS = [list_notes, read_note, search_notes, write_note]

if len(sys.argv) > 1 and sys.argv[1] == "serve":
    try:
        from mcp.server.mcpserver import MCPServer as Server            # mcp 2.x
    except ImportError:
        from mcp.server.fastmcp import FastMCP as Server                # mcp 1.x
    server = Server("notes")
    for fn in TOOLS:
        server.tool()(fn)

    @server.resource("notes://index")
    def index() -> str:
        """All note names, one per line."""
        return "\n".join(list_notes())

    server.run("stdio")
else:
    write_note("welcome.md", "# Welcome\nThis note was written by the self-test.\n", confirm=True)
    assert "welcome.md" in list_notes() and search_notes("self-test")
    assert write_note("x.md", "hi")["ok"] is False                       # no silent writes
    for bad in ["../config.yaml", ".env", "a/../../x.md", "evil.py"]:
        try:
            read_note(bad)
            raise SystemExit(f"security bug: {bad} was readable")
        except (ValueError, FileNotFoundError):
            pass
    print("selftest ok:", [f.__name__ for f in TOOLS])
    print("\nClaude Desktop -> Settings -> Developer -> Edit config, add under mcpServers:")
    print(json.dumps({"notes": {"command": sys.executable, "args": [str(HERE / "run.py"), "serve"],
                                "env": {"SUPPORT_ROOT": str(ROOT)}}}, indent=2))

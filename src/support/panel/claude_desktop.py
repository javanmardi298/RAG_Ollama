"""Register this project's MCP server in Claude Desktop's config, so Claude Desktop can use the project's tools.

Claude Desktop starts `python -m support.panel.mcp_server` itself (stdio). The entry uses this venv's Python
by absolute path, so it works without activating anything. The existing config is backed up before writing.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

from ..config import ROOT

SERVER_NAME = "support-agent"


def config_paths() -> list[Path]:
    """Where Claude Desktop reads its config. On Windows the Microsoft Store (MSIX) build uses a second location."""
    home = Path.home()
    if os.name == "nt":
        appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        paths = [appdata / "Claude" / "claude_desktop_config.json"]
        packages = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")) / "Packages"
        if packages.exists():
            for pkg in packages.glob("Claude_*"):
                paths.append(pkg / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json")
        return paths
    if sys.platform == "darwin":
        return [home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"]
    return [home / ".config" / "Claude" / "claude_desktop_config.json"]


def server_entry() -> dict:
    return {
        "command": sys.executable,
        "args": ["-m", "support.panel.mcp_server"],
        "env": {"SUPPORT_ROOT": str(ROOT), "PYTHONPATH": str(ROOT / "src"), "PYTHONUTF8": "1"},
    }


def _read(path: Path) -> dict:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def status() -> dict:
    paths = config_paths()
    found = []
    for p in paths:
        try:
            entry = _read(p).get("mcpServers", {}).get(SERVER_NAME)
        except (OSError, json.JSONDecodeError):
            entry = None
        if entry:
            found.append({"path": str(p), "python": entry.get("command"),
                          "current": entry.get("command") == sys.executable})
    from . import registry
    last = registry.last_event(source="mcp")
    detail = "نصب نشده" if not found else ("نصب شده" + ("" if all(f["current"] for f in found)
                                                       else " (با Python دیگری؛ دوباره نصب کن)"))
    if last:
        detail += f" — آخرین استفاده‌ی Claude Desktop: {time.strftime('%Y-%m-%d %H:%M', time.localtime(last['ts']))}"
    return {"installed": bool(found), "entries": found, "candidates": [str(p) for p in paths],
            "last_call": last["ts"] if last else None, "detail": detail, "entry": server_entry()}


def install(paths: list[Path] | None = None) -> dict:
    """Add or update our entry in every existing config location (and the standard one, created if missing)."""
    targets = paths or config_paths()
    targets = [p for p in targets if p.exists()] or targets[:1]
    written = []
    for path in targets:
        data = _read(path)
        if path.exists():
            shutil.copy2(path, path.with_suffix(f".backup-{time.strftime('%Y%m%d-%H%M%S')}.json"))
        data.setdefault("mcpServers", {})[SERVER_NAME] = server_entry()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(str(path))
    return {"written": written, "next": "Claude Desktop را کامل ببند (از system tray: Quit) و دوباره باز کن. "
                                        "در Settings → Developer باید «support-agent» با وضعیت running دیده شود."}


def uninstall(paths: list[Path] | None = None) -> dict:
    removed = []
    for path in paths or config_paths():
        data = _read(path) if path.exists() else {}
        if SERVER_NAME in data.get("mcpServers", {}):
            del data["mcpServers"][SERVER_NAME]
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            removed.append(str(path))
    return {"removed": removed}


if __name__ == "__main__":   # python -m support.panel.claude_desktop [install|uninstall|status]
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    print(json.dumps({"install": install, "uninstall": uninstall, "status": status}[action](), indent=2,
                     ensure_ascii=False))

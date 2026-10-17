"""The project's .env file (secrets such as ANTHROPIC_API_KEY). Never committed, never sent anywhere, never shown in full."""
from __future__ import annotations

import os
import re

from ..config import ROOT

ENV_PATH = ROOT / ".env"
ALLOWED = {"ANTHROPIC_API_KEY", "LANGSMITH_API_KEY", "LANGSMITH_TRACING", "OLLAMA_HOST", "WANDS_DIR", "HF_TOKEN"}
_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")


def read() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    out = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        m = _LINE.match(line)
        if m and not line.lstrip().startswith("#"):
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def load_into_environ() -> None:
    """Values already set in the environment win over .env."""
    for k, v in read().items():
        os.environ.setdefault(k, v)


def get(name: str) -> str | None:
    return os.environ.get(name) or read().get(name)


def set_value(name: str, value: str) -> None:
    if name not in ALLOWED:
        raise KeyError(f"{name} is not a supported .env key ({', '.join(sorted(ALLOWED))})")
    if any(c in value for c in "\r\n"):
        raise ValueError("value must be a single line")
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    lines = [l for l in lines if not (_LINE.match(l) and _LINE.match(l).group(1) == name)]
    if value:
        lines.append(f"{name}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if value:
        os.environ[name] = value
    else:
        os.environ.pop(name, None)


def mask(value: str | None) -> str:
    if not value:
        return ""
    return value[:7] + "…" + value[-4:] if len(value) > 14 else "…" * 3

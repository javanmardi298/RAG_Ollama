"""python lessons/00_setup/check_env.py : what works on this machine, and what to install for each provider. Never prints secrets."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ok = lambda b: "✓" if b else "✗"  # noqa: E731


def has(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def env_has(name: str) -> bool:
    if os.environ.get(name):
        return True
    f = ROOT / ".env"
    return f.exists() and any(line.startswith(name + "=") and line.split("=", 1)[1].strip() for line in f.read_text(encoding="utf-8").splitlines())


def ollama_up() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(os.environ.get("OLLAMA_HOST", "http://localhost:11434"), timeout=2)
        return True
    except Exception:
        return False


print(f"Python {sys.version.split()[0]}  {ok(sys.version_info >= (3, 10))} (need 3.10+)")
print(f"repo installed (import learn)       {ok(has('learn'))}   -> pip install -e .")
print(f"core packages (numpy sklearn yaml)  {ok(all(map(has, ['numpy', 'sklearn', 'yaml'])))}   -> pip install -r requirements.txt")
print()
print("Model providers (the offline one always works):")
print("  offline                            ✓  no setup; answers only show the shape of the pipeline")
print(f"  ollama   server running            {ok(ollama_up())}   -> install Ollama, `ollama pull qwen2.5:7b`")
print(f"           python package            {ok(has('ollama'))}   -> pip install ollama")
print(f"  anthropic  ANTHROPIC_API_KEY set   {ok(env_has('ANTHROPIC_API_KEY'))}   -> console.anthropic.com, key in .env")
print(f"             python package          {ok(has('anthropic'))}   -> pip install anthropic")
print(f"  opencode   on PATH                 {ok(bool(shutil.which('opencode')))}   -> https://opencode.ai (then log in to a provider)")
print(f"  openai_compatible  httpx           {ok(has('httpx'))}   -> pip install httpx; set LEARN_API_BASE")
print()
print("Optional parts:")
print(f"  torch (JEPA lessons)               {ok(has('torch'))}   -> pip install -r requirements-jepa.txt")
print(f"  panel (fastapi, uvicorn)           {ok(has('fastapi'))}   -> pip install -r requirements-panel.txt")
print(f"  .env is ignored by git             {ok('.env' in (ROOT / '.gitignore').read_text(encoding='utf-8'))}")

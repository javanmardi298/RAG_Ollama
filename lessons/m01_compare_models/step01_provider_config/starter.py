"""Step 1: resolve the model provider configuration from environment variables."""
from __future__ import annotations

PROVIDERS = {"offline", "ollama", "anthropic", "opencode", "openai_compatible"}
DEFAULT_MODEL = {"offline": "", "ollama": "qwen2.5:7b", "anthropic": "claude-sonnet-5-5", "opencode": "", "openai_compatible": ""}


def resolve_config(env: dict) -> dict:
    """-> {"provider", "model", "api_base", "budget_usd", "cloud"}; raises ValueError with a clear message for bad settings."""
    # TODO 1: provider from LEARN_PROVIDER (default "offline"), unknown -> ValueError
    # TODO 2: model from LEARN_MODEL or DEFAULT_MODEL
    # TODO 3: opencode needs "provider/model"; openai_compatible needs LEARN_API_BASE; anthropic needs ANTHROPIC_API_KEY in env
    # TODO 4: budget_usd = float(LEARN_BUDGET_USD or 0); not a number or negative -> ValueError
    # TODO 5: cloud = provider in {"anthropic", "openai_compatible"}
    raise NotImplementedError("TODO 1-5: resolve_config")

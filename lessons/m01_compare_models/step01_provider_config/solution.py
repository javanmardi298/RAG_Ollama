"""Step 1: resolve the model provider configuration from environment variables."""
from __future__ import annotations

PROVIDERS = {"offline", "ollama", "anthropic", "opencode", "openai_compatible"}
DEFAULT_MODEL = {"offline": "", "ollama": "qwen2.5:7b", "anthropic": "claude-sonnet-5-5", "opencode": "", "openai_compatible": ""}


def resolve_config(env: dict) -> dict:
    """-> {"provider", "model", "api_base", "budget_usd", "cloud"}; raises ValueError with a clear message for bad settings."""
    provider = env.get("LEARN_PROVIDER", "offline")
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}; choose one of {sorted(PROVIDERS)}")
    model = env.get("LEARN_MODEL") or DEFAULT_MODEL[provider]
    api_base = env.get("LEARN_API_BASE", "")
    if provider == "opencode" and "/" not in model:
        raise ValueError("opencode needs LEARN_MODEL=provider/model (see `opencode models`)")
    if provider == "openai_compatible" and not api_base:
        raise ValueError("openai_compatible needs LEARN_API_BASE, e.g. http://localhost:1234/v1")
    if provider == "anthropic" and not env.get("ANTHROPIC_API_KEY"):
        raise ValueError("anthropic needs ANTHROPIC_API_KEY (an API key from console.anthropic.com; a Claude.ai subscription is not one)")
    try:
        budget = float(env.get("LEARN_BUDGET_USD") or 0)
    except ValueError:
        raise ValueError("LEARN_BUDGET_USD must be a number") from None
    if budget < 0:
        raise ValueError("LEARN_BUDGET_USD must not be negative")
    return {"provider": provider, "model": model, "api_base": api_base, "budget_usd": budget,
            "cloud": provider in {"anthropic", "openai_compatible"}}

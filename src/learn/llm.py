"""The model a lesson talks to. Default: offline (no model, no key), so every lesson runs anywhere.

Choose with the environment (or lessons/learn.yaml): LEARN_PROVIDER = offline | ollama | anthropic | opencode | openai_compatible,
LEARN_MODEL = model name (opencode: provider/model), LEARN_API_BASE for openai_compatible.
"""
from __future__ import annotations

import os

from support import providers

DEFAULTS = {"offline": "", "ollama": "qwen2.5:7b", "anthropic": "claude-sonnet-5-5", "opencode": "", "openai_compatible": ""}


def get(provider: str | None = None, model: str | None = None):
    provider = provider or os.environ.get("LEARN_PROVIDER", "offline")
    model = model if model is not None else os.environ.get("LEARN_MODEL", DEFAULTS.get(provider, ""))
    return providers.make(provider, model, 0.0, api_base=os.environ.get("LEARN_API_BASE", ""),
                          budget=providers.Budget(float(os.environ.get("LEARN_BUDGET_USD", "0")),
                                                  float(os.environ.get("LEARN_PRICE_IN", "0")),
                                                  float(os.environ.get("LEARN_PRICE_OUT", "0"))))

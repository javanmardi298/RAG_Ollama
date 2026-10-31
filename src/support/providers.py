"""LLM providers behind the same interface as OllamaLLM (.chat(messages, tools, json_schema) and .json(messages, schema)).

    ollama             local model (support.llm.OllamaLLM)
    anthropic          Claude through the API (ANTHROPIC_API_KEY in .env). A Claude.ai subscription login is NOT an API key and
                       cannot be used by your own code (Anthropic's terms), so this needs a Console API key.
    opencode           any model configured in OpenCode, through `opencode run -m provider/model` (text only, no tool calls)
    openai_compatible  LM Studio, vLLM, OpenRouter, ...: POST {api_base}/chat/completions (key in OPENAI_API_KEY if needed)
    offline            deterministic stand-in with no model at all: lessons and CI run without any setup

Cloud providers keep a running cost estimate (tokens x the prices in settings) and stop at cloud_budget_usd.
Limits: tool calling is implemented for ollama only; the other providers answer text and JSON.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time

from .llm import LLMReply


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    """Estimated spend of one process. usd_limit 0 = unlimited. Prices are per million tokens, copied by you from the pricing page."""

    def __init__(self, usd_limit: float = 0.0, price_in: float = 0.0, price_out: float = 0.0):
        self.limit, self.price_in, self.price_out = usd_limit, price_in, price_out
        self.tokens_in = self.tokens_out = self.calls = 0

    @property
    def spent(self) -> float:
        return (self.tokens_in * self.price_in + self.tokens_out * self.price_out) / 1e6

    def check(self) -> None:
        if self.limit and self.spent >= self.limit:
            raise BudgetExceeded(f"estimated spend ${self.spent:.4f} reached the limit ${self.limit} (llm.cloud_budget_usd)")

    def add(self, tin: int, tout: int) -> None:
        self.tokens_in += tin
        self.tokens_out += tout
        self.calls += 1


def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    return system, [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]


def _json_from_text(text: str) -> dict:
    """Models sometimes wrap JSON in prose or a code fence: take the outermost {...}."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON object in the model answer: {text[:200]!r}")
    return json.loads(m.group(0))


class _Base:
    def json(self, messages: list[dict], schema: dict) -> dict:
        hint = {"role": "user", "content": "Answer with one JSON object only, matching this JSON schema:\n" + json.dumps(schema)}
        return _json_from_text(self.chat(list(messages) + [hint], json_schema=schema).content)


class AnthropicLLM(_Base):
    def __init__(self, model: str, temperature: float = 0.0, api_key: str | None = None, budget: Budget | None = None,
                 max_tokens: int = 1024, timeout_s: float = 180):
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError("pip install anthropic (requirements-panel.txt)") from e
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set (put it in .env or the environment; see lessons/00_setup)")
        self.client = anthropic.Anthropic(api_key=key, timeout=timeout_s)
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens
        self.budget = budget or Budget()

    def chat(self, messages, tools=None, json_schema=None) -> LLMReply:
        if tools:
            raise NotImplementedError("tool calling is implemented for the ollama provider only")
        self.budget.check()
        system, msgs = _split_system(messages)
        kw = {"system": system} if system else {}
        start = time.perf_counter()
        try:
            r = self.client.messages.create(model=self.model, max_tokens=self.max_tokens, messages=msgs,
                                            temperature=self.temperature, **kw)
        except Exception as e:                  # some current models reject sampling parameters: retry once without it
            if "temperature" not in str(e).lower():
                raise
            r = self.client.messages.create(model=self.model, max_tokens=self.max_tokens, messages=msgs, **kw)
        self.budget.add(r.usage.input_tokens, r.usage.output_tokens)
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return LLMReply(text, [], time.perf_counter() - start)


class OpenAICompatibleLLM(_Base):
    def __init__(self, model: str, api_base: str, temperature: float = 0.0, api_key: str | None = None,
                 budget: Budget | None = None, timeout_s: float = 180):
        import httpx
        if not api_base:
            raise RuntimeError("llm.api_base is empty (e.g. http://localhost:1234/v1 for LM Studio)")
        self.http = httpx.Client(base_url=api_base.rstrip("/"), timeout=timeout_s)
        self.model, self.temperature = model, temperature
        self.key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.budget = budget or Budget()

    def chat(self, messages, tools=None, json_schema=None) -> LLMReply:
        if tools:
            raise NotImplementedError("tool calling is implemented for the ollama provider only")
        self.budget.check()
        start = time.perf_counter()
        r = self.http.post("/chat/completions", headers={"Authorization": f"Bearer {self.key}"} if self.key else {},
                           json={"model": self.model, "temperature": self.temperature,
                                 "messages": [{"role": m["role"], "content": m["content"]} for m in messages]})
        r.raise_for_status()
        data = r.json()
        u = data.get("usage") or {}
        self.budget.add(u.get("prompt_tokens", 0), u.get("completion_tokens", 0))
        return LLMReply(data["choices"][0]["message"]["content"] or "", [], time.perf_counter() - start)


class OpenCodeLLM(_Base):
    """Runs `opencode run --model provider/model "<prompt>"` and returns what it prints.

    OpenCode (https://opencode.ai) keeps its own provider logins, so any model you can use there works here.
    Each call is a fresh one-shot run (the conversation is flattened into the prompt). Slow but needs no key in this project."""

    def __init__(self, model: str, timeout_s: float = 300, binary: str = "opencode", attach: str | None = None):
        if not shutil.which(binary):
            raise RuntimeError("opencode is not on PATH: install it from https://opencode.ai and log in to a provider first")
        self.binary, self.model, self.timeout_s, self.attach = binary, model, timeout_s, attach

    def chat(self, messages, tools=None, json_schema=None) -> LLMReply:
        if tools:
            raise NotImplementedError("tool calling is implemented for the ollama provider only")
        prompt = "\n\n".join(f"[{m['role']}] {m['content']}" for m in messages)
        cmd = [self.binary, "run", *(["-m", self.model] if self.model else []), *(["--attach", self.attach] if self.attach else []), prompt]
        start = time.perf_counter()
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_s, encoding="utf-8")
        if out.returncode:
            raise RuntimeError(f"opencode failed ({out.returncode}): {out.stderr[-500:]}")
        return LLMReply(out.stdout.strip(), [], time.perf_counter() - start)


class OfflineLLM(_Base):
    """No model: echoes the question in a fixed format, and fills JSON schemas with neutral values.
    Lets every lesson, test and CI job run anywhere; swap in a real provider to see real answers."""

    def chat(self, messages, tools=None, json_schema=None) -> LLMReply:
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return LLMReply("(offline model) " + last[:200])

    def json(self, messages, schema) -> dict:
        def fill(s):
            t = s.get("type")
            if "enum" in s:
                return "retrieve" if "retrieve" in s["enum"] else s["enum"][0]
            return {"boolean": True, "string": "", "number": 0, "integer": 0, "array": [],
                    "object": {k: fill(v) for k, v in s.get("properties", {}).items()}}.get(t, None)
        return fill(schema)


def make(provider: str, model: str, temperature: float = 0.0, host: str | None = None, api_base: str = "",
         timeout_s: float = 180, max_retries: int = 2, budget: Budget | None = None):
    if provider == "offline":
        return OfflineLLM()
    if provider == "ollama":
        from .llm import OllamaLLM
        return OllamaLLM(model, temperature=temperature, host=host, timeout_s=timeout_s, max_retries=max_retries)
    if provider == "anthropic":
        return AnthropicLLM(model, temperature, budget=budget, timeout_s=timeout_s)
    if provider == "opencode":
        return OpenCodeLLM(model, timeout_s=max(timeout_s, 300))
    if provider == "openai_compatible":
        return OpenAICompatibleLLM(model, api_base, temperature, budget=budget, timeout_s=timeout_s)
    raise ValueError(f"unknown provider {provider!r}")

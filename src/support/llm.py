"""One small interface for every LLM call in the project.

Real runs use OllamaLLM. Tests use ScriptedLLM, which replays prepared answers, so the
agent logic can be tested without a model, a GPU, or randomness.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class LLMReply:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    latency_s: float = 0.0


class OllamaLLM:
    def __init__(self, model: str = "qwen2.5:7b", temperature: float = 0.0, host: str | None = None):
        import ollama  # imported here so tests do not need the package

        self.client = ollama.Client(host=host) if host else ollama.Client()
        self.model = model
        self.temperature = temperature

    def chat(self, messages: list[dict], tools: list[dict] | None = None,
             json_schema: dict | None = None) -> LLMReply:
        start = time.perf_counter()
        resp = self.client.chat(
            model=self.model, messages=messages, tools=tools,
            format=json_schema, options={"temperature": self.temperature},
        )
        calls = [ToolCall(c.function.name, dict(c.function.arguments))
                 for c in (resp.message.tool_calls or [])]
        return LLMReply(resp.message.content or "", calls, time.perf_counter() - start)

    def json(self, messages: list[dict], schema: dict) -> dict:
        """Structured output: Ollama constrains decoding to the JSON schema."""
        return json.loads(self.chat(messages, json_schema=schema).content)


class ScriptedLLM:
    """Returns prepared replies in order and records what it was asked."""

    def __init__(self, replies: list[LLMReply | dict | str]):
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    def chat(self, messages, tools=None, json_schema=None) -> LLMReply:
        self.calls.append([dict(m) for m in messages])
        reply = self.replies.pop(0)
        if isinstance(reply, str):
            return LLMReply(content=reply)
        if isinstance(reply, dict):
            return LLMReply(content=json.dumps(reply))
        return reply

    def json(self, messages, schema) -> dict:
        return json.loads(self.chat(messages, json_schema=schema).content)

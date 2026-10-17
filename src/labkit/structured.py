"""Structured output that code can trust: parse, validate against a pydantic model, repair once, else fail loudly.

Constrained decoding (Ollama `format=`, Claude structured outputs) makes valid JSON likely, not business-valid
data: a total that does not match the line items is still a bug. Put those rules in the model's validators.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)


@dataclass
class Parsed(Generic[T]):
    value: T | None
    attempts: int
    errors: list[str]

    @property
    def ok(self) -> bool:
        return self.value is not None


def parse_json(text: str):
    """Tolerate code fences and text around the JSON object, nothing more creative than that."""
    text = _FENCE.sub("", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])


def _errors(e: Exception) -> list[str]:
    if isinstance(e, ValidationError):
        return [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
    return [str(e)]


def extract(llm, model: type[T], prompt: str, max_repairs: int = 1) -> Parsed[T]:
    """llm: object with .json(messages, schema) -> dict (support.llm interface) or .chat(messages) -> reply.content."""
    schema = model.model_json_schema()
    messages = [{"role": "user", "content": prompt}]
    errors: list[str] = []
    for attempt in range(1, max_repairs + 2):
        raw_text = ""
        try:
            if hasattr(llm, "json"):
                raw = llm.json(messages, schema)
                raw_text = json.dumps(raw, ensure_ascii=False)
            else:
                raw_text = llm.chat(messages).content
                raw = parse_json(raw_text)
            return Parsed(model.model_validate(raw), attempt, errors)
        except (ValueError, ValidationError) as e:    # JSONDecodeError is a ValueError
            errs = _errors(e)
            errors += errs
            messages = messages + [{"role": "assistant", "content": raw_text},
                                   {"role": "user", "content": "The JSON was invalid: " + "; ".join(errs) +
                                    ". Return the corrected JSON only."}]
    return Parsed(None, max_repairs + 1, errors)

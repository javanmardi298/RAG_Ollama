"""Direct chat with Claude from the panel (Anthropic API key in .env), with the same tools as the MCP server.

A manual tool-use loop: Claude answers or asks for a tool, the panel runs the tool from service.py and sends the
result back, until Claude gives a final answer or the round limit is reached. The full response content (including
thinking blocks) is appended to the history unchanged, as the API requires.
"""
from __future__ import annotations

import json
import threading
import time

from ..settings import load
from . import envfile, registry, service
from .guide import GUIDE


class ClaudeUnavailable(Exception):
    pass


def _client():
    try:
        import anthropic
    except ImportError as e:
        raise ClaudeUnavailable("پکیج anthropic نصب نیست: pip install -r requirements-panel.txt") from e
    key = envfile.get("ANTHROPIC_API_KEY")
    if not key:
        raise ClaudeUnavailable("کلید ANTHROPIC_API_KEY تنظیم نشده (صفحه‌ی اتصال‌ها).")
    return anthropic, anthropic.Anthropic(api_key=key)


def _tools(cfg) -> list[dict]:
    allowed = list(service.READ_TOOLS) + [service.chat_with_agent, service.make_colab_bundle]
    if cfg.allow_runs:
        allowed += [service.run_task, service.stop_run]
    if cfg.allow_settings_changes:
        allowed.append(service.update_settings)
    return [service.tool_schema(f) for f in allowed]


def _preview(result, limit: int = 600) -> str:
    text = json.dumps(result, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + " …"


class ClaudeChat:
    def __init__(self):
        self.history: dict[str, list] = {}
        self._lock = threading.Lock()

    def reset(self, chat_id: str) -> None:
        self.history.pop(chat_id, None)

    def send(self, chat_id: str, text: str, context: str = "") -> dict:
        anthropic, client = _client()
        cfg = load().claude
        tools = _tools(cfg)
        with self._lock:
            messages = self.history.setdefault(chat_id, [])
            content = text if not context else f"{text}\n\n[panel context: {context}]"
            messages.append({"role": "user", "content": content})
            calls, usage = [], {"input_tokens": 0, "output_tokens": 0}
            for _ in range(cfg.max_tool_rounds):
                kwargs = dict(model=cfg.model, max_tokens=cfg.max_tokens, system=GUIDE, tools=tools, messages=messages,
                              thinking={"type": "adaptive"}, output_config={"effort": cfg.effort})
                try:
                    if cfg.refusal_fallback:
                        try:
                            resp = client.beta.messages.create(**kwargs, betas=["server-side-fallback-2026-07-01"],
                                                               fallbacks="default")
                        except TypeError:   # an older anthropic package without the fallbacks parameter
                            resp = client.messages.create(**kwargs)
                    else:
                        resp = client.messages.create(**kwargs)
                except anthropic.AuthenticationError:
                    messages.pop()
                    raise ClaudeUnavailable("کلید API نامعتبر است.")
                except anthropic.RateLimitError:
                    messages.pop()
                    raise ClaudeUnavailable("محدودیت نرخ API؛ کمی بعد دوباره امتحان کن.")
                except anthropic.APIConnectionError:
                    messages.pop()
                    raise ClaudeUnavailable("اتصال به API برقرار نشد (اینترنت؟).")
                except anthropic.APIStatusError as e:
                    messages.pop()
                    raise ClaudeUnavailable(f"خطای API ({e.status_code}): {e.message}")
                usage["input_tokens"] += resp.usage.input_tokens
                usage["output_tokens"] += resp.usage.output_tokens
                messages.append({"role": "assistant", "content": resp.content})

                if resp.stop_reason == "refusal":
                    return self._final(resp, calls, usage, note="Claude این درخواست را رد کرد.")
                if resp.stop_reason != "tool_use":
                    note = "پاسخ به سقف max_tokens رسید و ناقص است." if resp.stop_reason == "max_tokens" else ""
                    return self._final(resp, calls, usage, note=note)

                results = []
                for block in (b for b in resp.content if b.type == "tool_use"):
                    started = time.time()
                    try:
                        out, is_error = service.call_tool(block.name, dict(block.input), origin="claude"), False
                    except Exception as e:
                        out, is_error = {"error": f"{type(e).__name__}: {e}"}, True
                    registry.log_event("claude", "tool_call", {"tool": block.name, "args": dict(block.input)})
                    calls.append({"tool": block.name, "input": dict(block.input), "result": _preview(out),
                                  "error": is_error, "ms": round((time.time() - started) * 1000)})
                    results.append({"type": "tool_result", "tool_use_id": block.id, "is_error": is_error,
                                    "content": json.dumps(out, ensure_ascii=False, default=str)[:60_000]})
                messages.append({"role": "user", "content": results})
            return {"reply": "به سقف دفعات استفاده از ابزار در یک پاسخ رسیدم (claude.max_tool_rounds). "
                             "بگو ادامه بدهم.", "tool_calls": calls, "usage": usage}

    @staticmethod
    def _final(resp, calls, usage, note=""):
        text = "\n".join(b.text for b in resp.content if b.type == "text").strip()
        return {"reply": (text + ("\n\n" + note if note else "")).strip(), "tool_calls": calls, "usage": usage,
                "model": resp.model}


CHAT = ClaudeChat()


def status() -> dict:
    cfg = load().claude
    key = envfile.get("ANTHROPIC_API_KEY")
    try:
        import anthropic  # noqa: F401
        pkg = True
    except ImportError:
        pkg = False
    return {"ready": bool(key) and pkg, "key": envfile.mask(key), "package": pkg, "model": cfg.model,
            "effort": cfg.effort, "allow_runs": cfg.allow_runs, "allow_settings_changes": cfg.allow_settings_changes}

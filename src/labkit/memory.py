"""Conversation memory for long chats: recent turns verbatim, older turns as a running summary, plus pinned facts.

The context window is not memory: sending the whole history gets slow, expensive and, past a point, worse
(the model loses the middle). Keep what must be exact (order id, verified email, decisions) as structured facts,
the last few turns verbatim, and the rest summarised.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Memory:
    keep_turns: int = 6                                   # recent messages kept verbatim
    summarize: Callable[[str, list[dict]], str] | None = None   # (old summary, dropped messages) -> new summary
    summary: str = ""
    facts: dict = field(default_factory=dict)             # exact values: never summarised away
    messages: list[dict] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.keep_turns:
            dropped, self.messages = self.messages[:-self.keep_turns], self.messages[-self.keep_turns:]
            if self.summarize:
                self.summary = self.summarize(self.summary, dropped)
            else:   # no LLM: keep a crude trace so nothing silently disappears
                self.summary = (self.summary + " " + " | ".join(f"{m['role']}: {m['content'][:60]}" for m in dropped)).strip()

    def remember(self, key: str, value) -> None:
        self.facts[key] = value

    def context(self, system: str) -> list[dict]:
        """Messages to send: system + facts + summary + recent turns."""
        extra = []
        if self.facts:
            extra.append("Known facts (exact): " + "; ".join(f"{k}={v}" for k, v in self.facts.items()))
        if self.summary:
            extra.append("Earlier in this conversation: " + self.summary)
        sys = system + ("\n\n" + "\n".join(extra) if extra else "")
        return [{"role": "system", "content": sys}] + self.messages


def llm_summarizer(llm, max_words: int = 120) -> Callable[[str, list[dict]], str]:
    def summarize(old: str, dropped: list[dict]) -> str:
        turns = "\n".join(f"{m['role']}: {m['content']}" for m in dropped)
        prompt = (f"Update the running summary of a support conversation in at most {max_words} words. Keep requests, "
                  f"decisions and open questions; drop greetings.\nCurrent summary: {old or '(none)'}\nNew turns:\n{turns}")
        return llm.chat([{"role": "user", "content": prompt}]).content.strip()
    return summarize

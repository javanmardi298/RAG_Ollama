"""Step 1: route a question: direct | retrieve | multi_hop."""
from __future__ import annotations

import re

GREETINGS = {"hello", "hi", "hey", "thanks", "thank you", "bye"}
QWORDS = {"how", "what", "when", "where", "why", "which", "who", "can", "do", "does", "is", "are"}


def route(question: str) -> str:
    q = question.strip().lower().rstrip("!.? ").strip()
    if q in GREETINGS or re.fullmatch(r"[\d\s+\-*/().]+", q):
        return "direct"
    words = re.findall(r"[a-z]+", q)
    if " and " in f" {q} " and sum(w in QWORDS for w in words) >= 2:
        return "multi_hop"
    return "retrieve"

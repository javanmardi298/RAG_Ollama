"""Step 1: route a question: direct | retrieve | multi_hop."""
from __future__ import annotations

import re

GREETINGS = {"hello", "hi", "hey", "thanks", "thank you", "bye"}
QWORDS = {"how", "what", "when", "where", "why", "which", "who", "can", "do", "does", "is", "are"}


def route(question: str) -> str:
    # TODO 1: normalise (lowercase, strip spaces and trailing "!.?")
    # TODO 2: greeting -> "direct"; pure arithmetic (digits, spaces, + - * / ( ) .) -> "direct"
    # TODO 3: contains " and " and at least two question words -> "multi_hop"; otherwise "retrieve"
    raise NotImplementedError("TODO 1-3: route")

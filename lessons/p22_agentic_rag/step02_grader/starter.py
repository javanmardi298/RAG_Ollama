"""Step 2: grade retrieved chunks: relevant or not."""
from __future__ import annotations

import re

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "and", "or", "in", "on", "for", "can", "how",
        "what", "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that", "when", "where", "there", "much", "many", "get", "have", "long"}
SYN = {"send back": "return", "money back": "refund", "broken": "damage defect", "couch": "sofa"}


def expand(text: str) -> str:
    text = text.lower()
    for a, b in SYN.items():
        text = text.replace(a, b)
    return text


def content_words(text: str) -> set[str]:
    # TODO 1: lowercase, words/numbers only, drop STOP and one-letter words, strip one trailing "s" from words longer than 3 letters
    raise NotImplementedError("TODO 1: content_words")


def grade(question: str, chunk: dict, min_ratio: float = 0.5) -> bool:
    # TODO 2: q = content_words(expand(question)); c = content_words(chunk heading + " " + chunk text)
    #         relevant when at least min_ratio of the question's content words are in the chunk: len(q & c) / len(q) >= min_ratio
    #         an empty question is never relevant
    raise NotImplementedError("TODO 2: grade")


if __name__ == "__main__":
    from learn.data import faq_chunks, faq_questions
    chunks = faq_chunks()
    for q in faq_questions():
        kept = [c["id"] for c in chunks if grade(q["question"], c)]
        print(f"{q['question'][:42]:42s} expected={q['relevant'] or '(none)':9s} kept={kept}")

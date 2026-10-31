"""Step 3: rewrite the query and retry, within a round budget."""
from __future__ import annotations

import re

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "and", "or", "in", "on", "for", "can", "how",
        "what", "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that", "when", "where", "there", "much", "many",
        "get", "have", "long"}
SYN = {"send back": "return", "money back": "refund", "broken": "damage defect", "couch": "sofa"}


def expand(text: str) -> str:
    text = text.lower()
    for a, b in SYN.items():
        text = text.replace(a, b)
    return text


def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def rewrite(question: str, tried: list[str]) -> list[str]:
    # TODO 1: candidates in this order: expand(question); the content words joined by spaces; each content word alone.
    #         Return only candidates that are not in `tried` (and not duplicates of each other).
    raise NotImplementedError("TODO 1: rewrite")


def agentic_search(question: str, search, grade, rewrite, max_rounds: int = 3, min_relevant: int = 1) -> dict:
    """search(query) -> list of chunk dicts with "id"; grade(question, chunk) -> bool; rewrite(question, tried) -> [queries]."""
    # TODO 2: queries = [question]; tried = []; relevant = {} (by chunk id); rounds = 0
    # TODO 3: while queries and rounds < max_rounds: rounds += 1; for each query: tried.append(query), search it, keep the
    #         chunks that grade(question, chunk) accepts; stop when len(relevant) >= min_relevant; else queries = rewrite(question, tried)
    # TODO 4: return {"chunks": list(relevant.values()), "rounds": rounds, "queries": tried}
    raise NotImplementedError("TODO 2-4: the corrective loop")


if __name__ == "__main__":
    from learn.data import faq_chunks, faq_questions, retrieve, rule_grade
    chunks = faq_chunks()
    for q in faq_questions():
        out = agentic_search(q["question"], lambda s: retrieve(s, chunks, k=3), rule_grade, rewrite)
        print(f"{q['question'][:42]:42s} rounds={out['rounds']} found={[c['id'] for c in out['chunks']]}")

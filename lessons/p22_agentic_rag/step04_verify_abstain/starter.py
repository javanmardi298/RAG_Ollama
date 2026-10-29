"""Step 4: the full agentic loop with verification and abstention (route, grade, search helpers are given)."""
from __future__ import annotations

import re

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "and", "or", "in", "on", "for", "can", "how",
        "what", "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that", "when", "where", "there", "much", "many",
        "get", "have", "long", "within", "will"}


def cw(text: str) -> set[str]:
    """content words with a simple plural strip"""
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1}


def route(question: str) -> str:                                     # step 1 (given)
    q = question.strip().lower().rstrip("!.? ").strip()
    return "direct" if q in {"hello", "hi", "hey", "thanks", "thank you", "bye"} else "retrieve"


def agentic_search(question, search, grade, rewrite, max_rounds=3, min_relevant=1) -> dict:   # step 3 (given)
    queries, tried, relevant, rounds = [question], [], {}, 0
    while queries and rounds < max_rounds:
        rounds += 1
        for q in queries:
            tried.append(q)
            for c in search(q):
                if grade(question, c):
                    relevant.setdefault(c["id"], c)
        if len(relevant) >= min_relevant:
            break
        queries = [x for x in rewrite(question, tried) if x not in tried]
    return {"chunks": list(relevant.values()), "rounds": rounds, "queries": tried}


def verify(answer: str, chunks: list[dict]) -> bool:
    # TODO 1: every content word of the answer (cw) must occur in the content words of all chunk texts together;
    #         an empty answer is never verified. Citation brackets like [returns#0] must NOT count as answer words.
    raise NotImplementedError("TODO 1: verify")


def run_agent(question: str, search, grade, rewrite, answer_fn, direct_fn=lambda q: "Hello! How can I help?") -> dict:
    # TODO 2: direct route -> {"answer": direct_fn(question), "citations": [], "route": "direct", "rounds": 0, "abstained": False}
    # TODO 3: found = agentic_search(...); no chunks -> abstain (answer None)
    # TODO 4: text, cites = answer_fn(question, chunks); keep only cites that are ids of the chunks; no cite left or
    #         not verify(text, chunks) -> abstain; otherwise return the answer. Always include route and rounds.
    raise NotImplementedError("TODO 2-4: run_agent")


def report(outcomes: list[dict], questions: list[dict]) -> dict:
    # TODO 5: count the five categories described in the lesson
    raise NotImplementedError("TODO 5: report")


if __name__ == "__main__":
    from learn.data import faq_chunks, faq_questions, retrieve, rule_grade
    chunks = faq_chunks()

    def rewrite(q, tried):
        return [x for x in [" ".join(sorted(cw(q)))] if x not in tried]

    def answer_fn(q, cs):                         # extractive: the best sentence of the best chunk, cited
        best = max(cs, key=lambda c: len(cw(q) & cw(c["text"])))
        return f"{best['text']} [{best['id']}]", [best["id"]]

    qs = faq_questions()
    outs = [run_agent(q["question"], lambda s: retrieve(s, chunks, k=3), rule_grade, rewrite, answer_fn) for q in qs]
    for q, o in zip(qs, outs):
        print(f"{q['question'][:42]:42s} {'ABSTAIN' if o['abstained'] else o['answer'][:50]}")
    print(report(outs, qs))

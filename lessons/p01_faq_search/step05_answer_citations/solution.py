"""Step 5: grounded answer with citations and abstention."""
from __future__ import annotations

import re

SYSTEM = ("You answer customer questions using ONLY the sources provided. After every claim write the id of its source "
          "in square brackets, like [returns#0]. If the sources do not contain the answer, say you do not know.")


def build_messages(question: str, chunks: list[dict]) -> list[dict]:
    sources = "\n".join(f"[{c['id']}] {c['heading']}: {c['text']}" for c in chunks)
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Sources:\n{sources}\n\nQuestion: {question}"}]


def extract_citations(text: str, allowed_ids: set[str]) -> list[str]:
    seen: list[str] = []
    for cid in re.findall(r"\[([^\]]+)\]", text):
        if cid in allowed_ids and cid not in seen:
            seen.append(cid)
    return seen


def answer(question: str, chunks: list[dict], llm) -> dict:
    if not chunks:
        return {"answer": None, "citations": [], "abstained": True}
    text = llm.chat(build_messages(question, chunks)).content
    cites = extract_citations(text, {c["id"] for c in chunks})
    if not cites:
        return {"answer": None, "citations": [], "abstained": True}
    return {"answer": text, "citations": cites, "abstained": False}


if __name__ == "__main__":
    from learn import llm as learn_llm
    from learn.data import faq_chunks, faq_questions, retrieve

    chunks, model = faq_chunks(), learn_llm.get()          # offline by default; see LEARN_PROVIDER in lessons/00_setup
    for q in faq_questions():
        out = answer(q["question"], retrieve(q["question"], chunks), model)
        print(f"{q['question'][:45]:45s} -> {'ABSTAINED' if out['abstained'] else out['answer'][:70]!r:70s} {out['citations']}")

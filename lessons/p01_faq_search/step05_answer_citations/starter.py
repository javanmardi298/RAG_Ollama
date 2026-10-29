"""Step 5: grounded answer with citations and abstention."""
from __future__ import annotations

import re

SYSTEM = ("You answer customer questions using ONLY the sources provided. After every claim write the id of its source "
          "in square brackets, like [returns#0]. If the sources do not contain the answer, say you do not know.")


def build_messages(question: str, chunks: list[dict]) -> list[dict]:
    # TODO 1: [{"role": "system", "content": SYSTEM}, {"role": "user", "content": ...}] where the user text lists every
    #         chunk as "[id] heading: text" (one per line) followed by "Question: ..."
    raise NotImplementedError("TODO 1: build the prompt")


def extract_citations(text: str, allowed_ids: set[str]) -> list[str]:
    # TODO 2: every [...] in the text, keep only ids in allowed_ids, no duplicates, in order of appearance
    raise NotImplementedError("TODO 2: extract valid citations")


def answer(question: str, chunks: list[dict], llm) -> dict:
    # TODO 3: no chunks -> abstain WITHOUT calling the model; otherwise call llm.chat(messages).content, extract the
    #         valid citations; no valid citation -> abstain. Return {"answer": str | None, "citations": [...], "abstained": bool}
    raise NotImplementedError("TODO 3: answer or abstain")


if __name__ == "__main__":
    from learn import llm as learn_llm
    from learn.data import faq_chunks, faq_questions, retrieve

    chunks, model = faq_chunks(), learn_llm.get()          # offline by default; see LEARN_PROVIDER in lessons/00_setup
    for q in faq_questions():
        out = answer(q["question"], retrieve(q["question"], chunks), model)
        print(f"{q['question'][:45]:45s} -> {'ABSTAINED' if out['abstained'] else out['answer'][:70]!r:70s} {out['citations']}")

"""Step 5: model-backed components (labkit.agentic_rag) behind one llm interface."""
from __future__ import annotations

import re

from labkit.agentic_rag import AgenticRAG, llm_grader, llm_rewriter, llm_router, llm_verifier
from labkit.chunking import Chunk

SYSTEM = ("Answer ONLY from the sources. After every claim write its source id in square brackets, like [returns#0]. "
          "If the sources do not contain the answer, say you do not know.")


def to_chunks(dicts: list[dict]) -> list[Chunk]:
    return [Chunk(chunk_id=d["id"], doc_id=d["doc_id"], text=d["text"], meta={"heading": d["heading"]}) for d in dicts]


def make_answer(llm):
    """returns answer(question, chunks) -> (text, cited chunk ids)"""
    def answer(question: str, chunks: list[Chunk]):
        sources = "\n".join(f"[{c.chunk_id}] {c.text}" for c in chunks)
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Sources:\n{sources}\n\nQuestion: {question}"}]
        text = llm.chat(messages).content
        allowed = {c.chunk_id for c in chunks}
        cites: list[str] = []
        for cid in re.findall(r"\[([^\]]+)\]", text):
            if cid in allowed and cid not in cites:
                cites.append(cid)
        return text, cites
    return answer


def make_agent(search, llm, max_rounds: int = 3) -> AgenticRAG:
    return AgenticRAG(search=search, answer=make_answer(llm), grade=llm_grader(llm), rewrite=llm_rewriter(llm),
                      verify=llm_verifier(llm), route=llm_router(llm),
                      direct=lambda q: llm.chat([{"role": "user", "content": q}]).content, max_rounds=max_rounds)


if __name__ == "__main__":
    import time

    from learn import llm as learn_llm
    from learn.data import faq_chunks, faq_questions, retrieve

    dicts = faq_chunks()
    chunks = to_chunks(dicts)
    by_id = {c.chunk_id: c for c in chunks}
    model = learn_llm.get()
    agent = make_agent(lambda q: [by_id[d["id"]] for d in retrieve(q, dicts, k=3)], model)
    counts = {"answered_correctly": 0, "abstained_wrongly": 0, "abstained_correctly": 0, "answered_unanswerable": 0}
    start = time.perf_counter()
    for q in faq_questions():
        out = agent.run(q["question"])
        if q["answerable"] == "yes":
            counts["abstained_wrongly" if out.abstained else "answered_correctly"] += 1
        else:
            counts["abstained_correctly" if out.abstained else "answered_unanswerable"] += 1
        print(f"{q['question'][:42]:42s} route={out.route:9s} rounds={out.rounds} {'ABSTAIN' if out.abstained else out.answer[:40]!r}")
    print("llm agent:", counts, f"{time.perf_counter() - start:.1f}s")
    print("Compare with the rule-based agent of step 4. Which errors changed?")

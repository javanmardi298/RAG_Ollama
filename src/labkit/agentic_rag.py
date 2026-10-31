"""Agentic RAG: retrieval as a loop the system controls, not a single lookup.

The patterns that became established (Self-RAG, Corrective RAG / CRAG, Adaptive-RAG, iterative multi-hop):
1. ROUTE      does this question need retrieval at all, one search, or several hops?
2. RETRIEVE   search with the current query
3. GRADE      is each retrieved chunk relevant? (cheap LLM judge, or a score threshold)
4. CORRECT    nothing relevant -> rewrite / decompose the query and search again (bounded)
5. ANSWER     from the relevant chunks only, with citations
6. VERIFY     is every claim supported? if not: one more round, else abstain ("I don't know")

Every decision is a pluggable function, so the loop is testable without a model and each step can be
evaluated on its own. Budgets (max_rounds) keep cost and latency bounded: an unbounded loop is a bug.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .chunking import Chunk


@dataclass
class Step:
    kind: str                 # route | retrieve | grade | rewrite | answer | verify | abstain
    detail: dict = field(default_factory=dict)


@dataclass
class AgenticAnswer:
    answer: str | None        # None = abstained
    citations: list[str]
    route: str
    rounds: int
    trace: list[Step]

    @property
    def abstained(self) -> bool:
        return self.answer is None


@dataclass
class AgenticRAG:
    search: Callable[[str], list[Chunk]]                          # query -> chunks
    answer: Callable[[str, list[Chunk]], tuple[str, list[str]]]   # (question, chunks) -> (answer, cited chunk ids)
    grade: Callable[[str, Chunk], bool] = lambda q, c: True       # is this chunk relevant to the question?
    rewrite: Callable[[str, list[str]], list[str]] = lambda q, tried: []   # new queries (synonyms, decomposition)
    verify: Callable[[str, str, list[Chunk]], bool] = lambda q, a, cs: True  # every claim supported?
    route: Callable[[str], str] = lambda q: "retrieve"            # "direct" | "retrieve" | "multi_hop"
    direct: Callable[[str], str] | None = None                   # answer without retrieval (chit-chat, maths)
    max_rounds: int = 3
    min_relevant: int = 1

    def run(self, question: str) -> AgenticAnswer:
        trace = [Step("route", {"route": (r := self.route(question))})]
        if r == "direct" and self.direct is not None:
            return AgenticAnswer(self.direct(question), [], r, 0, trace)

        queries, tried, relevant = [question], [], {}
        rounds = 0
        while queries and rounds < self.max_rounds:
            rounds += 1
            for q in queries:
                tried.append(q)
                found = self.search(q)
                keep = [c for c in found if self.grade(question, c)]
                trace += [Step("retrieve", {"query": q, "n": len(found)}),
                          Step("grade", {"kept": [c.chunk_id for c in keep], "dropped": len(found) - len(keep)})]
                for c in keep:
                    relevant.setdefault(c.chunk_id, c)
            enough = len(relevant) >= self.min_relevant
            if enough:
                chunks = list(relevant.values())
                text, cites = self.answer(question, chunks)
                cites = [c for c in cites if c in relevant]          # a citation must point to a chunk we gave
                ok = bool(text) and bool(cites) and self.verify(question, text, chunks)
                trace += [Step("answer", {"citations": cites}), Step("verify", {"ok": ok})]
                if ok:
                    return AgenticAnswer(text, cites, r, rounds, trace)
            # Corrective step: new queries we have not tried yet (multi-hop questions also land here).
            queries = [q for q in self.rewrite(question, tried) if q not in tried]
            trace.append(Step("rewrite", {"queries": queries}))
        trace.append(Step("abstain", {"reason": "budget exhausted" if queries else "no new queries"}))
        return AgenticAnswer(None, [], r, rounds, trace)


# ---------- LLM-backed building blocks (support.llm interface: .json(messages, schema)) ----------

GRADE_SCHEMA = {"type": "object", "properties": {"relevant": {"type": "boolean"}}, "required": ["relevant"]}
ROUTE_SCHEMA = {"type": "object", "properties": {"route": {"type": "string", "enum": ["direct", "retrieve", "multi_hop"]}},
                "required": ["route"]}
QUERIES_SCHEMA = {"type": "object", "properties": {"queries": {"type": "array", "items": {"type": "string"}}},
                  "required": ["queries"]}
VERIFY_SCHEMA = {"type": "object", "properties": {"supported": {"type": "boolean"}, "unsupported_claims":
                 {"type": "array", "items": {"type": "string"}}}, "required": ["supported"]}


def llm_grader(llm):
    def grade(question: str, chunk: Chunk) -> bool:
        p = f"Does this passage help answer the question? Question: {question}\nPassage: {chunk.indexed_text[:1500]}"
        return bool(llm.json([{"role": "user", "content": p}], GRADE_SCHEMA)["relevant"])
    return grade


def llm_router(llm):
    def route(question: str) -> str:
        p = ("Classify how to answer. direct = no documents needed (greeting, arithmetic). retrieve = one lookup in the "
             "knowledge base. multi_hop = needs facts from several documents combined.\nQuestion: " + question)
        return llm.json([{"role": "user", "content": p}], ROUTE_SCHEMA)["route"]
    return route


def llm_rewriter(llm, n: int = 2):
    def rewrite(question: str, tried: list[str]) -> list[str]:
        p = (f"The search queries {tried} did not find what is needed to answer: {question}\n"
             f"Write up to {n} different search queries: synonyms, the key entity alone, or the first sub-question "
             f"of a multi-step question.")
        return llm.json([{"role": "user", "content": p}], QUERIES_SCHEMA)["queries"][:n]
    return rewrite


def llm_verifier(llm):
    def verify(question: str, answer: str, chunks: list[Chunk]) -> bool:
        src = "\n\n".join(f"[{c.chunk_id}] {c.text}" for c in chunks)
        p = f"Is every claim in the answer supported by the sources?\nSources:\n{src}\n\nAnswer: {answer}"
        return bool(llm.json([{"role": "user", "content": p}], VERIFY_SCHEMA)["supported"])
    return verify

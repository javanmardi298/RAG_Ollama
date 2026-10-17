"""Stage 2 with LangChain: documents, retrievers, a hybrid retriever and an LCEL answer chain.

What changes compared with support.rag:
* chunks become langchain_core Documents (text + metadata),
* BM25 and dense search become Retriever objects with one interface (.invoke(query) -> list[Document]),
* hybrid search is a small custom retriever doing RRF (LangChain's EnsembleRetriever does weighted RRF too),
* the answer step is a chain: retrieve -> format -> prompt -> structured output.
What stays: the checks on citations and numbers (support.guardrails), because they are the safety net.
"""
from __future__ import annotations

from collections import Counter

from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import InMemoryVectorStore
from pydantic import BaseModel, Field

from ..guardrails import allowed_numbers, check_output
from ..rag import load_chunks, tokenize


def policy_documents() -> list[Document]:
    """Same chunks as the plain version (title + paragraph), as LangChain Documents."""
    return [Document(page_content=c.indexed_text,
                     metadata={"chunk_id": c.chunk_id, "doc_id": c.doc_id, "lang": c.lang, "title": c.title})
            for c in load_chunks()]


class RRFRetriever(BaseRetriever):
    """Reciprocal Rank Fusion over several retrievers. Subclassing BaseRetriever makes it a Runnable."""

    retrievers: list[BaseRetriever]
    k: int = 3
    c: int = 60

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        score, by_id = Counter(), {}
        for r in self.retrievers:
            for rank, doc in enumerate(r.invoke(query, config={"callbacks": run_manager.get_child()})):
                key = doc.metadata["chunk_id"]
                score[key] += 1 / (self.c + rank + 1)
                by_id[key] = doc
        return [by_id[key] for key, _ in score.most_common(self.k)]


def build_retrievers(embedding, k: int = 3, depth: int = 10) -> dict[str, BaseRetriever]:
    """One hybrid retriever per language (we answer German customers from German policies)."""
    docs = policy_documents()
    out = {}
    for lang in ("en", "de"):
        part = [d for d in docs if d.metadata["lang"] == lang]
        # same tokenizer as the plain BM25 (the default just splits on spaces); needs `pip install rank_bm25`
        bm25 = BM25Retriever.from_documents(part, k=depth, preprocess_func=tokenize)
        dense = InMemoryVectorStore.from_documents(part, embedding).as_retriever(search_kwargs={"k": depth})
        out[lang] = RRFRetriever(retrievers=[bm25, dense], k=k)
    return out


class Answer(BaseModel):
    answerable: bool = Field(description="false if the sources do not answer the question")
    answer: str = Field(description="1-3 sentences in the customer's language")
    citations: list[str] = Field(description="ids of the sources used, e.g. returns#2")


ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Answer the customer's question using ONLY the sources. Answer in {language}. "
               "Cite the source ids you used. If the sources do not answer the question, set answerable=false."),
    ("human", "Sources:\n{sources}\n\nQuestion: {question}"),
])


def format_docs(docs: list[Document]) -> str:
    return "\n\n".join(f"[{d.metadata['chunk_id']}] {d.page_content}" for d in docs)


def make_answer_fn(model, retrievers: dict[str, BaseRetriever]):
    """Returns answer(question, lang) -> {"answer": str | None, "sources": [...]}, the interface the agents use."""
    chain = ANSWER_PROMPT | model.with_structured_output(Answer)

    def answer(question: str, lang: str) -> dict:
        docs = retrievers[lang].invoke(question)
        sources = format_docs(docs)
        out = chain.invoke({"sources": sources, "question": question,
                            "language": "German" if lang == "de" else "English"})
        ids = {d.metadata["chunk_id"] for d in docs}
        cited_ok = bool(out.citations) and set(out.citations) <= ids
        numbers_ok = check_output(out.answer, allowed_numbers({"s": sources}, {"q": question})).ok
        ok = out.answerable and cited_ok and numbers_ok
        return {"answer": out.answer if ok else None, "sources": out.citations,
                "checks": {"answerable": out.answerable, "citations_valid": cited_ok, "numbers_supported": numbers_ok}}
    return answer

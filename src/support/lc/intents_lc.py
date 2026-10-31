"""Stage 1 with LangChain: the LLM intent classifier as an LCEL chain.

Compare with support.intents.LLMClassifier: same idea (dynamic few-shot + constrained output),
written as  prompt | model.with_structured_output(schema).
"""
from __future__ import annotations

from typing import Literal

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, create_model
from sklearn.feature_extraction.text import TfidfVectorizer

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Classify the customer message of an online furniture store into exactly one intent.\n"
     "Use 'oos' if the message is not about orders, delivery, payment, refunds or the account."),
    ("human", "{examples}\n\nMessage: \"{text}\""),
])


def intent_schema(labels: list[str]):
    """A Pydantic model whose `intent` field only accepts the known labels.

    with_structured_output turns this into a JSON schema with an enum, so the model cannot
    invent a label; LangChain also validates and parses the reply into this class.
    """
    return create_model("IntentChoice",
                        intent=(Literal[tuple(sorted(labels))], Field(description="the single best intent")))


class ExampleSelector:
    """Picks the k most similar training messages (TF-IDF cosine), like the plain version.

    LangChain also has SemanticSimilarityExampleSelector (embedding-based) for the same job.
    """

    def __init__(self, train: pd.DataFrame, k: int = 8):
        self.train, self.k = train.reset_index(drop=True), k
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(self.train["text"])
        self.X = self.vec.transform(self.train["text"])

    def __call__(self, text: str) -> str:
        sims = (self.X @ self.vec.transform([text]).T).toarray().ravel()
        idx = sims.argsort()[::-1][: self.k]
        return "Examples:\n" + "\n".join(f'"{self.train.text[i]}" -> {self.train.intent[i]}' for i in idx)


def make_intent_chain(model, train: pd.DataFrame, labels: list[str], k: int = 8):
    """Returns a Runnable: {"text": ...} -> IntentChoice.

    The leading lambda is coerced into a RunnableLambda, so the whole thing supports
    .invoke, .batch (parallel), .stream and tracing like any other LangChain component.
    """
    select = ExampleSelector(train, k)
    add_examples = lambda x: {"text": x["text"], "examples": select(x["text"])}  # noqa: E731
    return add_examples | PROMPT | model.with_structured_output(intent_schema(labels))


def predict(chain, texts: list[str], max_concurrency: int = 2) -> list[str]:
    """.batch runs several requests at once; keep concurrency low for a local Ollama."""
    out = chain.batch([{"text": t} for t in texts], config={"max_concurrency": max_concurrency})
    return [o.intent for o in out]

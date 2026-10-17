"""Model factories: one place to switch model names, temperature or provider."""
from __future__ import annotations

import os

CHAT_MODEL = os.getenv("SUPPORT_MODEL", "qwen2.5:7b")
EMBED_MODEL = os.getenv("SUPPORT_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def chat_model(temperature: float = 0.0, model: str = CHAT_MODEL):
    """A LangChain chat model backed by the local Ollama server.

    Swapping provider (OpenAI, Anthropic, Mistral...) only changes this function:
    every chain and graph talks to the same BaseChatModel interface.
    """
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, temperature=temperature, base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"))


def embeddings(model: str = EMBED_MODEL):
    """The same multilingual encoder as the plain version, wrapped as LangChain Embeddings."""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=model, encode_kwargs={"normalize_embeddings": True})

"""Contextual retrieval: before indexing, give every chunk a short LLM-written sentence that situates it in its
document ("This section of the 2026 returns policy covers custom-made furniture."). The context is prepended
for BOTH the embedding and the BM25 index. Anthropic reported 35% fewer top-20 retrieval failures with
contextual embeddings and 49% with contextual embeddings + contextual BM25 (67% with reranking on top).

Cost is one LLM call per chunk; with prompt caching the whole document is paid once. Cache results on disk:
re-indexing must not re-pay for unchanged chunks.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .chunking import Chunk
from .loaders import Document

PROMPT = ("<document>\n{doc}\n</document>\nHere is a chunk from that document:\n<chunk>\n{chunk}\n</chunk>\n"
          "Write one short sentence (max 40 words) that situates this chunk within the document, to improve search "
          "retrieval of the chunk. Answer only with the sentence.")


def contextualize(llm, doc: Document, chunks: list[Chunk], cache_file: str | Path | None = None,
                  max_doc_chars: int = 20_000) -> list[Chunk]:
    """Returns new chunks whose meta['context'] is the generated sentence (indexed_text picks it up)."""
    cache = {}
    if cache_file and Path(cache_file).exists():
        cache = json.loads(Path(cache_file).read_text(encoding="utf-8"))
    out = []
    for c in chunks:
        key = hashlib.sha256(f"{doc.doc_id}\0{c.text}".encode()).hexdigest()[:24]
        if key not in cache:
            reply = llm.chat([{"role": "user", "content": PROMPT.format(doc=doc.text[:max_doc_chars], chunk=c.text)}])
            cache[key] = " ".join(reply.content.split())[:400]
        title = c.meta.get("context") or doc.meta.get("title", "")
        out.append(Chunk(c.chunk_id, c.doc_id, c.text, {**c.meta, "context": f"{title}. {cache[key]}".strip(". ")}))
    if cache_file:
        Path(cache_file).write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
    return out

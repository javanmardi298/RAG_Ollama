"""Chunking strategies. Chunk size is a retrieval parameter: measure recall@k for each strategy, do not guess.

* fixed      every n words with overlap: simple baseline
* recursive  split on paragraphs, then sentences, then words, until pieces fit
* headings   one chunk per markdown section, heading path kept as context ("Returns > Exceptions")
* python     one chunk per top-level function / class (code search needs whole units, not windows)
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from .loaders import Document


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    meta: dict = field(default_factory=dict)

    @property
    def indexed_text(self) -> str:
        """What gets indexed: the context (title / heading path) travels with the text."""
        ctx = self.meta.get("context")
        return f"{ctx}. {self.text}" if ctx else self.text


def _words(text: str) -> list[str]:
    return text.split()


def fixed(doc: Document, size: int = 200, overlap: int = 40) -> list[Chunk]:
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    w = _words(doc.text)
    out, start, i = [], 0, 0
    while start < len(w):
        out.append(Chunk(f"{doc.doc_id}#{i}", doc.doc_id, " ".join(w[start:start + size]),
                         {**doc.meta, "context": doc.meta.get("title", "")}))
        if start + size >= len(w):
            break
        start += size - overlap
        i += 1
    return out


_SENT = re.compile(r"(?<=[.!?؟。])\s+")


def recursive(doc: Document, max_words: int = 200) -> list[Chunk]:
    def split(text: str, level: int) -> list[str]:
        if len(_words(text)) <= max_words:
            return [text]
        parts = (text.split("\n\n") if level == 0 else _SENT.split(text) if level == 1 else None)
        if parts is None or len(parts) == 1:
            if level < 2 and parts is not None:
                return split(text, level + 1)
            w = _words(text)
            return [" ".join(w[i:i + max_words]) for i in range(0, len(w), max_words)]
        pieces, buf = [], ""
        for p in parts:
            cand = f"{buf}\n\n{p}".strip() if level == 0 else f"{buf} {p}".strip()
            if len(_words(cand)) <= max_words:
                buf = cand
            else:
                if buf:
                    pieces.append(buf)
                buf = p
        if buf:
            pieces.append(buf)
        return [s for piece in pieces for s in split(piece, level + 1)]

    texts = [t.strip() for t in split(doc.text, 0) if t.strip()]
    return [Chunk(f"{doc.doc_id}#{i}", doc.doc_id, t, {**doc.meta, "context": doc.meta.get("title", "")})
            for i, t in enumerate(texts)]


_H = re.compile(r"^(#{1,6})\s+(.*)$")


def headings(doc: Document, max_words: int = 300) -> list[Chunk]:
    """Split at markdown headings; each chunk carries its heading path. Long sections are split recursively."""
    out, path, buf = [], [], []

    def flush():
        text = "\n".join(buf).strip()
        if not text:
            return
        ctx = " > ".join([doc.meta.get("title", "")] + [h for _, h in path] if doc.meta.get("title") else [h for _, h in path])
        sub = Document(doc.doc_id, text, {**doc.meta, "title": ctx})
        for c in recursive(sub, max_words):
            out.append(Chunk(f"{doc.doc_id}#{len(out)}", doc.doc_id, c.text, {**doc.meta, "context": ctx,
                                                                                  "section": path[-1][1] if path else ""}))

    for line in doc.text.splitlines():
        m = _H.match(line)
        if m:
            flush(); buf.clear()
            level = len(m.group(1))
            path = [(lv, h) for lv, h in path if lv < level] + [(level, m.group(2).strip())]
        else:
            buf.append(line)
    flush()
    return out


def python_code(doc: Document) -> list[Chunk]:
    """One chunk per top-level function or class, with its qualified name and line range."""
    tree = ast.parse(doc.text)
    lines = doc.text.splitlines()
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            text = "\n".join(lines[start - 1:node.end_lineno])
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            out.append(Chunk(f"{doc.doc_id}::{node.name}", doc.doc_id, text,
                             {**doc.meta, "context": f"{doc.meta.get('title', doc.doc_id)} {kind} {node.name}",
                              "symbol": node.name, "kind": kind, "lines": (start, node.end_lineno),
                              "docstring": ast.get_docstring(node) or ""}))
    return out


STRATEGIES = {"fixed": fixed, "recursive": recursive, "headings": headings, "python": python_code}


def chunk_all(docs: list[Document], strategy: str = "recursive", **kw) -> list[Chunk]:
    fn = STRATEGIES[strategy]
    return [c for d in docs for c in (fn(d) if strategy == "python" else fn(d, **kw))]

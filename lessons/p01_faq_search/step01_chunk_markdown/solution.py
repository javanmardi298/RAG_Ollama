"""Step 1: split a markdown document into chunks that keep their heading path."""
from __future__ import annotations


def chunk_markdown(text: str, doc_id: str) -> list[dict]:
    """Return [{"id": "returns#0", "doc_id": "returns", "heading": "Returns > Return window", "text": "..."}, ...]"""
    chunks: list[dict] = []
    h1, h2, buf = "", "", []

    def flush():
        body = " ".join(" ".join(buf).split())
        if body:
            heading = " > ".join(x for x in (h1, h2) if x)
            chunks.append({"id": f"{doc_id}#{len(chunks)}", "doc_id": doc_id, "heading": heading, "text": body})
        buf.clear()

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            h2 = line[3:].strip()
        elif line.startswith("# "):
            flush()
            h1, h2 = line[2:].strip(), ""
        else:
            buf.append(line)
    flush()
    return chunks


if __name__ == "__main__":
    from learn.data import faq_docs
    for name, text in faq_docs().items():
        for c in chunk_markdown(text, name):
            print(c["id"], "|", c["heading"], "|", c["text"][:50])

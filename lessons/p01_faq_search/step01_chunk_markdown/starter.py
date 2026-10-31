"""Step 1: split a markdown document into chunks that keep their heading path."""
from __future__ import annotations


def chunk_markdown(text: str, doc_id: str) -> list[dict]:
    """Return [{"id": "returns#0", "doc_id": "returns", "heading": "Returns > Return window", "text": "..."}, ...]"""
    chunks: list[dict] = []
    h1, h2, buf = "", "", []

    def flush():
        # TODO 1: turn the lines in `buf` into one clean string (hint: " ".join(" ".join(buf).split()))
        #         if it is not empty, append a chunk dict to `chunks`, then clear `buf`.
        raise NotImplementedError("TODO 1: flush() builds a chunk from buf")

    for line in text.splitlines():
        # TODO 2: a line starting with "## " ends the current chunk and sets h2;
        #         a line starting with "# " ends the current chunk, sets h1 and resets h2;
        #         any other line belongs to the current chunk.
        raise NotImplementedError("TODO 2: walk through the lines")
    flush()
    return chunks


if __name__ == "__main__":
    from learn.data import faq_docs
    for name, text in faq_docs().items():
        for c in chunk_markdown(text, name):
            print(c["id"], "|", c["heading"], "|", c["text"][:50])

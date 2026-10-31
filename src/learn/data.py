"""Small fixed datasets the lessons share (in lessons/_data, no download)."""
from __future__ import annotations

import csv

from support.config import ROOT

DATA = ROOT / "lessons" / "_data"


def faq_docs() -> dict[str, str]:
    """doc id (file name) -> markdown text of the FAQ pages."""
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted((DATA / "faq").glob("*.md"))}


def faq_questions() -> list[dict]:
    """[{question, relevant (doc id or ''), answerable ('yes'/'no')}]"""
    with (DATA / "faq_questions.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def faq_chunks() -> list[dict]:
    """The FAQ pages cut at '##' headings (the same result as the step 1 solution), ready for the later steps."""
    out = []
    for name, text in faq_docs().items():
        sections, title, heading, buf = [], "", "", []
        for line in text.splitlines() + ["# "]:                 # the sentinel closes the last section
            if line.startswith("#"):
                body = " ".join(" ".join(buf).split())
                if body:
                    sections.append((" > ".join(x for x in (title, heading) if x), body))
                buf = []
                if line.startswith("## "):
                    heading = line[3:].strip()
                else:
                    title, heading = line[2:].strip(), ""
            else:
                buf.append(line)
        out += [{"id": f"{name}#{i}", "doc_id": name, "heading": h, "text": t} for i, (h, t) in enumerate(sections)]
    return out


_STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "can", "how", "what", "it", "we", "your", "for", "in", "by"}


def retrieve(question: str, chunks: list[dict], k: int = 3) -> list[dict]:
    """Tiny word-overlap retriever so later steps can run end to end (the real ones are your BM25 / hybrid from steps 2-4)."""
    import re

    def ws(t):
        return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in _STOP}
    q = ws(question)
    scored = [(len(q & ws(c["heading"] + " " + c["text"])), i) for i, c in enumerate(chunks)]
    return [chunks[i] for s, i in sorted(scored, key=lambda t: (-t[0], t[1])) if s > 0][:k]


_SYN = {"send back": "return", "money back": "refund", "broken": "damage defect", "couch": "sofa"}
_GSTOP = _STOP | {"there", "much", "many", "get", "have", "long", "when", "where", "if", "be", "at", "from", "this", "that", "with", "and", "or", "on"}


def rule_grade(question: str, chunk: dict, min_ratio: float = 0.5) -> bool:
    """The rule grader of p22 step 2 (at least half of the question's content words appear in the chunk)."""
    import re

    def ws(t):
        return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in _GSTOP and len(w) > 1}
    q = question.lower()
    for a, b in _SYN.items():
        q = q.replace(a, b)
    qs = ws(q)
    return bool(qs) and len(qs & ws(chunk["heading"] + " " + chunk["text"])) / len(qs) >= min_ratio

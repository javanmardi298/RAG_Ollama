"""A minimal knowledge graph for GraphRAG experiments: triples, k-hop neighbourhoods, paths, provenance.

Vector RAG finds passages that look like the question; multi-hop questions ("which supplier of the product that
failed most often is based in Germany?") need facts connected across documents. Extract (subject, relation, object)
triples with an LLM, keep the chunk each came from, and retrieve a neighbourhood around the question's entities.
For large graphs use networkx or Neo4j; the ideas are the same.
"""
from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Triple:
    s: str
    r: str
    o: str
    source: str = ""          # chunk id the fact came from (citations!)


def norm_entity(name: str) -> str:
    """Entity resolution, the cheap version: case, spacing, punctuation. Real projects need aliases too."""
    return re.sub(r"[^\w]+", " ", name.lower()).strip()


class Graph:
    def __init__(self, triples: list[Triple] = ()):
        self.triples: list[Triple] = []
        self.out: dict[str, list[Triple]] = defaultdict(list)
        self.inc: dict[str, list[Triple]] = defaultdict(list)
        self.aliases: dict[str, str] = {}
        for t in triples:
            self.add(t)

    def alias(self, name: str, canonical: str) -> None:
        self.aliases[norm_entity(name)] = norm_entity(canonical)

    def key(self, name: str) -> str:
        k = norm_entity(name)
        return self.aliases.get(k, k)

    def add(self, t: Triple) -> None:
        t = Triple(self.key(t.s), t.r.strip().lower(), self.key(t.o), t.source)
        if t in self.triples:
            return
        self.triples.append(t)
        self.out[t.s].append(t)
        self.inc[t.o].append(t)

    def neighbourhood(self, entity: str, hops: int = 2, max_triples: int = 50) -> list[Triple]:
        """All triples within `hops` of the entity (both directions), nearest first."""
        start = self.key(entity)
        seen, found, queue = {start}, [], deque([(start, 0)])
        while queue and len(found) < max_triples:
            node, d = queue.popleft()
            if d == hops:
                continue
            for t in self.out[node] + self.inc[node]:
                if t not in found:
                    found.append(t)
                nxt = t.o if t.s == node else t.s
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, d + 1))
        return found[:max_triples]

    def path(self, a: str, b: str, max_hops: int = 4) -> list[Triple] | None:
        """Shortest chain of facts linking two entities (the explanation of a multi-hop answer)."""
        a, b = self.key(a), self.key(b)
        prev: dict[str, tuple[str, Triple]] = {}
        queue, seen = deque([(a, 0)]), {a}
        while queue:
            node, d = queue.popleft()
            if node == b:
                chain, cur = [], b
                while cur != a:
                    cur, t = prev[cur][0], prev[cur][1]
                    chain.append(t)
                return chain[::-1]
            if d == max_hops:
                continue
            for t in self.out[node] + self.inc[node]:
                nxt = t.o if t.s == node else t.s
                if nxt not in seen:
                    seen.add(nxt)
                    prev[nxt] = (node, t)
                    queue.append((nxt, d + 1))
        return None

    def entities_in(self, text: str) -> list[str]:
        """Graph entities mentioned in a question (longest first, so 'acme gmbh' beats 'acme')."""
        low = " " + norm_entity(text) + " "
        names = sorted(set(self.out) | set(self.inc) | set(self.aliases), key=len, reverse=True)
        found = []
        for n in names:
            if f" {n} " in low:
                found.append(self.aliases.get(n, n))
                low = low.replace(f" {n} ", " ")
        return list(dict.fromkeys(found))

    @staticmethod
    def as_context(triples: list[Triple]) -> str:
        return "\n".join(f"({t.s}) -[{t.r}]-> ({t.o})" + (f" [{t.source}]" if t.source else "") for t in triples)


TRIPLE_SCHEMA = {"type": "object", "properties": {"triples": {"type": "array", "items": {
    "type": "object", "properties": {"s": {"type": "string"}, "r": {"type": "string"}, "o": {"type": "string"}},
    "required": ["s", "r", "o"]}}}, "required": ["triples"]}


def extract_triples(llm, chunk_id: str, text: str, relations: list[str] | None = None) -> list[Triple]:
    """LLM extraction with a fixed relation vocabulary (free-form relations make the graph unusable)."""
    rel = f"Use only these relations: {', '.join(relations)}.\n" if relations else ""
    out = llm.json([{"role": "user", "content": f"Extract factual (subject, relation, object) triples.\n{rel}"
                     f"Use names exactly as written. Text:\n{text}"}], TRIPLE_SCHEMA)
    allowed = {r.lower() for r in relations} if relations else None
    return [Triple(t["s"], t["r"], t["o"], chunk_id) for t in out.get("triples", [])
            if t.get("s") and t.get("o") and (allowed is None or t["r"].lower() in allowed)]

# Starter: GraphRAG basics. data/triples.jsonl holds facts with their source; eval/questions.jsonl has
# multi-hop questions with the answer entity. Without a model it answers by graph paths; with Ollama you can
# extract triples from your own chunks (labkit.graph.extract_triples) and compare with vector RAG.
#   python run.py
import os, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
from labkit.graph import Graph, Triple

triples = [Triple(**json.loads(l)) for l in (HERE / "data" / "triples.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
g = Graph(triples)
g.alias("Holz Aktiengesellschaft", "Holz AG")
print(f"{len(g.triples)} triples, {len(set(g.out) | set(g.inc))} entities")
hits = 0
for line in (HERE / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines():
    q = json.loads(line)
    ents = g.entities_in(q["question"])
    chain = g.path(ents[0], q["answer"]) if ents else None
    ok = chain is not None and len(chain) == q["hops"]
    hits += ok
    print("OK  " if ok else "MISS", q["question"])
    if chain:
        print("     " + Graph.as_context(chain).replace("\n", "\n     "))
print(f"path found with the expected number of hops: {hits}")

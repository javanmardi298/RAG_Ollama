# Starter: Agentic RAG = route -> retrieve -> grade -> rewrite -> answer -> verify -> abstain (labkit.agentic_rag).
#   python run.py     runs offline with simple rule-based graders, so you see the loop and the metrics first;
#                     set use_llm: true in config.yaml to use Ollama for routing, grading, rewriting and verifying.
# eval/questions.csv: answerable=yes (expected doc), no (must abstain) or direct (no retrieval needed).
import csv, re
import os, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
(HERE / "results").mkdir(exist_ok=True)
from labkit.agentic_rag import AgenticRAG, llm_grader, llm_rewriter, llm_router, llm_verifier
from labkit.chunking import chunk_all
from labkit.loaders import load_dir
from labkit.retrieval import Index

docs = load_dir(HERE / "data")
index = Index(chunk_all(docs, "recursive"))
k = int(cfg.get("k", 5))
STOP = {"a", "an", "the", "do", "does", "i", "you", "my", "is", "can", "to", "of", "what", "how", "when", "will", "for",
        "with", "after", "be", "it", "need", "have", "many", "long", "your", "are", "there", "send", "back"}
SYN = {"send back": "return", "refunded": "refund money back", "delivery": "shipping delivery", "broken": "defect warranty",
       "covered": "warranty", "custom-made": "custom-made"}


def terms(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9-]+", s.lower()) if w not in STOP}


def search(q: str):
    return index.search(q, k=k, mode="bm25")


# ---- offline building blocks (rules); the LLM versions replace them when use_llm is true ----
def expand(q: str) -> str:
    q = q.lower()
    for a, b in SYN.items():
        q = q.replace(a, b)
    return q


def grade(q, c):                       # relevant if the chunk shares a content word with the question
    return len(terms(expand(q)) & terms(c.text)) >= 1     # naive on purpose: "phone number" matches "order number"


def rewrite(q, tried):                 # corrective step: synonyms, then the content words alone
    return [x for x in [expand(q), " ".join(sorted(terms(expand(q))))] if x not in tried]


def answer(q, chunks):                 # extractive: best sentence of the best chunk, cited
    qt = terms(expand(q))
    best = max(chunks, key=lambda c: len(qt & terms(c.text)))
    body = " ".join(line for line in best.text.splitlines() if not line.startswith("#"))
    sents = re.split(r"(?<=[.!?])\s+", body)
    return max(sents, key=lambda s: len(qt & terms(s))).strip(), [best.chunk_id]


def verify(q, a, chunks):              # every content word of the answer appears in the sources
    src = terms(" ".join(c.text for c in chunks))
    return len(terms(a) - src) == 0


def route(q):
    return "direct" if q.strip().lower() in {"hello", "hi", "thanks"} else "retrieve"


rag = AgenticRAG(search=search, answer=answer, grade=grade, rewrite=rewrite, verify=verify, route=route,
                 direct=lambda q: "Hello! How can I help?", max_rounds=int(cfg.get("max_rounds", 3)),
                 min_relevant=int(cfg.get("min_relevant", 1)))
if cfg.get("use_llm"):
    from support.llm import OllamaLLM
    llm = OllamaLLM(cfg.get("llm", "qwen2.5:7b"), temperature=0)
    rag.grade, rag.rewrite, rag.verify = llm_grader(llm), llm_rewriter(llm), llm_verifier(llm)
    if cfg.get("router", True):
        rag.route = llm_router(llm)

with (HERE / "eval" / "questions.csv").open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
results, stats = [], {"correct": 0, "wrong": 0, "abstained_correctly": 0, "abstained_wrongly": 0, "answered_unanswerable": 0}
for r in rows:
    out = rag.run(r["question"])
    cited_docs = {c.split("#")[0].split(":")[0] for c in out.citations}
    if r["answerable"] == "no":
        stats["abstained_correctly" if out.abstained else "answered_unanswerable"] += 1
    elif r["answerable"] == "direct":
        stats["correct" if out.route == "direct" else "wrong"] += 1
    elif out.abstained:
        stats["abstained_wrongly"] += 1
    else:
        stats["correct" if any(r["expected"] in d for d in cited_docs) else "wrong"] += 1
    results.append({"question": r["question"], "answer": out.answer, "citations": out.citations, "route": out.route,
                    "rounds": out.rounds, "trace": [(s.kind, s.detail) for s in out.trace]})
    print(f"{r['question'][:45]:45s} -> {'ABSTAIN' if out.abstained else (out.answer or '')[:50]!s:50s} rounds {out.rounds}")

print("\n", stats)
print("abstained correctly on", stats["abstained_correctly"], "of", sum(r["answerable"] == "no" for r in rows),
      "unanswerable questions; read results/agentic_rag.json for the full trace of each decision.")
(HERE / "results" / "agentic_rag.json").write_text(json.dumps({"stats": stats, "results": results}, indent=2, ensure_ascii=False),
                                                   encoding="utf-8")

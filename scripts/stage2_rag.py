# Stage 2: policy RAG. Retrieval runs on CPU (tiny corpus); answers via local Ollama.
# %%
import json, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.config import RESULTS_DIR
from support.rag import load_chunks, Retriever, retrieval_metrics, answer_question
from support.llm import OllamaLLM

qa = yaml.safe_load((ROOT / "eval" / "policy_qa.yaml").read_text(encoding="utf-8"))
answerable = [q for q in qa if q["doc"]]
chunks = load_chunks()
print(len(chunks), "chunks")

# %% Retrieval: BM25 vs dense vs hybrid
from sentence_transformers import SentenceTransformer
enc = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
retriever = Retriever(chunks, encoder=enc)
rows = [retrieval_metrics(retriever, answerable, k=3, mode=m) for m in ("bm25", "dense", "hybrid")]
for r in rows: print(r)

# %% Answers: citations valid, numbers supported, required fact present, unanswerable refused
llm = OllamaLLM("qwen2.5:7b")
results = []
for q in qa:
    out = answer_question(llm, q["question"], retriever.search(q["question"], q["lang"], 3), q["lang"])
    fact_ok = q["must_mention"].lower() in out["answer"].lower() if q["doc"] else not out["answerable"]
    results.append({**q, **out, "fact_ok": fact_ok})
ans = [r for r in results if r["doc"]]
summary = {
    "retrieval": rows,
    "answer_fact_rate": sum(r["fact_ok"] for r in ans) / len(ans),
    "citation_valid_rate": sum(r["citations_valid"] for r in ans) / len(ans),
    "numbers_supported_rate": sum(r["numbers_supported"] for r in results) / len(results),
    "unanswerable_refused_rate": sum(r["fact_ok"] for r in results if not r["doc"]) / max(1, sum(not r["doc"] for r in results)),
}
print(json.dumps(summary, indent=2))
(RESULTS_DIR / "stage2_rag.json").write_text(json.dumps({"summary": summary, "items": results}, indent=2, ensure_ascii=False))

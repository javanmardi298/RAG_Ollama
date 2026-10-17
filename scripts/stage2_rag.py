# Stage 2: policy RAG. Retrieval runs on CPU (tiny corpus); answers via local Ollama.
# Parameters: configs/project.yaml -> rag.*, embeddings.model, llm.chat_model
# %%
import json, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.config import RESULTS_DIR
from support.rag import answer_question, retrieval_metrics
from support.runtime import make_encoder, make_llm, make_retriever
from support.settings import settings

R = settings().rag
qa = yaml.safe_load((ROOT / "eval" / "policy_qa.yaml").read_text(encoding="utf-8"))
answerable = [q for q in qa if q["doc"]]

# %% Retrieval: BM25 vs dense vs hybrid, same questions, same k
retriever = make_retriever(encoder=make_encoder())
print(len(retriever.chunks), "chunks")
rows = [retrieval_metrics(retriever, answerable, k=R.k, mode=m) for m in ("bm25", "dense", "hybrid")]
for r in rows:
    print(r)
# Which questions does the configured mode miss? Read them: they tell you WHY (synonyms, language, chunking).
misses = [q["question"] for q in answerable
          if q["doc"] not in [c.doc_id for c in retriever.search(q["question"], q["lang"], R.k, R.mode)]]
print(f"missed by {R.mode}@{R.k}:", misses or "none")

# %% Answers: citations valid, numbers supported, required fact present, unanswerable refused
llm = make_llm("agent")
results = []
for q in qa:
    out = answer_question(llm, q["question"], retriever.search(q["question"], q["lang"], R.k, R.mode), q["lang"])
    fact_ok = q["must_mention"].lower() in out["answer"].lower() if q["doc"] else not out["answerable"]
    results.append({**q, **out, "fact_ok": fact_ok})
ans = [r for r in results if r["doc"]]
summary = {
    "mode": R.mode, "k": R.k,
    "retrieval": rows,
    "missed_questions": misses,
    "answer_fact_rate": sum(r["fact_ok"] for r in ans) / len(ans),
    "citation_valid_rate": sum(r["citations_valid"] for r in ans) / len(ans),
    "numbers_supported_rate": sum(r["numbers_supported"] for r in results) / len(results),
    "unanswerable_refused_rate": sum(r["fact_ok"] for r in results if not r["doc"]) / max(1, sum(not r["doc"] for r in results)),
}
print(json.dumps(summary, indent=2))
(RESULTS_DIR / "stage2_rag.json").write_text(json.dumps({"summary": summary, "items": results}, indent=2,
                                                        ensure_ascii=False), encoding="utf-8")

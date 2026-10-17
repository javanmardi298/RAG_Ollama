# Stage 2 (LangChain version): Documents, retrievers, hybrid RRF retriever, structured answer chain.
# %%
import json, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.config import RESULTS_DIR
from support.lc.models import chat_model, embeddings
from support.lc.rag_lc import build_retrievers, make_answer_fn

qa = yaml.safe_load((ROOT / "eval" / "policy_qa.yaml").read_text(encoding="utf-8"))
retrievers = build_retrievers(embeddings(), k=3)

# %% Retrieval: same metric as the plain version (gold document in the top 3)
hits = [q["doc"] in [d.metadata["doc_id"] for d in retrievers[q["lang"]].invoke(q["question"])] for q in qa if q["doc"]]
print("recall@3 (LangChain hybrid):", round(sum(hits) / len(hits), 3))

# %% Answers with the same checks
answer = make_answer_fn(chat_model(), retrievers)
rows = []
for q in qa:
    out = answer(q["question"], q["lang"])
    ok = (q["must_mention"].lower() in (out["answer"] or "").lower()) if q["doc"] else out["answer"] is None
    rows.append({**q, **out, "fact_ok": ok})
print("fact rate:", sum(r["fact_ok"] for r in rows) / len(rows))
(RESULTS_DIR / "lc_stage2_rag.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))

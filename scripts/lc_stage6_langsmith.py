# Stage 6 (optional): the RAG question set as a LangSmith dataset + experiment.
# Needs a free LangSmith account:  export LANGSMITH_API_KEY=...  LANGSMITH_TRACING=true
# Privacy: inputs and outputs are sent to LangSmith's servers. Use only synthetic data (as here).
import sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from langsmith import Client
from support.lc.models import chat_model, embeddings
from support.lc.rag_lc import build_retrievers, make_answer_fn

client = Client()
qa = yaml.safe_load((ROOT / "eval" / "policy_qa.yaml").read_text(encoding="utf-8"))
name = "support-agent-policy-qa"
if not client.has_dataset(dataset_name=name):
    ds = client.create_dataset(dataset_name=name, description="Hand-written policy questions, EN/DE")
    client.create_examples(dataset_id=ds.id, examples=[
        {"inputs": {"question": q["question"], "lang": q["lang"]},
         "outputs": {"doc": q["doc"], "must_mention": q["must_mention"]}} for q in qa])

answer = make_answer_fn(chat_model(), build_retrievers(embeddings()))

def target(inputs: dict) -> dict:
    return answer(inputs["question"], inputs["lang"])

# Evaluators are plain functions: code-based checks, the same ones as the local evaluation.
def fact_present(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    if reference_outputs["doc"] is None:
        return {"key": "refused_unanswerable", "score": outputs["answer"] is None}
    return {"key": "fact_present", "score": reference_outputs["must_mention"].lower() in (outputs["answer"] or "").lower()}

def citations_valid(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    return {"key": "citations_valid", "score": bool(outputs.get("checks", {}).get("citations_valid"))}

client.evaluate(target, data=name, evaluators=[fact_present, citations_valid],
                experiment_prefix="hybrid-rrf-qwen2.5-7b", max_concurrency=2)

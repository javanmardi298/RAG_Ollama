# Starter: a budgeted tool-using agent loop (ReAct style) with a cost/latency ledger.
# Tools here: search over local documents (data/) and a calculator. Add web search (SearXNG) or repo tools later.
#   python run.py "your question"          needs Ollama with a tool-calling model (config.yaml: llm)
import os, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml
from labkit.chunking import chunk_all
from labkit.loaders import load_dir
from labkit.ops import Ledger, Metered
from labkit.retrieval import Index
from support.llm import OllamaLLM

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
docs = load_dir(HERE / "data")
index = Index(chunk_all(docs, "recursive")) if docs else None
ledger = Ledger(str(HERE / "results" / "ledger.db"))
llm = Metered(OllamaLLM(cfg.get("llm", "qwen2.5:7b"), temperature=0), ledger, feature="agent")
MAX_STEPS = int(cfg.get("max_steps", 8))

TOOLS = [
    {"type": "function", "function": {"name": "search", "description": "Search the local documents.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "calculate", "description": "Evaluate an arithmetic expression.",
     "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}},
]


def run_tool(name, args):
    if name == "search":
        if not index:
            return {"error": "no documents in data/"}
        return {"results": [{"source": c.chunk_id, "text": c.text[:500]} for c in index.search(args["query"], k=4, mode="bm25")]}
    if name == "calculate":
        expr = args["expression"]
        if not set(expr) <= set("0123456789+-*/(). "):
            return {"error": "only arithmetic is allowed"}
        return {"result": eval(expr, {"__builtins__": {}})}   # safe: characters checked above
    return {"error": f"unknown tool {name}"}


question = " ".join(sys.argv[1:]) or "What is 17% of 1499?"
messages = [{"role": "system", "content": "Answer the question. Use tools when needed. Cite sources as [source]. "
                                          "If the documents do not contain the answer, say so."},
            {"role": "user", "content": question}]
for step in range(1, MAX_STEPS + 1):
    reply = llm.chat(messages, tools=TOOLS)
    if not reply.tool_calls:
        print(reply.content)
        break
    messages.append({"role": "assistant", "content": reply.content,
                     "tool_calls": [{"function": {"name": c.name, "arguments": c.arguments}} for c in reply.tool_calls]})
    for c in reply.tool_calls:
        out = run_tool(c.name, c.arguments)
        print(f"[step {step}] {c.name}({c.arguments}) -> {json.dumps(out)[:160]}")
        messages.append({"role": "tool", "tool_name": c.name, "content": json.dumps(out)})
else:
    print(f"Stopped: step budget ({MAX_STEPS}) reached. A real agent must end with a clear 'I could not finish'.")
print("ledger:", ledger.summary())

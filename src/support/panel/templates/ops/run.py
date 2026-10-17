# Starter: LLMOps layer around any LLM: cache, cost/latency ledger, cheap-to-strong router, versioned prompts.
# Runs without a model (a fake LLM simulates a cheap and a strong model); then plug in OllamaLLM / Claude.
#   python run.py
import os, random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
from labkit.ops import Cache, Ledger, Metered, Price, PromptRegistry, Router


class FakeLLM:
    """Stand-in: the cheap model sometimes returns an empty answer, the strong one never does."""
    def __init__(self, model, fail_rate):
        self.model, self.temperature, self.fail_rate = model, 0.0, fail_rate

    def chat(self, messages, **kw):
        ok = random.Random(messages[-1]["content"] + self.model).random() > self.fail_rate
        return type("R", (), {"content": f"[{self.model}] answer" if ok else "", "tool_calls": []})()


prompts = PromptRegistry()
v = prompts.register("faq", "Answer the customer question briefly: {question}")
ledger, cache = Ledger(str(HERE / "results" / "ledger.db")), Cache(str(HERE / "results" / "cache.db"), ttl_s=3600)
cheap = Metered(FakeLLM("small-local", 0.25), ledger, cache, Price(0, 0), feature="faq:cheap")
strong = Metered(FakeLLM("big-cloud", 0.0), ledger, cache, Price(2.0, 10.0), feature="faq:strong")
router = Router(cheap, strong, accept=lambda r: bool(r.content.strip()))

questions = [f"question {i % 40}" for i in range(200)]          # repeats -> cache hits
for q in questions:
    text, version = prompts.render("faq", question=q)
    router.chat([{"role": "user", "content": text}])
print(f"prompt faq@{v}; escalation rate {router.escalation_rate:.0%}; cache hits {cache.hits} / misses {cache.misses}")
for row in ledger.summary():
    print(row)
print("Next: replace FakeLLM with OllamaLLM (cheap) and a stronger model, and accept() with your output check.")

# Starter: GEPA-style prompt optimisation with train / validation / test (labkit.optimize).
#   python run.py     offline: the "prompt" is a list of routing rules a tiny keyword model follows, and the proposer
#                     adds a rule from a failure, so you see the loop, the Pareto front and the length penalty;
#                     set use_llm: true in config.yaml to optimise a real prompt with Ollama (task model + proposer).
import random, re
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
from labkit.optimize import llm_proposer, optimize

INTENTS = {"refund": ["refund", "money back", "reimburse"], "shipping": ["deliver", "shipping", "parcel", "arrive"],
           "cancel": ["cancel", "stop my order"], "return": ["return", "send back"]}
rng = random.Random(0)
templates = {"refund": ["I want my {} please", "how do I get a {}"], "shipping": ["when will it {}", "where is my {}"],
             "cancel": ["please {} it", "I need to {}"], "return": ["can I {} the chair", "how to {} an item"]}
data = [{"text": rng.choice(templates[i]).format(w), "label": i} for i in INTENTS for w in INTENTS[i] for _ in range(3)]
rng.shuffle(data)
train, val, test = data[:12], data[12:24], data[24:]


def offline_classify(prompt: str, text: str) -> str:
    """The 'model' follows rules written in the prompt: lines like  - refund: refund, money back"""
    for line in prompt.splitlines():
        m = re.match(r"\s*-\s*(\w+):\s*(.+)", line)
        if m and any(w.strip() and w.strip() in text.lower() for w in m.group(2).split(",")):
            return m.group(1)
    return "other"


def offline_propose(prompt: str, failures) -> str:
    ex, _, _ = failures[0]          # "reflection": add the missing phrase for the intent that failed
    words = [w for w in INTENTS[ex["label"]] if w in ex["text"].lower()]
    return prompt + f"\n- {ex['label']}: {words[0] if words else ex['text'].lower()}"


if cfg.get("use_llm"):
    from support.llm import OllamaLLM
    task_llm = OllamaLLM(cfg.get("llm", "qwen2.5:7b"), temperature=0)
    schema = {"type": "object", "properties": {"intent": {"type": "string", "enum": [*INTENTS, "other"]}}, "required": ["intent"]}
    classify = lambda prompt, text: task_llm.json([{"role": "system", "content": prompt}, {"role": "user", "content": text}], schema)["intent"]  # noqa: E731
    propose = llm_proposer(OllamaLLM(cfg.get("proposer_llm", cfg.get("llm", "qwen2.5:7b")), temperature=0.7))
    seed = "Classify the customer message into one intent: refund, shipping, cancel, return or other."
else:
    classify, propose = offline_classify, offline_propose
    seed = "Classify the message. Rules:\n- refund: refund"


def evaluate(prompt, ex):
    got = classify(prompt, ex["text"])
    return (1.0 if got == ex["label"] else 0.0), f"expected {ex['label']}, got {got} for: {ex['text']}"


acc = lambda prompt, xs: sum(evaluate(prompt, x)[0] for x in xs) / len(xs)  # noqa: E731
res = optimize(seed, train, val, evaluate, propose, budget=int(cfg.get("budget", 8)),
               length_penalty=float(cfg.get("length_penalty", 0.02)))
for i, c in enumerate(res["history"]):
    print(f"cand {i} parent {c.parent}  train {c.train_mean:.2f}  val(penalised) {c.val_score:.2f}  chars {len(c.prompt)}")
best = res["best"]
print(f"\nTEST accuracy (measured once, at the end): seed {acc(seed, test):.2f} -> best {acc(best.prompt, test):.2f}")
print("best prompt:\n" + best.prompt)
(HERE / "results" / "optimize.json").write_text(json.dumps(
    {"seed_test": acc(seed, test), "best_test": acc(best.prompt, test), "best_prompt": best.prompt,
     "history": [{"train": c.train_mean, "val": c.val_score, "chars": len(c.prompt), "parent": c.parent} for c in res["history"]]},
    indent=2), encoding="utf-8")

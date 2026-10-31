# Stage 1 (LangChain version): the LLM classifier as an LCEL chain. Compare with scripts/stage1_intents.py.
# pip install -r requirements-lc.txt
# %%
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.intents import evaluate, load_clinc_oos, load_splits, timed_predict, with_oos
from support.lc.intents_lc import make_intent_chain, predict
from support.lc.models import chat_model

splits = with_oos(load_splits(), load_clinc_oos())
train, dev = splits["train"], splits["dev"]
chain = make_intent_chain(chat_model(), train, labels=list(train.intent.unique()), k=8)

# %% One call: look at what the chain returns (a Pydantic object, already validated)
print(chain.invoke({"text": "i want my money back for the broken lamp"}))

# %% Same sample as the plain LLM classifier, so the two are directly comparable
sample = dev.groupby("intent", group_keys=False).apply(lambda g: g.sample(min(len(g), 8), random_state=7))
preds, ms = timed_predict(lambda texts: predict(chain, list(texts), max_concurrency=2), sample.text)
res = evaluate(sample.intent, preds, flags=sample.flags)
print({k: round(v, 4) for k, v in res.items() if isinstance(v, float)}, f"{ms:.0f} ms/msg")

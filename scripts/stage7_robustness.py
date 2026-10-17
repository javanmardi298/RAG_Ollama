# Stage 7: accuracy vs. noise level, and on German messages.
# %%
import json, sys, joblib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
from support.config import RESULTS_DIR, PROCESSED_DIR
from support.intents import load_splits, evaluate
from support.robustness import noisify, translate_batch
from support.llm import OllamaLLM

dev = load_splits()["dev"]
model = joblib.load(RESULTS_DIR / "intent_model.joblib")
curve = []
for level in range(4):
    noisy = [noisify(t, level) for t in dev.text]
    curve.append({"level": level, **{k: v for k, v in evaluate(dev.intent, model.predict(noisy)).items() if isinstance(v, float)}})
print(pd.DataFrame(curve))

# %% German test set: translate a stratified sample, then CHECK BY HAND (mark bad rows ok=False)
test = load_splits()["test"]
sample = test.groupby("intent", group_keys=False).apply(lambda g: g.sample(min(len(g), 10), random_state=7))
llm = OllamaLLM("qwen2.5:7b")
german = []
for i in range(0, len(sample), 10):
    german += translate_batch(llm, sample.text.iloc[i:i + 10].tolist())
sample = sample.assign(text_de=german, ok=True)
sample.to_csv(PROCESSED_DIR / "intents_test_de_TO_REVIEW.csv", index=False)
print("Review the file, set ok=False for bad translations, save as intents_test_de.csv")

# %% After review
de = pd.read_csv(PROCESSED_DIR / "intents_test_de.csv").query("ok")
res = evaluate(de.intent, model.predict(de.text_de))
print("German:", {k: round(v, 4) for k, v in res.items() if isinstance(v, float)})
(RESULTS_DIR / "stage7_robustness.json").write_text(json.dumps({"noise_curve": curve, "german": res}, indent=2, default=str))

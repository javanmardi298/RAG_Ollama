# Stage 7: accuracy vs. noise level, and on German messages.
# Parameters: configs/project.yaml -> robustness.*
# The German part has a manual step: translate -> YOU review -> evaluate. Run the script again after reviewing.
# %%
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
from support.config import RESULTS_DIR, PROCESSED_DIR, SEED
from support.intents import load_splits, evaluate
from support.robustness import noisify, translate_batch
from support.runtime import load_classifier, make_llm
from support.settings import settings

R = settings().robustness
model = load_classifier().model
dev = load_splits()["dev"]
curve = []
for level in range(R.max_noise_level + 1):
    noisy = [noisify(t, level, seed=SEED) for t in dev.text]
    curve.append({"level": level, **{k: v for k, v in evaluate(dev.intent, model.predict(noisy)).items() if isinstance(v, float)}})
print(pd.DataFrame(curve))
out = {"noise_curve": curve, "german": None, "german_status": "not started"}

# %% German test set: translate a stratified sample, then CHECK BY HAND (mark bad rows ok=False)
to_review, reviewed = PROCESSED_DIR / "intents_test_de_TO_REVIEW.csv", PROCESSED_DIR / "intents_test_de.csv"
if not reviewed.exists() and not to_review.exists() and R.translate:
    test = load_splits()["test"]
    sample = test.groupby("intent", group_keys=False).apply(lambda g: g.sample(min(len(g), R.german_per_intent), random_state=SEED))
    llm = make_llm("agent")
    german = []
    for i in range(0, len(sample), 10):
        german += translate_batch(llm, sample.text.iloc[i:i + 10].tolist())
        print(f"translated {len(german)}/{len(sample)}")
    sample.assign(text_de=german, ok=True).to_csv(to_review, index=False, encoding="utf-8")
if not reviewed.exists():
    out["german_status"] = "waiting for review" if to_review.exists() else "skipped (robustness.translate = false)"
    print(f"Review {to_review.name}: set ok=False for bad translations, add messages you wrote yourself, "
          f"save as {reviewed.name}, then run this stage again.")

# %% After review
if reviewed.exists():
    de = pd.read_csv(reviewed).query("ok")
    res = evaluate(de.intent, model.predict(de.text_de))
    out["german"], out["german_status"] = res, "evaluated"
    print("German:", {k: round(v, 4) for k, v in res.items() if isinstance(v, float)})
(RESULTS_DIR / "stage7_robustness.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

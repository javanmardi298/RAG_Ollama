# Stage 1: intent classification. Run cell by cell in VS Code (each "# %%" is a cell) or as a script.
# The embedding part is fastest on Colab (GPU); TF-IDF and the LLM part run locally.
# %%
import json, sys, joblib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from support.config import RESULTS_DIR, ensure_dirs
from support.intents import (load_splits, load_clinc_oos, with_oos, make_tfidf_model, EmbeddingClassifier,
                             LLMClassifier, evaluate, fit_temperature, apply_temperature, timed_predict)
ensure_dirs()
splits = with_oos(load_splits(), load_clinc_oos())
train, dev, test = splits["train"], splits["dev"], splits["test"]
print({k: len(v) for k, v in splits.items()})

# %% Model 1: TF-IDF + logistic regression
tfidf = make_tfidf_model().fit(train.text, train.intent)
proba, ms = timed_predict(tfidf.predict_proba, dev.text)
pred = tfidf.classes_[proba.argmax(1)]
res_tfidf = evaluate(dev.intent, pred, proba.max(1), dev.flags)
print("tfidf", {k: round(v, 4) for k, v in res_tfidf.items() if isinstance(v, float)}, f"{ms:.2f} ms/msg")
print("accuracy by flag:", res_tfidf.get("accuracy_by_flag"))

# %% Calibration: fit temperature on dev, check ECE before / after
y_idx = np.searchsorted(tfidf.classes_, dev.intent)
T = fit_temperature(proba, y_idx)
cal = apply_temperature(proba, T)
print(f"T={T:.2f}  ECE before={res_tfidf['ece']:.4f}  after={evaluate(dev.intent, pred, cal.max(1))['ece']:.4f}")

# %% Model 2: multilingual embeddings + logistic regression (Colab GPU recommended)
emb = EmbeddingClassifier()
X_train, X_dev = emb.encode(train.text), emb.encode(dev.text)
emb.fit(train.text, train.intent, X=X_train)
proba_e = emb.predict_proba(dev.text, X=X_dev)
pred_e = emb.classes_[proba_e.argmax(1)]
res_emb = evaluate(dev.intent, pred_e, proba_e.max(1), dev.flags)
print("embeddings", {k: round(v, 4) for k, v in res_emb.items() if isinstance(v, float)})

# %% Model 3: LLM with dynamic few-shot (local Ollama). Use a sample: ~1-3 s per message.
from support.llm import OllamaLLM
sample = dev.groupby("intent", group_keys=False).apply(lambda g: g.sample(min(len(g), 8), random_state=7))
llm_clf = LLMClassifier(OllamaLLM("qwen2.5:7b"), train, labels=list(train.intent.unique()), k=8)
pred_l, ms_l = timed_predict(llm_clf.predict, sample.text)
res_llm = evaluate(sample.intent, pred_l, flags=sample.flags)
print("llm", {k: round(v, 4) for k, v in res_llm.items() if isinstance(v, float)}, f"{ms_l:.0f} ms/msg")

# %% Choose on dev, report the winner ONCE on test, save it for the agent
best = tfidf   # replace by the model that wins on dev, considering speed and calibration too
proba_t = apply_temperature(best.predict_proba(test.text), T)
res_test = evaluate(test.intent, best.classes_[proba_t.argmax(1)], proba_t.max(1), test.flags)
joblib.dump(best, RESULTS_DIR / "intent_model.joblib")
(RESULTS_DIR / "temperature.txt").write_text(str(T))
summary = {"dev": {"tfidf": res_tfidf, "embeddings": res_emb, "llm_sample": res_llm}, "test": res_test}
(RESULTS_DIR / "stage1_intents.json").write_text(json.dumps(summary, indent=2, default=str))
print("test", {k: round(v, 4) for k, v in res_test.items() if isinstance(v, float)})

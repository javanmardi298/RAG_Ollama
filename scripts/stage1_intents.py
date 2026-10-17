# Stage 1: intent classification. Run cell by cell in VS Code (each "# %%" is a cell), as a script, or from the panel.
# The embedding part is fastest on Colab (GPU); TF-IDF and the LLM part run locally.
# Parameters: configs/project.yaml -> intents.*, embeddings.*, llm.chat_model
# %%
import json, sys, joblib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from support.config import RESULTS_DIR, SEED, ensure_dirs
from support.intents import (load_splits, load_clinc_oos, with_oos, make_tfidf_model, EmbeddingClassifier,
                             LLMClassifier, evaluate, fit_temperature, apply_temperature, timed_predict)
from support.runtime import make_llm
from support.settings import encoder_device, settings

S = settings().intents
ensure_dirs()
splits = with_oos(load_splits(), load_clinc_oos(settings().data.clinc_json or None),
                  test_oos_max=settings().data.test_oos_max)
train, dev, test = splits["train"], splits["dev"], splits["test"]
print({k: len(v) for k, v in splits.items()})


def short(res):
    return {k: round(v, 4) for k, v in res.items() if isinstance(v, float)}


def calibrate(model, proba, name):
    """Temperature fitted on dev for THIS model (a T from another model would be meaningless)."""
    pred = model.classes_[proba.argmax(1)]
    T = fit_temperature(proba, np.searchsorted(model.classes_, dev.intent))
    after = evaluate(dev.intent, pred, apply_temperature(proba, T).max(1))["ece"]
    print(f"{name}: T={T:.2f}  ECE after={after:.4f}")
    return T, after


# %% Model 1: TF-IDF + logistic regression
tfidf = make_tfidf_model(C=S.tfidf_C).fit(train.text, train.intent)
proba, ms = timed_predict(tfidf.predict_proba, dev.text)
res_tfidf = {**evaluate(dev.intent, tfidf.classes_[proba.argmax(1)], proba.max(1), dev.flags), "ms_per_msg": ms}
print("tfidf", short(res_tfidf), "| accuracy by flag:", res_tfidf.get("accuracy_by_flag"))
T_tfidf, res_tfidf["ece_calibrated"] = calibrate(tfidf, proba, "tfidf")
candidates = {"tfidf": (tfidf, T_tfidf)}

# %% Model 2: multilingual embeddings + logistic regression (Colab GPU recommended)
res_emb = None
if S.run_embeddings:
    emb = EmbeddingClassifier(settings().embeddings.model, C=S.embedding_C, device=encoder_device())
    X_train = emb.encode(train.text, batch_size=settings().embeddings.batch_size)
    emb.fit(train.text, train.intent, X=X_train)
    proba_e, ms_e = timed_predict(lambda t: emb.predict_proba(t), dev.text)
    res_emb = {**evaluate(dev.intent, emb.classes_[proba_e.argmax(1)], proba_e.max(1), dev.flags), "ms_per_msg": ms_e}
    print("embeddings", short(res_emb))
    T_emb, res_emb["ece_calibrated"] = calibrate(emb, proba_e, "embeddings")
    candidates["embeddings"] = (emb, T_emb)
else:
    print("embeddings: skipped (intents.run_embeddings = false)")

# %% Model 3: LLM with dynamic few-shot (local Ollama). Use a sample: ~1-3 s per message.
res_llm = None
if S.run_llm:
    sample = dev.groupby("intent", group_keys=False).apply(
        lambda g: g.sample(min(len(g), S.llm_sample_per_intent), random_state=SEED))
    llm_clf = LLMClassifier(make_llm("agent"), train, labels=list(train.intent.unique()), k=S.llm_few_shot_k)
    pred_l, ms_l = timed_predict(llm_clf.predict, sample.text)
    res_llm = {**evaluate(sample.intent, pred_l, flags=sample.flags), "ms_per_msg": ms_l}
    print("llm", short(res_llm), f"{ms_l:.0f} ms/msg")
else:
    print("llm: skipped (intents.run_llm = false)")

# %% Report the winner chosen on DEV once on test, save it for the agent
if S.winner not in candidates:
    raise SystemExit(f"intents.winner = {S.winner} but that model was not trained in this run.")
best, T = candidates[S.winner]
proba_t = apply_temperature(best.predict_proba(test.text), T)
res_test = evaluate(test.intent, best.classes_[proba_t.argmax(1)], proba_t.max(1), test.flags)
joblib.dump(best, RESULTS_DIR / "intent_model.joblib")
(RESULTS_DIR / "temperature.txt").write_text(str(T))
summary = {"winner": S.winner, "temperature": T,
           "dev": {"tfidf": res_tfidf, "embeddings": res_emb, "llm_sample": res_llm}, "test": res_test}
(RESULTS_DIR / "stage1_intents.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
print("test", short(res_test))

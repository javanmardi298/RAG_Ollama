# Stage 9 (Colab, GPU): fine-tune a multilingual encoder for intents with LoRA and compare with stage 1.
# The panel's "Colab bundle" button writes results/colab_lora_bundle.zip with this script, the splits and
# lora_config.json (from configs/project.yaml -> lora.*). Upload the zip to Colab, unzip, run this file.
# !pip install -q transformers peft datasets accelerate evaluate
import json, os
import pandas as pd, torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from sklearn.metrics import f1_score
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          Trainer, TrainingArguments)

CFG = json.load(open("lora_config.json")) if os.path.exists("lora_config.json") else {
    "base_model": "xlm-roberta-base", "r": 16, "alpha": 32, "dropout": 0.1, "learning_rate": 5e-4,
    "epochs": 3, "batch_size": 32, "seed": 7}
MODEL = CFG["base_model"]        # multilingual encoder: one model for English and German
train, dev = pd.read_csv("intents_train.csv"), pd.read_csv("intents_dev.csv")
labels = sorted(train.intent.unique()); l2i = {l: i for i, l in enumerate(labels)}
tok = AutoTokenizer.from_pretrained(MODEL)

def to_ds(df):
    ds = Dataset.from_dict({"text": df.text.tolist(), "label": [l2i[l] for l in df.intent]})
    return ds.map(lambda b: tok(b["text"], truncation=True, max_length=64), batched=True)

model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=len(labels))
lora = LoraConfig(task_type=TaskType.SEQ_CLS, r=CFG["r"], lora_alpha=CFG["alpha"], lora_dropout=CFG["dropout"],
                  target_modules=["query", "value"])
model = get_peft_model(model, lora)
model.print_trainable_parameters()      # roughly 1 % of the weights are trained

def metrics(p):
    pred = p.predictions.argmax(-1)
    return {"macro_f1": f1_score(p.label_ids, pred, average="macro"), "accuracy": (pred == p.label_ids).mean()}

args = TrainingArguments("lora-intents", learning_rate=CFG["learning_rate"], per_device_train_batch_size=CFG["batch_size"],
                         num_train_epochs=CFG["epochs"], eval_strategy="epoch", save_strategy="epoch",
                         load_best_model_at_end=True, metric_for_best_model="macro_f1",
                         fp16=torch.cuda.is_available(), report_to=[], seed=CFG["seed"])
trainer = Trainer(model=model, args=args, train_dataset=to_ds(train), eval_dataset=to_ds(dev),
                  data_collator=DataCollatorWithPadding(tok), compute_metrics=metrics)
trainer.train()
res = trainer.evaluate()
print(res)
json.dump({"config": CFG, "dev": res}, open("stage9_lora.json", "w"), indent=2)
print("Download stage9_lora.json and put it in results/ so the panel can compare it with stage 1.")

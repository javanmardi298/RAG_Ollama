# Stage 9 (Colab, GPU): fine-tune xlm-roberta-base for intents with LoRA and compare with stage 1.
# !pip install -q transformers peft datasets accelerate evaluate
# Upload data/processed/intents_{train,dev}.csv first.
import numpy as np, pandas as pd, torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from sklearn.metrics import f1_score
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          Trainer, TrainingArguments)

MODEL = "xlm-roberta-base"        # multilingual encoder: one model for English and German
train, dev = pd.read_csv("intents_train.csv"), pd.read_csv("intents_dev.csv")
labels = sorted(train.intent.unique()); l2i = {l: i for i, l in enumerate(labels)}
tok = AutoTokenizer.from_pretrained(MODEL)

def to_ds(df):
    ds = Dataset.from_dict({"text": df.text.tolist(), "label": [l2i[l] for l in df.intent]})
    return ds.map(lambda b: tok(b["text"], truncation=True, max_length=64), batched=True)

model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=len(labels))
lora = LoraConfig(task_type=TaskType.SEQ_CLS, r=16, lora_alpha=32, lora_dropout=0.1, target_modules=["query", "value"])
model = get_peft_model(model, lora)
model.print_trainable_parameters()      # roughly 1 % of the weights are trained

def metrics(p):
    pred = p.predictions.argmax(-1)
    return {"macro_f1": f1_score(p.label_ids, pred, average="macro"), "accuracy": (pred == p.label_ids).mean()}

args = TrainingArguments("lora-intents", learning_rate=5e-4, per_device_train_batch_size=32, num_train_epochs=3,
                         eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
                         metric_for_best_model="macro_f1", fp16=torch.cuda.is_available(), report_to=[], seed=7)
trainer = Trainer(model=model, args=args, train_dataset=to_ds(train), eval_dataset=to_ds(dev),
                  data_collator=DataCollatorWithPadding(tok), compute_metrics=metrics)
trainer.train()
print(trainer.evaluate())

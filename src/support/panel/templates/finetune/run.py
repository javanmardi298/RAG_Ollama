# Starter: prepare a fine-tuning / distillation run.
#   python run.py            writes results/colab_bundle.zip: train/dev splits + LoRA script + lora_config.json
# Upload the zip to Colab (GPU), unzip, run stage9_lora_colab.py, put stage9_lora.json back into results/.
# Distillation: label unlabelled messages with a big model first (see README, stage 3), then train on those labels.
import os, json, sys, zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
splits = ROOT / "data" / "processed"
missing = [n for n in ("train", "dev") if not (splits / f"intents_{n}.csv").exists()]
if missing:
    raise SystemExit("Run stage 0 of the support agent first (data/processed/intents_*.csv).")
lora = {"base_model": cfg.get("base_model", "xlm-roberta-base"), "r": cfg.get("lora_r", 16), "alpha": cfg.get("lora_alpha", 32),
        "dropout": 0.1, "learning_rate": cfg.get("lr", 5e-4), "epochs": cfg.get("epochs", 3), "batch_size": 32, "seed": 7}
out = HERE / "results" / "colab_bundle.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(ROOT / "scripts" / "stage9_lora_colab.py", "stage9_lora_colab.py")
    for n in ("train", "dev"):
        z.write(splits / f"intents_{n}.csv", f"intents_{n}.csv")
    z.writestr("lora_config.json", json.dumps(lora, indent=2))
print("wrote", out, "with", lora)

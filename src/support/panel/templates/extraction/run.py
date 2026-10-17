# Starter: structured extraction + field-level evaluation.
# data/*.txt are document texts (OCR output or extracted PDF text); eval/gold.jsonl has {"file": ..., "fields": {...}}.
#   python run.py            needs Ollama with the model in config.yaml (llm)
import os, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml
from pydantic import BaseModel, Field, model_validator
from labkit.metrics import extraction_report
from labkit.structured import extract
from support.llm import OllamaLLM

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}


class Invoice(BaseModel):
    """Edit this model for your documents. Validators hold the business rules (code, not the LLM)."""
    vendor: str
    invoice_number: str
    date: str = Field(description="ISO date YYYY-MM-DD")
    net: float
    vat: float
    total: float

    @model_validator(mode="after")
    def amounts_add_up(self):
        if abs(self.net + self.vat - self.total) > 0.02:
            raise ValueError(f"net + vat = {self.net + self.vat:.2f} but total = {self.total:.2f}")
        return self


llm = OllamaLLM(cfg.get("llm", "qwen2.5:7b"), temperature=0)
gold = [json.loads(l) for l in (HERE / "eval" / "gold.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
pairs, review = [], []
for g in gold:
    text = (HERE / "data" / g["file"]).read_text(encoding="utf-8")
    out = extract(llm, Invoice, f"Extract the invoice fields from this document.\n\n{text}",
                  max_repairs=int(cfg.get("max_repairs", 1)))
    pred = out.value.model_dump() if out.ok else {}
    pairs.append((pred, g["fields"]))
    needs_human = (not out.ok) or (out.ok and out.value.total > float(cfg.get("approval_above_eur", 1000)))
    if needs_human:
        review.append({"file": g["file"], "reason": "invalid" if not out.ok else "above approval limit", "errors": out.errors})
    print(g["file"], "ok" if out.ok else "FAILED", f"attempts={out.attempts}", "-> human review" if needs_human else "")
report = extraction_report(pairs)
report["review_queue"] = review
report["straight_through_rate"] = 1 - len(review) / len(gold)
print(json.dumps({k: v for k, v in report.items() if k != "review_queue"}, indent=2))
(HERE / "results" / "extraction.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

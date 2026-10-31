# Starter: retrieval baseline and evaluation. Runs as is on the sample data; then put your documents in data/
# and your labelled questions in eval/questions.csv (question, relevant doc ids separated by |).
#   python run.py            BM25 (and dense + hybrid if sentence-transformers is installed)
import os, csv, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml
from labkit.chunking import chunk_all
from labkit.loaders import load_dir
from labkit.metrics import retrieval_report
from labkit.retrieval import Index

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
k = int(cfg.get("k", 5))
docs = load_dir(HERE / "data")
chunks = chunk_all(docs, cfg.get("chunk_strategy", "recursive"), **({"max_words": cfg["chunk_words"]}
                   if cfg.get("chunk_strategy", "recursive") in ("recursive", "headings") and "chunk_words" in cfg else {}))
print(f"{len(docs)} documents -> {len(chunks)} chunks")

encoder = None
try:
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer(cfg.get("embeddings", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"))
except Exception as e:                       # BM25 still runs; say why dense is missing
    print("dense/hybrid skipped:", type(e).__name__, e)
index = Index(chunks, encoder=encoder, rrf_k=int(cfg.get("rrf_k", 60)))

with (HERE / "eval" / "questions.csv").open(encoding="utf-8") as f:
    questions = [(r["question"], set(r["relevant"].split("|"))) for r in csv.DictReader(f)]

report = {}
for mode in ["bm25"] + (["dense", "hybrid"] if encoder else []):
    runs, misses = [], []
    for q, rel in questions:
        ranked = list(dict.fromkeys(c.doc_id for c in index.search(q, k=k * 3, mode=mode)))
        runs.append((ranked, rel))
        if not set(ranked[:k]) & rel:
            misses.append(q)
    report[mode] = {**retrieval_report(runs, k), "missed": misses}
    print(mode, {m: round(v, 3) for m, v in report[mode].items() if isinstance(v, float)}, f"missed {len(misses)}")
(HERE / "results" / "retrieval.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print("Read the missed questions: synonyms? language? chunk too small? That is your next experiment.")

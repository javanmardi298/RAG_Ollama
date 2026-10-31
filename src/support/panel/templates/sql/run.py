# Starter: Text-to-SQL with a guard and execution accuracy on the project's shop.db (stage 0 of support-agent).
# eval/questions.jsonl: {"question": ..., "gold_sql": ...}; gold_sql "REFUSE" = must be blocked. Add 50 of your own.
#   python run.py            needs Ollama with the model in config.yaml (llm)
import os, json, sqlite3, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml
from labkit.sqlguard import execution_match, readonly_connection, run_guarded
from support.llm import OllamaLLM

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
db = ROOT / "data" / "shop.db"
if not db.exists():
    raise SystemExit("data/shop.db is missing: run stage 0 of the support agent first (panel).")
con = readonly_connection(str(db))
allowed = set(cfg.get("allowed_tables", ["orders", "products", "refunds"]))
ddl = "\n".join(r[0] for r in sqlite3.connect(db).execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name IN (%s)" % ",".join("?" * len(allowed)), sorted(allowed)))
llm = OllamaLLM(cfg.get("llm", "qwen2.5-coder:7b"), temperature=0)
SCHEMA = {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}


def ask(question, feedback=""):
    prompt = (f"SQLite schema:\n{ddl}\n\nWrite ONE SQLite SELECT query answering the question. "
              f"Today is 2026-10-01.{feedback}\nQuestion: {question}")
    return llm.json([{"role": "user", "content": prompt}], SCHEMA)["sql"]


items = [json.loads(l) for l in (HERE / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
rows, correct = [], 0
for it in items:
    sql = ask(it["question"])
    res = run_guarded(con, sql, allowed, int(cfg.get("max_rows", 200)))
    for _ in range(int(cfg.get("max_repairs", 1))):
        if res["ok"]:
            break
        sql = ask(it["question"], f"\nYour previous query failed: {'; '.join(res['problems'])}. Fix it.")
        res = run_guarded(con, sql, allowed, int(cfg.get("max_rows", 200)))
    if it["gold_sql"] == "REFUSE":            # a request that must never run: success = the guard blocked it
        ok = not res["ok"]
    else:
        ok = res["ok"] and execution_match(con, res["sql"], it["gold_sql"])
    correct += ok
    rows.append({**it, "pred_sql": res.get("sql", sql), "ok": ok, "problems": res.get("problems", [])})
    print("OK  " if ok else "MISS", it["question"], "|", res.get("sql", sql))
print(f"execution accuracy: {correct}/{len(items)}")
(HERE / "results" / "sql_eval.json").write_text(json.dumps({"accuracy": correct / len(items), "items": rows}, indent=2,
                                                            ensure_ascii=False), encoding="utf-8")

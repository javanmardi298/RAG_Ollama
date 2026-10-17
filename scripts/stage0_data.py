# Stage 0: data, order database, data summary. Same steps as notebooks/00_setup_data.ipynb, runnable from the panel.
# Parameters: configs/project.yaml -> data.*, project.seed
# %%
import json, os, platform, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import pandas as pd, sklearn
from support import config
from support.data import clean_intents, load_bitext, load_wands_products, split_intents
from support.intents import load_clinc_oos
from support.orders import build_database
from support.settings import settings

S = settings()
config.ensure_dirs()
print("project root:", config.ROOT, "| reference date:", config.reference_date(), "| seed:", config.SEED)

# %% Part A: intent data. Look before you model.
raw = load_bitext(S.data.bitext_csv or None)
counts = raw["intent"].value_counts()
print(raw.shape, f"{raw['intent'].nunique()} intents | rows per intent min {counts.min()} max {counts.max()}")
flag_share = (raw["flags"].fillna("").apply(set).explode().value_counts() / len(raw)).round(3)
print("share of rows per flag (Z typos, Q colloquial, K keywords):", flag_share.to_dict())

known, present = set(config.intent_map()), set(raw["intent"].unique())
missing = sorted(present - known)
print("missing from intents.yaml:", missing or "none")
if missing:
    raise SystemExit("Add the missing intents to configs/intents.yaml before going on (the agent would crash on them).")

# %% Clean, deduplicate, split WITHOUT leakage (grouped by normalized key)
clean, report = clean_intents(raw)
print(json.dumps(report, indent=2))
splits = split_intents(clean, seed=config.SEED)
share = pd.DataFrame({n: p["intent"].value_counts(normalize=True) for n, p in splits.items()}).fillna(0)
max_gap = float((share.max(axis=1) - share.min(axis=1)).max())
for name, part in splits.items():
    part.to_csv(config.PROCESSED_DIR / f"intents_{name}.csv", index=False)
    print(f"{name:>5}: {len(part):>6} rows ({len(part) / len(clean):.0%})")
print(f"largest intent-share gap between splits: {max_gap:.3%}  -> test split is now LOCKED, decide on dev")

# %% Out-of-scope messages (CLINC150), downloaded once
oos = load_clinc_oos(S.data.clinc_json or None)
print("CLINC150 oos:", {k: len(v) for k, v in oos.items()})

# %% Part B: order database (WANDS product names, synthetic orders, 11 boundary cases)
wands = load_wands_products(S.data.wands_dir or os.getenv("WANDS_DIR"))
sizes = build_database(wands, config.DB_PATH, n_customers=S.data.n_customers, n_products=S.data.n_products,
                       n_orders=S.data.n_orders, seed=config.SEED)
con = sqlite3.connect(config.DB_PATH)
by_status = dict(con.execute("SELECT status, COUNT(*) FROM orders GROUP BY status").fetchall())
edge = [r[0] for r in con.execute("SELECT scenario FROM orders WHERE scenario IS NOT NULL ORDER BY order_id")]
con.close()
print(sizes, by_status, f"{len(edge)} boundary orders")

# %% Data summary: every number in the README comes from here
summary = {
    "reference_date": str(config.reference_date()), "seed": config.SEED,
    "bitext": {"rows_raw": len(raw), "intents": int(raw["intent"].nunique()), **report,
               "splits": {n: len(p) for n, p in splits.items()}, "max_intent_share_gap": max_gap,
               "flag_share": flag_share.to_dict()},
    "clinc_oos": {k: len(v) for k, v in oos.items()},
    "database": sizes, "orders_by_status": by_status, "boundary_orders": edge,
    "versions": {"python": platform.python_version(), "pandas": pd.__version__, "sklearn": sklearn.__version__},
}
(config.RESULTS_DIR / "data_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("saved results/data_summary.json. Next: run the tests (pytest -q), then stage 1.")

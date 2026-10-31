"""Read each stage's result files and turn them into a few headline numbers (what the panel and Claude show).

Rule from the project: Automation Rate is never shown without False Automation Rate next to it.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..config import RESULTS_DIR


def _load(name: str):
    path = RESULTS_DIR / name
    if not path.exists():
        return None
    if name.endswith(".jsonl"):
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(path.read_text(encoding="utf-8"))


def _r(x, n=4):
    return round(x, n) if isinstance(x, (int, float)) and not isinstance(x, bool) else x


def _metric(label: str, value, fmt: str = "num", hint: str = "") -> dict:
    return {"label": label, "value": _r(value), "fmt": fmt, "hint": hint}


def stage_results(stage: int) -> dict:
    """{'available': bool, 'metrics': [..], 'details': {...}, 'files': [...]}. Details feed the charts."""
    fn = {0: _s0, 1: _s1, 2: _s2, 3: _s3, 4: _s4, 5: _s5, 6: _s6, 7: _s7, 8: _s8, 9: _s9}[stage]
    try:
        metrics, details = fn()
    except Exception as e:   # a malformed or old-format file must not break the panel
        return {"available": False, "metrics": [], "details": {"error": f"{type(e).__name__}: {e}"}}
    return {"available": bool(metrics), "metrics": metrics, "details": details}


def headline(stage: int) -> dict:
    """Flat {label: value} for the run registry and run comparison; display formats under "_fmt"."""
    metrics = stage_results(stage)["metrics"]
    return {**{m["label"]: m["value"] for m in metrics}, "_fmt": {m["label"]: m["fmt"] for m in metrics}}


def _s0():
    d = _load("data_summary.json")
    if not d:
        return [], {}
    b = d["bitext"]
    return [_metric("intents", b["intents"]), _metric("rows after cleaning", b["rows_out"]),
            _metric("duplicates dropped", b["exact_duplicates_dropped"]),
            _metric("train / dev / test", " / ".join(str(v) for v in b["splits"].values()), "text"),
            _metric("max intent-share gap", b.get("max_intent_share_gap"), "pct"),
            _metric("orders", d["database"]["orders"]),
            _metric("boundary orders", len(d.get("boundary_orders", [])) or None)], d


def _s1():
    d = _load("stage1_intents.json")
    if not d:
        return [], {}
    t = d["test"]
    m = [_metric("winner", d.get("winner", "tfidf"), "text"), _metric("test macro-F1", t["macro_f1"], "num"),
         _metric("test accuracy", t["accuracy"], "pct"), _metric("test ECE (calibrated)", t.get("ece"), "num",
                                                                  "< 0.05 is good")]
    if "oos_recall" in t:
        m.append(_metric("out-of-scope recall", t["oos_recall"], "pct"))
    dev = {k: {kk: _r(vv) for kk, vv in v.items() if isinstance(vv, (int, float))}
           for k, v in d["dev"].items() if v}
    return m, {"dev": dev, "accuracy_by_flag": t.get("accuracy_by_flag")}


def _s2():
    d = _load("stage2_rag.json")
    if not d:
        return [], {}
    s = d["summary"]
    rec = {r["mode"]: next(v for k, v in r.items() if k.startswith("recall@")) for r in s["retrieval"]}
    k = next(k for k in s["retrieval"][0] if k.startswith("recall@"))
    m = [_metric(f"{k} {mode}", v, "pct") for mode, v in rec.items()]
    m += [_metric("answer fact rate", s["answer_fact_rate"], "pct"),
          _metric("citations valid", s["citation_valid_rate"], "pct"),
          _metric("numbers supported", s["numbers_supported_rate"], "pct"),
          _metric("unanswerable refused", s["unanswerable_refused_rate"], "pct")]
    return m, {"recall": rec, "k": k, "missed": s.get("missed_questions", []), "mode": s.get("mode")}


def _s3():
    d = _load("stage3_smoke.json")
    if not d:
        return [], {}
    return [_metric("smoke turns", len(d["turns"])), _metric("actions written", len(d["actions"])),
            _metric("handed off", d["closed"], "bool")], d


def _s4():
    d = _load("stage4_thresholds.json")
    if not d:
        t = _load("thresholds.json")
        return ([_metric(f"threshold {k}", v) for k, v in t.items()], {}) if t else ([], {})
    m = [_metric(f"threshold {k}", v["threshold"]) for k, v in d["chosen"].items()]
    m += [_metric("dev automation rate", d["dev_automation_rate"], "pct"),
          _metric("dev error among automated", d["dev_error_among_automated"], "pct")]
    return m, {"curve": d.get("curve", []), "chosen": d["chosen"], "budgets": d["budgets"], "cost_based": d.get("cost_based")}


def _s5():
    d = _load("stage5_redteam.json")
    if not d:
        return [], {}
    s = d["summary"]
    return [_metric("attacks caught", s["input_catch_rate"], "pct"), _metric("bad answers caught", s["output_catch_rate"], "pct"),
            _metric("cases", s["n_inputs"] + s["n_outputs"])], {"missed": s["missed"], "inputs": d["inputs"],
                                                                  "outputs": d["outputs"]}


def _s6():
    d = _load("stage6_summary.json")
    if not d:
        return [], {}
    ci = d.get("task_success_ci95") or (None, None)
    m = [_metric("scenarios", d["n"]), _metric("task success", d["task_success"], "pct",
                                               f"95% CI {ci[0]:.0%}–{ci[1]:.0%}" if ci[0] is not None else ""),
         _metric("automation rate", d["automation_rate"], "pct"),
         _metric("false automation rate", d["false_automation_rate"], "pct"),
         _metric("policy violations", d["policy_violation_rate"], "pct"),
         _metric("unnecessary handoffs", d["unnecessary_handoff_rate"], "pct")]
    rel = d.get("reliability") or {}
    if rel:
        k = rel.get("trials", 1)
        m.append(_metric(f"pass^{k} (all {k} runs succeed)", rel.get(f"pass^{k}"), "pct", "reliability, tau-bench style"))
    j = _load("stage6_judge.json")
    if j:
        m.append(_metric("judge kappa", j["kappa"], "num", ">= 0.6 before trusting the judge"))
    return m, {"summary": d, "judge": j}


def _s7():
    d = _load("stage7_robustness.json")
    if not d:
        return [], {}
    curve = d["noise_curve"]
    m = [_metric(f"accuracy noise {c['level']}", c["accuracy"], "pct") for c in curve]
    if d.get("german"):
        m.append(_metric("German accuracy", d["german"]["accuracy"], "pct"))
    m.append(_metric("German status", d.get("german_status", ""), "text"))
    return m, {"curve": curve}


def _s8():
    mon, lt = _load("stage8_monitor.json"), _load("stage8_loadtest.json")
    m, det = [], {}
    if lt:
        m += [_metric("load p95 ms", lt["p95_ms"], "num"), _metric("throughput rps", lt["throughput_rps"]),
              _metric("load errors", lt["errors"])]
        det["loadtest"] = lt
    if mon:
        m += [_metric("traces", mon["n_traces"]), _metric("trace p95 ms", mon["latency"]["p95_ms"])]
        if mon.get("drift"):
            m += [_metric("intent PSI", mon["drift"]["psi"]), _metric("drift alert", mon["drift"]["alert"], "bool")]
        det["monitor"] = mon
    return m, det


def _s9():
    d, lora = _load("stage9_ab.json"), _load("stage9_lora.json")
    m, det = [], {}
    if d:
        m += [_metric("needed per arm", d["n_needed_per_arm"]), _metric("SRM mismatch", d["srm"]["mismatch"], "bool"),
              _metric("primary diff", d["primary"]["diff"], "pct"), _metric("primary p-value", d["primary"]["p_value"]),
              _metric("ship", d["ship"], "bool")]
        det["ab"] = d
    if lora:
        m.append(_metric("LoRA dev macro-F1", lora["dev"].get("eval_macro_f1"), "num"))
        det["lora"] = lora
    return m, det


def files_status() -> list[dict]:
    out = []
    for p in sorted(RESULTS_DIR.glob("*")):
        if p.is_file() and p.name not in {"panel.db", "panel.db-wal", "panel.db-shm", ".gitkeep"}:
            out.append({"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime})
    return out


def result_file(name: str) -> Path | None:
    """Only plain files directly inside results/ (no path tricks)."""
    p = (RESULTS_DIR / name).resolve()
    return p if p.parent == RESULTS_DIR.resolve() and p.is_file() else None

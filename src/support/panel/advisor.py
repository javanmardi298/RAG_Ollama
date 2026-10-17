"""Reminders and suggestions, decided by code from the project's state (no LLM involved).

Each rule looks at settings, preflight checks, result files and the run history, and returns advice items:
{level: error|warn|info, stage, title, text, action}. The same list is shown in the panel and given to Claude.
"""
from __future__ import annotations

from ..config import CONFIG_DIR, RESULTS_DIR
from ..settings import load
from . import registry
from .catalog import JOB_AD, STAGES
from .results import stage_results


def _item(level, stage, title, text, action=None):
    return {"level": level, "stage": stage, "title": title, "text": text, "action": action}


def _mtime(name: str) -> float | None:
    p = RESULTS_DIR / name
    return p.stat().st_mtime if p.exists() else None


def _settings_drift(s) -> list[dict]:
    """Parameters changed since the last successful run of a stage -> its results are out of date."""
    out = []
    current = s.model_dump(mode="json")
    for st in STAGES:
        runs = [r for r in registry.list_runs(stage=st.id, limit=20) if r["status"] == "succeeded" and r["kind"] == "batch"
                and not r["task"].startswith("tests")]
        if not runs or not st.settings:
            continue
        old = runs[0]["settings"]
        changed = [f"{sec}.{k}: {old.get(sec, {}).get(k)} → {v}" for sec in st.settings
                   for k, v in current.get(sec, {}).items() if old.get(sec, {}).get(k) != v]
        if changed:
            out.append(_item("warn", st.id, f"نتایج مرحله‌ی {st.id} قدیمی است",
                             "از آخرین اجرا این پارامترها عوض شده‌اند: " + "، ".join(changed[:6]) +
                             ". دوباره اجرا کن تا نتیجه با تنظیمات فعلی بخواند.",
                             {"type": "run", "task": runs[0]["task"]}))
    return out


def advice(checks: list[dict] | None = None) -> list[dict]:
    from .preflight import run_all
    s = load()
    checks = checks if checks is not None else run_all()
    c = {x["id"]: x for x in checks}
    res = {i: stage_results(i) for i in range(10)}
    items: list[dict] = []

    # --- environment ---
    for cid in ("python", "pkg_core", "ollama", "ollama_model", "disk"):
        if cid in c and not c[cid]["ok"] and c[cid]["level"] == "error":
            items.append(_item("error", None, c[cid]["label"], f"{c[cid]['detail']}. راه‌حل: {c[cid]['fix']}",
                               {"type": "page", "page": "setup"}))
    if "venv" in c and not c["venv"]["ok"]:
        items.append(_item("warn", None, "خارج از محیط مجازی", "پکیج‌ها در Python سیستم نصب می‌شوند و با پروژه‌های دیگر قاطی می‌شوند. "
                           + c["venv"]["fix"], {"type": "page", "page": "setup"}))

    # --- order of stages ---
    if not c.get("data_splits", {}).get("ok"):
        items.append(_item("warn", 0, "مرحله‌ی ۰ هنوز اجرا نشده", "همه‌ی مرحله‌ها به داده و shop.db نیاز دارند. از اینجا شروع کن.",
                           {"type": "run", "task": "stage0_data"}))
    elif not c.get("intent_model", {}).get("ok"):
        items.append(_item("info", 1, "قدم بعدی: مرحله‌ی ۱", "داده آماده است؛ مدل intent را بساز (agent بدون آن کار نمی‌کند).",
                           {"type": "run", "task": "stage1_intents"}))
    if res[0]["available"] and registry.count_runs("tests_all") == 0:
        items.append(_item("info", 0, "تست‌ها را اجرا کن", "۶۶+ تست بدون مدل و داده اجرا می‌شوند و منطق قطعی را تضمین می‌کنند.",
                           {"type": "run", "task": "tests_all"}))
    last_tests = registry.list_runs(task="tests_all", limit=1)
    if last_tests and last_tests[0]["status"] == "failed":
        items.append(_item("error", 0, "تست‌ها شکست خورده‌اند", f"اجرای #{last_tests[0]['run_id']} را بخوان و قبل از ادامه درستش کن.",
                           {"type": "run_log", "run_id": last_tests[0]["run_id"]}))
    policy_mtime = (CONFIG_DIR / "policy_rules.yaml").stat().st_mtime
    if last_tests and policy_mtime > last_tests[0]["started_at"]:
        items.append(_item("warn", 0, "policy_rules.yaml بعد از آخرین تست تغییر کرده",
                           "متن‌های EN/DE هم باید همان عددها را داشته باشند؛ test_policy_sync را با اجرای همه‌ی تست‌ها چک کن.",
                           {"type": "run", "task": "tests_all"}))

    items += _settings_drift(s)

    # --- stage 1 ---
    if res[1]["available"]:
        n = registry.count_runs("stage1_intents")
        if n >= 4:
            items.append(_item("warn", 1, f"test {n} بار گزارش شده",
                               "هر اجرای مرحله‌ی ۱ test را هم گزارش می‌کند. اگر بعد از دیدن test چیزی را عوض کرده‌ای، روی test tune کرده‌ای. "
                               "تصمیم‌ها را فقط روی dev بگیر و عدد test آخر را گزارش کن."))
        dev = res[1]["details"].get("dev", {})
        ece = next((m["value"] for m in res[1]["metrics"] if m["label"].startswith("test ECE")), None)
        if ece is not None and ece > 0.05:
            items.append(_item("warn", 1, "calibration ضعیف", f"ECE روی test {ece:.3f} است (> 0.05). آستانه‌های مرحله‌ی ۴ به اطمینان صادق نیاز دارند."))
        if dev.get("embeddings") and dev.get("tfidf") and s.intents.winner == "tfidf" and \
                dev["embeddings"].get("macro_f1", 0) > dev["tfidf"].get("macro_f1", 0) + 0.01:
            items.append(_item("info", 1, "embedding روی dev بهتر بوده",
                               "macro-F1 embedding از TF-IDF بیشتر است. اگر سرعت قابل‌قبول است، intents.winner را embeddings کن (به‌خصوص برای آلمانی).",
                               {"type": "setting", "key": "intents.winner"}))
        if not dev.get("llm_sample") and s.intents.run_llm is False:
            items.append(_item("info", 1, "مقایسه با LLM انجام نشده", "برای کامل بودن مقایسه، intents.run_llm را یک بار روشن کن."))

    # --- stage 2 ---
    if res[2]["available"]:
        rec, mode = res[2]["details"]["recall"], res[2]["details"].get("mode", s.rag.mode)
        best = max(rec, key=rec.get)
        if rec.get(mode, 0) < rec[best] - 0.02:
            items.append(_item("warn", 2, f"rag.mode = {mode} بهترین نیست",
                               f"روی سؤال‌ها {best} بهتر بود ({rec[best]:.0%} در برابر {rec.get(mode, 0):.0%}).",
                               {"type": "setting", "key": "rag.mode"}))
        if res[2]["details"].get("missed"):
            items.append(_item("info", 2, f"{len(res[2]['details']['missed'])} سؤال پیدا نشد",
                               "سؤال‌های از دست رفته را بخوان: مترادف؟ زبان؟ chunk بد؟ " + " | ".join(res[2]["details"]["missed"][:3])))
    elif c.get("data_splits", {}).get("ok"):
        items.append(_item("info", 2, "RAG هنوز ارزیابی نشده", "مرحله‌ی ۲ به مرحله‌ی ۱ وابسته نیست؛ می‌توانی موازی جلو بروی.",
                           {"type": "run", "task": "stage2_rag"}))

    # --- stage 4 ---
    if res[1]["available"] and not (RESULTS_DIR / "thresholds.json").exists():
        items.append(_item("warn", 4, "آستانه‌ها تنظیم نشده‌اند", "agent با آستانه‌های پیش‌فرض (0.5/0.7/0.85) کار می‌کند. مرحله‌ی ۴ را اجرا کن.",
                           {"type": "run", "task": "stage4_thresholds"}))
    if not s.decision.use_tuned_thresholds:
        items.append(_item("warn", 4, "آستانه‌های مرحله‌ی ۴ استفاده نمی‌شوند", "decision.use_tuned_thresholds خاموش است.",
                           {"type": "setting", "key": "decision.use_tuned_thresholds"}))
    t_thr, t_model = _mtime("thresholds.json"), _mtime("intent_model.joblib")
    if t_thr and t_model and t_model > t_thr:
        items.append(_item("warn", 4, "مدل intent بعد از آستانه‌ها عوض شده", "آستانه‌ها برای مدل قبلی انتخاب شده‌اند؛ مرحله‌ی ۴ را دوباره اجرا کن.",
                           {"type": "run", "task": "stage4_thresholds"}))

    # --- stage 5 ---
    if res[5]["available"] and res[5]["details"]["missed"]:
        items.append(_item("info", 5, f"{len(res[5]['details']['missed'])} حمله رد شد",
                           "guardrail را در src/support/guardrails.py اصلاح کن، دوباره اجرا کن، و تست‌ها را اجرا کن: "
                           + " | ".join(res[5]["details"]["missed"][:2])))
    elif not res[5]["available"]:
        items.append(_item("info", 5, "red-team اجرا نشده", "یک دقیقه طول می‌کشد و به مدل نیاز ندارد.", {"type": "run", "task": "stage5_redteam"}))

    # --- stage 6 ---
    if res[6]["available"]:
        summ = res[6]["details"]["summary"]
        lo, hi = summ.get("task_success_ci95", (0, 0))
        if hi - lo > 0.2:
            items.append(_item("info", 6, "فاصله‌ی اطمینان پهن است", f"task success بین {lo:.0%} و {hi:.0%}؛ با {summ['n']} سناریو. "
                               "برای عدد قابل‌گزارش evaluation.n_run را بیشتر کن (مثلاً ۸۰).", {"type": "setting", "key": "evaluation.n_run"}))
        if summ.get("same_model_both_sides"):
            items.append(_item("info", 6, "یک مدل در دو طرف گفتگو", "مدل مشتری شبیه‌سازی‌شده را با مدل agent متفاوت کن تا آزمون سخت‌تر و صادق‌تر شود.",
                               {"type": "setting", "key": "llm.user_sim_model"}))
        if not summ.get("thresholds"):
            items.append(_item("warn", 6, "ارزیابی با آستانه‌های پیش‌فرض اجرا شده", "بعد از مرحله‌ی ۴ دوباره اجرا کن تا عدد نهایی واقعی باشد."))
        judge = res[6]["details"].get("judge")
        if not judge:
            items.append(_item("warn", 6, "LLM judge اعتبارسنجی نشده", "قبل از استفاده از قاضی LLM، توافقش را با برچسب‌های خودت بسنج.",
                               {"type": "run", "task": "stage6_judge"}))
        elif judge["kappa"] < 0.6:
            items.append(_item("warn", 6, f"توافق judge کم است (kappa {judge['kappa']:.2f})",
                               "prompt قاضی را بهتر کن یا مدل قوی‌تری بگذار؛ اختلاف‌ها را بخوان."))
    t6, t_thr = _mtime("stage6_summary.json"), _mtime("thresholds.json")
    if t6 and t_thr and t_thr > t6:
        items.append(_item("warn", 6, "آستانه‌ها بعد از ارزیابی عوض شده‌اند", "عدد مرحله‌ی ۶ با آستانه‌های قبلی است؛ دوباره اجرا کن.",
                           {"type": "run", "task": "stage6_eval"}))

    # --- stage 7 ---
    if res[7]["available"] and res[7]["details"] is not None:
        status = next((m["value"] for m in res[7]["metrics"] if m["label"] == "German status"), "")
        if status == "waiting for review":
            items.append(_item("warn", 7, "ترجمه‌ی آلمانی منتظر بازبینی توست",
                               "data/processed/intents_test_de_TO_REVIEW.csv را بازبینی کن و با نام intents_test_de.csv ذخیره کن، بعد دوباره اجرا کن."))

    # --- stage 8 ---
    if res[8]["available"]:
        lt = res[8]["details"].get("loadtest")
        if lt and lt["p95_ms"] > s.serving.p95_target_ms:
            items.append(_item("warn", 8, "p95 بالاتر از هدف", f"{lt['p95_ms']:.0f} ms در برابر هدف {s.serving.p95_target_ms} ms. "
                               "مدل کوچک‌تر، کش جواب‌های RAG، یا کاربر هم‌زمان کمتر روی Ollama محلی."))
        mon = res[8]["details"].get("monitor")
        if mon and mon.get("drift") and mon["drift"]["alert"]:
            items.append(_item("error", 8, "هشدار drift", "توزیع intent یا نرخ ارجاع تغییر کرده؛ biggest_changes را در نتیجه‌ی پایش ببین."))

    # --- stage 9 ---
    if res[9]["available"]:
        ab = res[9]["details"].get("ab")
        if ab and ab["srm"]["mismatch"]:
            items.append(_item("error", 9, "SRM: تخصیص خراب است", "نتیجه‌ی A/B را نخوان؛ اول دلیل عدم توازن بازوها را پیدا کن."))
        if ab and ab.get("underpowered"):
            items.append(_item("warn", 9, "آزمایش کم‌توان", f"کمتر از {ab['n_needed_per_arm']} گفتگو در هر بازو؛ نتیجه‌ی غیرمعنادار چیزی نمی‌گوید."))
        if not res[9]["details"].get("lora"):
            items.append(_item("info", 9, "LoRA هنوز اجرا نشده", "«ساخت بسته‌ی Colab» را بزن و نتیجه را در results/stage9_lora.json بگذار.",
                               {"type": "colab_bundle"}))

    # --- reproducibility & connections ---
    if c.get("git") and c["git"]["detail"].endswith("commit‌نشده"):
        items.append(_item("info", None, "تغییرات commit‌نشده", "هر اجرا commit را ثبت می‌کند؛ با تغییرات commit‌نشده، نتیجه به کد دقیق برنمی‌گردد."))
    seeds = {r["settings"].get("project", {}).get("seed") for r in registry.list_runs(limit=30)}
    if len(seeds - {None}) > 1:
        items.append(_item("info", None, "اجراها با seedهای مختلف", "نتایج با seed متفاوت مستقیماً قابل‌مقایسه نیستند."))
    if not c.get("anthropic_key", {}).get("ok") and not c.get("claude_desktop", {}).get("ok"):
        items.append(_item("info", None, "Claude هنوز وصل نیست", "یا کلید API را در «اتصال‌ها» بگذار، یا پنل را در Claude Desktop نصب کن.",
                           {"type": "page", "page": "setup"}))

    for job_id, text in JOB_AD.items():
        if not any(res[st.id]["available"] for st in STAGES if job_id in st.job_ad):
            items.append(_item("info", None, f"بند آگهی بدون مدرک: {text}",
                               "هنوز هیچ نتیجه‌ای برای این بند نداری؛ برای رزومه حداقل یک عدد لازم است.", {"type": "page", "page": "coverage"}))

    order = {"error": 0, "warn": 1, "info": 2}
    return sorted(items, key=lambda x: (order[x["level"]], x["stage"] if x["stage"] is not None else -1))


def coverage() -> list[dict]:
    """For each job-ad requirement: which stages provide evidence and their headline numbers."""
    res = {i: stage_results(i) for i in range(10)}
    out = []
    for job_id, text in JOB_AD.items():
        stages = [st for st in STAGES if job_id in st.job_ad]
        evidence = [{"stage": st.id, "title": st.title, "metrics": res[st.id]["metrics"]}
                    for st in stages if res[st.id]["available"]]
        out.append({"id": job_id, "text": text, "stages": [st.id for st in stages], "evidence": evidence,
                    "covered": bool(evidence)})
    return out


def stage_status(stage_id: int) -> str:
    """done | running | stale | todo (for the sidebar)."""
    active = [r for r in registry.active_runs() if r["stage"] == stage_id]
    if active:
        return "running"
    if not stage_results(stage_id)["available"]:
        return "todo"
    return "done"

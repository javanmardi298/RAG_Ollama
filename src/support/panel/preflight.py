"""Checks that tell a beginner what is missing BEFORE a 20-minute run fails on minute 19.

Each check: id, label, ok, level (error = blocks the tasks that need it, warn, info), detail, fix.
Fixes are written for Windows PowerShell first, because that is where the project is run.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import time
import urllib.request

from ..config import DB_PATH, PROCESSED_DIR, RAW_DIR, RESULTS_DIR, ROOT
from ..settings import load
from . import envfile, registry

PACKAGES = {
    "pkg_core": ("پکیج‌های اصلی", ["pandas", "numpy", "scipy", "sklearn", "yaml", "joblib", "pydantic", "matplotlib"],
                 "pip install -r requirements.txt"),
    "pkg_embed": ("sentence-transformers (embedding)", ["sentence_transformers"], "pip install sentence-transformers"),
    "pkg_ollama": ("کلاینت Ollama برای Python", ["ollama"], "pip install ollama"),
    "pkg_data": ("datasets (دانلود Bitext)", ["datasets"], "pip install datasets"),
    "pkg_lc": ("LangChain / LangGraph", ["langchain", "langgraph", "langchain_ollama", "langchain_community",
                                         "langchain_huggingface", "langgraph.checkpoint.sqlite"],
               "pip install -r requirements-lc.txt"),
    "pkg_serve": ("FastAPI / uvicorn / httpx", ["fastapi", "uvicorn", "httpx"], "pip install -r requirements-serve.txt httpx"),
    "pkg_panel": ("پکیج‌های پنل (mcp، anthropic، psutil)", ["fastapi", "uvicorn", "mcp", "anthropic", "psutil"],
                  "pip install -r requirements-panel.txt"),
}

_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str, ttl: float, fn):
    now = time.time()
    if key in _cache and now - _cache[key][0] < ttl:
        return _cache[key][1]
    value = fn()
    _cache[key] = (now, value)
    return value


def _has(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def ollama_models(host: str) -> list[str] | None:
    """Names of pulled models, or None when the server does not answer."""
    def ask():
        try:
            with urllib.request.urlopen(host.rstrip("/") + "/api/tags", timeout=2) as r:
                return [m["name"] for m in json.load(r).get("models", [])]
        except Exception:
            return None
    return _cached(f"ollama:{host}", 5, ask)


def _model_pulled(name: str, pulled: list[str]) -> bool:
    return name in pulled or (":" not in name and f"{name}:latest" in pulled)


def _check(id, label, ok, detail="", fix="", level="error"):
    return {"id": id, "label": label, "ok": bool(ok), "level": "ok" if ok else level, "detail": detail, "fix": fix}


def run_all() -> list[dict]:
    s = load()
    checks = []
    v = sys.version_info
    checks.append(_check("python", "Python ≥ 3.10", v >= (3, 10), f"{sys.version.split()[0]} در {sys.executable}",
                         "Python 3.11 را از python.org نصب کن و تیک «Add to PATH» را بزن."))
    in_venv = sys.prefix != sys.base_prefix
    checks.append(_check("venv", "محیط مجازی (.venv)", in_venv, sys.prefix,
                         "windows\\setup.ps1 را اجرا کن؛ یا: py -3.11 -m venv .venv ; .venv\\Scripts\\Activate.ps1",
                         level="warn"))
    for cid, (label, mods, fix) in PACKAGES.items():
        missing = [m for m in mods if not _has(m)]
        level = "error" if cid in ("pkg_core",) else "warn"
        checks.append(_check(cid, label, not missing, "کم است: " + ", ".join(missing) if missing else "نصب است", fix, level))

    pulled = ollama_models(s.llm.host)
    checks.append(_check("ollama", "سرور Ollama", pulled is not None,
                         f"{s.llm.host} — {len(pulled)} مدل" if pulled is not None else f"{s.llm.host} جواب نمی‌دهد",
                         "Ollama را از ollama.com نصب و اجرا کن (آیکون در system tray). آدرس: تنظیمات ← llm.host"))
    for cid, label, model in [("ollama_model", "مدل agent در Ollama", s.llm.chat_model),
                              ("ollama_user_model", "مدل مشتری شبیه‌سازی‌شده", s.llm.user_sim_model)]:
        ok = pulled is not None and _model_pulled(model, pulled)
        checks.append(_check(cid, label, ok, model, f"ollama pull {model}", "error" if cid == "ollama_model" else "warn"))

    raw = {"Bitext": RAW_DIR / "bitext.csv", "CLINC150": RAW_DIR / "clinc_data_full.json",
           "WANDS": RAW_DIR / "wands_product.csv"}
    present = {k: p.exists() for k, p in raw.items()}
    if s.data.wands_dir:
        present["WANDS"] = present["WANDS"] or os.path.exists(os.path.join(s.data.wands_dir, "product.csv"))
    checks.append(_check("data_raw", "داده‌ی خام (دانلود)", all(present.values()),
                         " · ".join(f"{k} {'✓' if v else '✗'}" for k, v in present.items()),
                         "مرحله‌ی ۰ را اجرا کن؛ بار اول دانلود می‌کند (اینترنت لازم است).", "warn"))
    splits = all((PROCESSED_DIR / f"intents_{n}.csv").exists() for n in ("train", "dev", "test"))
    checks.append(_check("data_splits", "تقسیم train/dev/test", splits, str(PROCESSED_DIR), "مرحله‌ی ۰ را اجرا کن."))
    checks.append(_check("db", "دیتابیس سفارش‌ها (shop.db)", DB_PATH.exists(), str(DB_PATH), "مرحله‌ی ۰ را اجرا کن."))
    checks.append(_check("intent_model", "مدل intent (مرحله‌ی ۱)", (RESULTS_DIR / "intent_model.joblib").exists(),
                         "results/intent_model.joblib", "مرحله‌ی ۱ را اجرا کن."))
    checks.append(_check("thresholds", "آستانه‌های تنظیم‌شده (مرحله‌ی ۴)", (RESULTS_DIR / "thresholds.json").exists(),
                         "results/thresholds.json", "مرحله‌ی ۴ را اجرا کن؛ تا آن موقع agent آستانه‌های پیش‌فرض دارد.", "info"))
    checks.append(_check("stage6_runs", "گفتگوهای ارزیابی (مرحله‌ی ۶)", (RESULTS_DIR / "stage6_runs.jsonl").exists(),
                         "results/stage6_runs.jsonl", "مرحله‌ی ۶ را اجرا کن.", "info"))

    free_gb = shutil.disk_usage(ROOT).free / 1e9
    checks.append(_check("disk", "فضای دیسک آزاد", free_gb >= 2, f"{free_gb:.1f} GB",
                         "حداقل ۲ GB (مدل‌های Ollama ~۵ GB جداگانه). فایل‌های بزرگ را پاک کن.",
                         "error" if free_gb < 1 else "warn"))
    gpu = shutil.which("nvidia-smi") is not None
    checks.append(_check("gpu", "GPU (NVIDIA)", gpu, "پیدا شد" if gpu else "پیدا نشد؛ CPU کار می‌کند ولی embedding کندتر است",
                         "اختیاری: embedding و LoRA را در Colab اجرا کن.", "info"))
    commit, dirty = registry.git_state()
    checks.append(_check("git", "git و commit تمیز", commit is not None and not dirty,
                         f"commit {commit}" + (" — تغییرات commit‌نشده" if dirty else "") if commit else "git پیدا نشد",
                         "قبل از اجرای گزارش‌دادنی commit کن تا نتیجه به کد دقیق برگردد.", "info"))
    key = envfile.get("ANTHROPIC_API_KEY")
    checks.append(_check("anthropic_key", "کلید Claude API", bool(key), envfile.mask(key) if key else "تنظیم نشده",
                         "صفحه‌ی «اتصال‌ها» ← کلید API (در .env ذخیره می‌شود). برای چت مستقیم با Claude لازم است.", "info"))
    from .claude_desktop import status as cd_status
    cd = cd_status()
    checks.append(_check("claude_desktop", "اتصال Claude Desktop (MCP)", cd["installed"],
                         cd["detail"], "صفحه‌ی «اتصال‌ها» ← «نصب در Claude Desktop»، بعد Claude Desktop را کامل ببند و باز کن.",
                         "info"))
    return checks


def failing(ids: list[str]) -> list[dict]:
    by_id = {c["id"]: c for c in run_all()}
    return [by_id[i] for i in ids if i in by_id and not by_id[i]["ok"] and by_id[i]["level"] in ("error", "warn")]

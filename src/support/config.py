"""Paths and config loading, shared by every notebook and module."""
from __future__ import annotations

import os
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(os.getenv("SUPPORT_ROOT", Path(__file__).resolve().parents[2]))
CONFIG_DIR = ROOT / "configs"
POLICY_DIR = ROOT / "policies"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = ROOT / "results"
DB_PATH = DATA_DIR / "shop.db"

SEED = 7


@lru_cache
def rules() -> dict:
    return yaml.safe_load((CONFIG_DIR / "policy_rules.yaml").read_text(encoding="utf-8"))


@lru_cache
def intent_map() -> dict[str, dict]:
    return yaml.safe_load((CONFIG_DIR / "intents.yaml").read_text(encoding="utf-8"))["intents"]


def reference_date() -> date:
    """The simulated 'today'. Never use date.today() in this project."""
    return date.fromisoformat(rules()["reference_date"])


def ensure_dirs() -> None:
    for d in (RAW_DIR, PROCESSED_DIR, RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)

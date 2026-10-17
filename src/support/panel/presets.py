"""Project presets (presets/projects/*.yaml), building blocks (presets/components.yaml) and settings presets
(presets/settings/*.yaml): loading with validation, learning progress, and project scaffolding.

python -m support.panel.presets check            validate every preset file
python -m support.panel.presets export out.json  everything as one JSON
python -m support.panel.presets html out.html    the online roadmap artifact (roadmap_template.html + this data)
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from contextlib import closing
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..config import ROOT

PRESET_DIR = ROOT / "presets"
PROJECTS_DIR = ROOT / "projects"
TEMPLATES = Path(__file__).parent / "templates"
LEVELS = {1: "پایه", 2: "میانی", 3: "پیشرفته"}
TRACKS = {"rag": "RAG و بازیابی", "agent": "Agent", "workflow": "Workflow", "eval": "ارزیابی", "ml": "یادگیری ماشین",
          "production": "Production", "world_models": "JEPA و World Model"}
STATUS = {"ready": "در سیستم", "labkit": "اضافه‌شده در labkit", "external": "ابزار بیرونی"}

# Which starter template a scaffolded project gets.
TEMPLATE_FOR = {"p01_faq_search": "rag", "p02_product_search": "rag", "p03_document_qa": "rag", "p09_multilingual_rag": "rag",
                "p05_invoice_extraction": "extraction", "p06_text_to_sql": "sql", "p07_email_triage_workflow": "workflow",
                "p12_multi_agent_claims": "workflow", "p10_research_agent": "agent", "p11_code_assistant": "agent",
                "p13_graphrag": "graph", "p14_llmops_platform": "ops", "p15_finetune_distill": "finetune",
                "p16_llm_security": "redteam",
                "p17_jepa_basics": "jepa", "p18_collapse_sigreg": "jepa", "p19_world_model_planning": "world_model",
                "p20_surprise_monitoring": "world_model", "p21_vjepa2_video": "vjepa2",
                "p22_agentic_rag": "agentic_rag", "p23_contextual_multimodal_rag": "rag",
                "p24_agent_reliability": "reliability", "p25_prompt_optimization": "optimize",
                "p26_mcp_a2a": "mcp", "p27_context_engineering": "context", "p28_secure_agent": "capsec",
                "p29_agentic_rl": "finetune", "p30_agent_skills": "skills"}


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Component(_M):
    name: str
    category: str
    status: str
    where: str

    @field_validator("status")
    @classmethod
    def _status(cls, v):
        if v not in STATUS:
            raise ValueError(f"status must be one of {list(STATUS)}")
        return v


class DataSource(_M):
    name: str
    url: str = ""
    license: str = ""
    note: str = ""


class PStage(_M):
    title: str
    learn: list[str]
    build: list[str]
    measure: str
    pitfall: str


class Implemented(_M):
    project: str
    stages: list[int]


class Project(_M):
    id: str
    order: int
    level: int = Field(ge=1, le=3)
    title: str
    title_en: str
    tracks: list[str]
    weeks: str
    real_world: str
    problem: str
    goal: str
    prerequisites: list[str] = []
    data: list[DataSource]
    stack: dict
    components: list[str]
    stages: list[PStage]
    metrics: list[str]
    params: dict
    guardrails: list[str]
    production: list[str]
    interview: list[str]
    advanced: list[str]
    cv: str
    implemented: Implemented | None = None

    @field_validator("tracks")
    @classmethod
    def _tracks(cls, v):
        bad = set(v) - set(TRACKS)
        if bad:
            raise ValueError(f"unknown tracks {bad}")
        return v


class SettingsPreset(_M):
    id: str
    title: str
    description: str
    changes: dict


@lru_cache
def components() -> dict[str, Component]:
    data = yaml.safe_load((PRESET_DIR / "components.yaml").read_text(encoding="utf-8"))["components"]
    return {k: Component.model_validate(v) for k, v in data.items()}


@lru_cache
def projects() -> dict[str, Project]:
    out = {}
    for path in sorted((PRESET_DIR / "projects").glob("*.yaml")):
        p = Project.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        if p.id != path.stem:
            raise ValueError(f"{path.name}: id '{p.id}' must equal the file name")
        out[p.id] = p
    comps = components()
    for p in out.values():
        missing = [c for c in p.components if c not in comps]
        if missing:
            raise ValueError(f"{p.id}: unknown components {missing}")
        unknown = [q for q in p.prerequisites if q not in out]
        if unknown:
            raise ValueError(f"{p.id}: unknown prerequisites {unknown}")
    return dict(sorted(out.items(), key=lambda kv: kv[1].order))


@lru_cache
def settings_presets() -> dict[str, SettingsPreset]:
    return {p.stem: SettingsPreset.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
            for p in sorted((PRESET_DIR / "settings").glob("*.yaml"))}


# ---------- progress (stored with the run history) ----------

def _con():
    from . import registry
    con = registry.connect()
    con.execute("CREATE TABLE IF NOT EXISTS preset_progress (preset TEXT, stage INTEGER, done INTEGER, ts REAL, "
                "PRIMARY KEY (preset, stage))")
    return con


def progress() -> dict[str, list[int]]:
    with closing(_con()) as con:
        rows = con.execute("SELECT preset, stage FROM preset_progress WHERE done = 1").fetchall()
    out: dict[str, list[int]] = {}
    for preset, stage in rows:
        out.setdefault(preset, []).append(stage)
    return out


def set_progress(preset_id: str, stage: int, done: bool) -> dict:
    p = projects()[preset_id]
    if not 0 <= stage < len(p.stages):
        raise ValueError(f"{preset_id} has stages 0..{len(p.stages) - 1}")
    with closing(_con()) as con, con:
        con.execute("INSERT OR REPLACE INTO preset_progress VALUES (?, ?, ?, ?)", (preset_id, stage, int(done), time.time()))
    done_list = progress().get(preset_id, [])
    return {"preset": preset_id, "done": sorted(done_list), "total": len(p.stages)}


# ---------- views ----------

def summary(p: Project, prog: dict[str, list[int]] | None = None) -> dict:
    comps = components()
    by_status = {s: [c for c in p.components if comps[c].status == s] for s in STATUS}
    done = (prog or {}).get(p.id, [])
    return {"id": p.id, "order": p.order, "level": p.level, "level_name": LEVELS[p.level], "title": p.title,
            "title_en": p.title_en, "tracks": p.tracks, "weeks": p.weeks, "stages": len(p.stages),
            "done": len(done), "prerequisites": p.prerequisites, "implemented": bool(p.implemented),
            "components": {s: len(v) for s, v in by_status.items()}, "template": TEMPLATE_FOR.get(p.id)}


def detail(preset_id: str) -> dict:
    p = projects()[preset_id]
    comps = components()
    prog = progress()
    return {**p.model_dump(), **summary(p, prog), "stages": [s.model_dump() for s in p.stages],
            "done_stages": sorted(prog.get(preset_id, [])),
            "component_details": [{"id": c, **comps[c].model_dump(), "status_name": STATUS[comps[c].status]}
                                  for c in p.components],
            "scaffolded": (PROJECTS_DIR / preset_id).exists(),
            "unlocks": [q.id for q in projects().values() if preset_id in q.prerequisites]}


def export() -> dict:
    """Everything the online artifact needs, in one object."""
    return {"levels": LEVELS, "tracks": TRACKS, "status": STATUS,
            "components": {k: v.model_dump() for k, v in components().items()},
            "projects": [{**p.model_dump(), "template": TEMPLATE_FOR.get(p.id)} for p in projects().values()],
            "settings_presets": [s.model_dump() for s in settings_presets().values()]}


# ---------- scaffolding ----------

def _readme(p: Project) -> str:
    comps = components()
    lines = [f"# {p.title}", f"_{p.title_en}_ · سطح {LEVELS[p.level]} · {p.weeks} هفته", "",
             f"**کاربرد واقعی:** {p.real_world}", "", f"**مسئله:** {p.problem}", "", f"**هدف:** {p.goal}", "",
             "## داده", *[f"- [{d.name}]({d.url}) · {d.license} · {d.note}" if d.url else f"- {d.name} · {d.note}"
                          for d in p.data], "",
             "## قطعه‌ها", *[f"- `{c}` {comps[c].name}: **{STATUS[comps[c].status]}** ({comps[c].where})"
                             for c in p.components], ""]
    for i, s in enumerate(p.stages, 1):
        lines += [f"## مرحله‌ی {i}: {s.title}", "**یاد بگیر:**", *[f"- {x}" for x in s.learn], "**بساز:**",
                  *[f"- [ ] {x}" for x in s.build], f"**بسنج:** {s.measure}", f"**دام:** {s.pitfall}", ""]
    lines += ["## معیارها", *[f"- {m}" for m in p.metrics], "", "## guardrail", *[f"- {g}" for g in p.guardrails], "",
              "## production", *[f"- {g}" for g in p.production], "", "## سؤال‌های مصاحبه", *[f"- {q}" for q in p.interview],
              "", "## نسخه‌ی پیشرفته", *[f"- {a}" for a in p.advanced], "", "## خط رزومه (با عددهای خودت پر کن)", "",
              f"> {p.cv}", ""]
    return "\n".join(lines)


def scaffold(preset_id: str, target: Path | None = None, overwrite: bool = False) -> dict:
    """projects/<id>/: README (the full plan), config.yaml (preset params), a runnable starter, data/eval folders."""
    p = projects()[preset_id]
    if p.implemented and p.implemented.project == "support-agent" and preset_id == "p08_support_agent":
        return {"ok": False, "error": "این پروژه همین repo است؛ از صفحه‌ی مرحله‌ها استفاده کن."}
    dest = (target or PROJECTS_DIR) / preset_id
    if dest.exists() and not overwrite:
        return {"ok": False, "error": f"{dest} already exists", "path": str(dest)}
    (dest / "data").mkdir(parents=True, exist_ok=True)
    (dest / "eval").mkdir(exist_ok=True)
    (dest / "results").mkdir(exist_ok=True)
    (dest / "README.md").write_text(_readme(p), encoding="utf-8")
    (dest / "config.yaml").write_text(
        f"# {p.title_en}: parameters (edit, re-run, compare)\n" + yaml.safe_dump(p.params, sort_keys=False, allow_unicode=True),
        encoding="utf-8")
    files = ["README.md", "config.yaml"]
    tpl = TEMPLATE_FOR.get(preset_id)
    if tpl:
        for f in sorted(x for x in (TEMPLATES / tpl).rglob("*") if x.is_file() and "__pycache__" not in x.parts):
            target_path = dest / f.relative_to(TEMPLATES / tpl)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target_path)
            files.append(str(f.relative_to(TEMPLATES / tpl)))
    return {"ok": True, "path": str(dest), "files": files, "template": tpl,
            "next": f"cd projects/{preset_id} ; python run.py   (README.md has the plan)"}


def check() -> list[str]:
    for fn in (components, projects, settings_presets):
        fn.cache_clear()
    from ..settings import Settings
    problems = []
    ps = projects()
    for sp in settings_presets().values():
        data = Settings().model_dump(mode="json")
        for k, v in sp.changes.items():
            sec, _, f = k.partition(".")
            if sec not in data or f not in data[sec]:
                problems.append(f"settings preset {sp.id}: unknown key {k}")
            else:
                data[sec][f] = v
        try:
            Settings.model_validate(data)
        except Exception as e:
            problems.append(f"settings preset {sp.id}: {e}")
    for pid in TEMPLATE_FOR:
        if pid not in ps:
            problems.append(f"template mapping for unknown preset {pid}")
        elif not (TEMPLATES / TEMPLATE_FOR[pid]).is_dir():
            problems.append(f"{pid}: template folder {TEMPLATE_FOR[pid]} missing")
    return problems


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "export":
        Path(sys.argv[2]).write_text(json.dumps(export(), ensure_ascii=False, indent=1), encoding="utf-8")
    elif cmd == "html":
        data = json.dumps(export(), ensure_ascii=False).replace("</", "<\\/")      # keep </script> out of the data
        page = (Path(__file__).parent / "roadmap_template.html").read_text(encoding="utf-8").replace("__DATA__", data)
        Path(sys.argv[2]).write_text(page, encoding="utf-8")
    else:
        probs = check()
        print("\n".join(probs) or f"ok: {len(projects())} projects, {len(components())} components, "
                                  f"{len(settings_presets())} settings presets")
        sys.exit(1 if probs else 0)

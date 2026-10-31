"""Project presets, settings presets, scaffolding and the starters that must run without a model."""
import os
import subprocess
import sys

import pytest

pytest.importorskip("pydantic")

from support.config import ROOT  # noqa: E402
from support.panel import presets  # noqa: E402


@pytest.fixture(autouse=True)
def tmp_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPPORT_PANEL_DB", str(tmp_path / "panel.db"))


def test_all_preset_files_are_valid():
    assert presets.check() == []
    ps = presets.projects()
    assert len(ps) >= 10
    assert {p.level for p in ps.values()} == {1, 2, 3}                  # basic, intermediate and advanced
    assert {t for p in ps.values() for t in p.tracks} >= {"rag", "agent", "workflow", "eval", "production", "ml", "world_models"}
    for p in ps.values():
        assert p.stages and p.interview and p.advanced and p.data, p.id
        for q in p.prerequisites:
            assert ps[q].order < p.order, f"{p.id} depends on a later project {q}"


def test_every_external_component_names_a_tool_and_ready_ones_exist():
    import importlib
    for cid, c in presets.components().items():
        assert c.where, cid
        if c.status not in ("ready", "labkit") or not c.where.startswith(("support.", "labkit.", "jepa_lab.")) or " " in c.where:
            continue
        parts = c.where.split(".")
        obj, rest = None, []
        for i in range(len(parts), 0, -1):                          # the longest importable module prefix
            try:
                obj, rest = importlib.import_module(".".join(parts[:i])), parts[i:]
                break
            except ModuleNotFoundError as e:
                if e.name and not e.name.startswith(("support", "labkit", "jepa_lab")):
                    obj = "optional dependency missing"          # e.g. langgraph not installed in CI
                    break
        if isinstance(obj, str):
            continue
        assert obj is not None, f"{cid}: {c.where} not importable"
        for name in rest:
            obj = getattr(obj, name)                                 # fails if the referenced code is gone


def test_progress_roundtrip():
    out = presets.set_progress("p01_faq_search", 1, True)
    assert out["done"] == [1] and out["total"] == len(presets.projects()["p01_faq_search"].stages)
    presets.set_progress("p01_faq_search", 1, False)
    assert presets.progress().get("p01_faq_search", []) == []
    with pytest.raises(ValueError):
        presets.set_progress("p01_faq_search", 99, True)


def test_scaffold_every_preset_and_refuse_overwrite(tmp_path):
    for pid in presets.projects():
        out = presets.scaffold(pid, target=tmp_path)
        if pid == "p08_support_agent":
            assert out["ok"] is False
            continue
        assert out["ok"], out
        readme = (tmp_path / pid / "README.md").read_text(encoding="utf-8")
        assert presets.projects()[pid].title in readme and "## مرحله‌ی 1" in readme
        if out["template"]:
            assert (tmp_path / pid / "run.py").exists()
            subprocess.run([sys.executable, "-m", "py_compile", str(tmp_path / pid / "run.py")], check=True)
    assert presets.scaffold("p01_faq_search", target=tmp_path)["ok"] is False


@pytest.mark.parametrize("pid, expect", [
    ("p01_faq_search", "recall@5"),
    ("p07_email_triage_workflow", "waiting_approval"),
    ("p13_graphrag", "path found"),
    ("p14_llmops_platform", "escalation rate"),
    ("p16_llm_security", "guardrail caught"),
    ("p22_agentic_rag", "abstained correctly"),
    ("p24_agent_reliability", "pass^k"),
    ("p25_prompt_optimization", "TEST accuracy"),
    ("p26_mcp_a2a", "selftest ok"),
    ("p27_context_engineering", "clear stale results"),
    ("p28_secure_agent", "blocked"),
    ("p30_agent_skills", "skills valid"),
])
def test_model_free_starters_run(tmp_path, pid, expect):
    presets.scaffold(pid, target=tmp_path)
    out = subprocess.run([sys.executable, "run.py"], cwd=tmp_path / pid, capture_output=True, text=True, timeout=120,
                         env={**os.environ, "SUPPORT_ROOT": str(ROOT), "PYTHONUTF8": "1"})
    assert out.returncode == 0, out.stderr[-2000:]
    assert expect in out.stdout


@pytest.mark.parametrize("pid, expect", [("p17_jepa_basics", "random_encoder"), ("p19_world_model_planning", "planner cem")])
def test_jepa_starters_run_quick(tmp_path, pid, expect):
    pytest.importorskip("torch")
    presets.scaffold(pid, target=tmp_path)
    out = subprocess.run([sys.executable, "run.py", "--quick"], cwd=tmp_path / pid, capture_output=True, text=True, timeout=300,
                         env={**os.environ, "SUPPORT_ROOT": str(ROOT), "PYTHONUTF8": "1"})
    assert out.returncode == 0, out.stderr[-2000:]
    assert expect in out.stdout


def test_workflow_starter_never_acts_twice_on_a_duplicate(tmp_path):
    presets.scaffold("p07_email_triage_workflow", target=tmp_path)
    subprocess.run([sys.executable, "run.py"], cwd=tmp_path / "p07_email_triage_workflow", check=True, capture_output=True,
                   env={**os.environ, "SUPPORT_ROOT": str(ROOT)})
    actions = (tmp_path / "p07_email_triage_workflow" / "results" / "actions.jsonl").read_text().splitlines()
    assert sum('"HH-100007"' in a for a in actions) == 1


def test_settings_presets_are_valid_and_apply(monkeypatch, tmp_path):
    from support import settings as st
    from support.panel import service
    path = tmp_path / "project.yaml"
    monkeypatch.setattr(service, "apply_changes", lambda ch: st.apply_changes(ch, path))
    monkeypatch.setattr(service, "load", lambda: st.load(path))
    listed = {p["id"]: p for p in service.list_settings_presets()}
    assert {"quick_smoke", "laptop_cpu", "full_eval"} <= set(listed)
    out = service.apply_settings_preset("laptop_cpu")
    assert out["ok"] and st.load(path).rag.mode == "bm25"
    # Claude cannot use a preset to grant or remove its own permissions
    assert service.apply_settings_preset("claude_readonly", origin="claude")["ok"] is False


def test_preset_tools_are_exposed_to_claude_and_mcp():
    from support.panel import service
    names = {f.__name__ for f in service.ALL_TOOLS}
    assert {"list_presets", "get_preset", "scaffold_preset", "set_preset_progress", "apply_settings_preset"} <= names
    assert len(service.list_presets(level=3)["projects"]) >= 5
    d = service.get_preset("p06_text_to_sql")
    assert any(c["id"] == "sql_guard" and c["status"] == "labkit" for c in d["component_details"])


def test_export_for_the_artifact():
    data = presets.export()
    assert len(data["projects"]) == len(presets.projects()) and data["components"] and data["settings_presets"]

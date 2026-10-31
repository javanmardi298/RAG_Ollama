"""The control panel's logic: catalog, run registry and runner, advice rules, tools, Claude integrations, web API.

Nothing here needs Ollama, a model, data or the internet. The registry and logs go to a temporary folder.
"""
import json
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("pydantic")

from support.config import ROOT  # noqa: E402
from support.panel import catalog, registry, runner  # noqa: E402


@pytest.fixture(autouse=True)
def tmp_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPPORT_PANEL_DB", str(tmp_path / "panel.db"))
    monkeypatch.setattr(runner, "LOG_DIR", tmp_path / "logs")
    yield tmp_path


# ---------- catalog ----------

def test_every_task_points_to_an_existing_script():
    for _st, task in catalog.TASKS.values():
        scripts = [p for p in task.cmd if p.startswith("scripts/") or p.startswith("tests/")]
        for s in scripts:
            assert (ROOT / s).exists(), f"{task.id}: {s} missing"


def test_catalog_settings_sections_and_job_ad_exist():
    from support.settings import Settings
    sections = set(Settings().model_dump())
    for st in catalog.STAGES:
        assert set(st.settings) <= sections, st.id
        assert set(st.job_ad) <= set(catalog.JOB_AD), st.id
        assert st.concepts and st.steps and st.interview and st.advanced, st.id
    covered = {j for st in catalog.STAGES for j in st.job_ad}
    assert covered == set(catalog.JOB_AD)          # every requirement of the job ad has at least one stage


def test_placeholders_are_filled_from_settings():
    from support.settings import Settings
    s = Settings.model_validate({"serving": {"port": 9001}})
    assert runner.resolve_cmd(["uvicorn", "--port", "{serving.port}"], s) == ["uvicorn", "--port", "9001"]


# ---------- registry and runner ----------

def _fake_task(monkeypatch, code, task_id="fake", kind="batch"):
    st = catalog.STAGES[5]
    task = catalog.Task(task_id, "fake", [sys.executable, "-c", code], kind=kind)
    monkeypatch.setitem(catalog.TASKS, task_id, (st, task))
    monkeypatch.setattr(runner, "TASKS", catalog.TASKS)


def _wait(run_id, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        run = registry.get_run(run_id)
        if run["status"] not in ("queued", "running"):
            return run
        time.sleep(0.2)
    raise AssertionError("run did not finish")


def test_run_writes_log_status_and_settings_snapshot(monkeypatch):
    _fake_task(monkeypatch, "print('hello from the task'); print('é ü ß ✓')")
    out = runner.start("fake", origin="test", check_needs=False)
    run = _wait(out["run_id"])
    assert run["status"] == "succeeded" and run["exit_code"] == 0
    assert "hello from the task" in runner.tail(out["run_id"]) and "✓" in runner.tail(out["run_id"])
    assert run["settings"]["rag"]["k"] >= 1 and run["origin"] == "test"


def test_failed_run_is_marked_failed(monkeypatch):
    _fake_task(monkeypatch, "import sys; print('boom'); sys.exit(3)")
    run = _wait(runner.start("fake", check_needs=False)["run_id"])
    assert run["status"] == "failed" and run["exit_code"] == 3


def test_one_batch_at_a_time_and_stop(monkeypatch):
    _fake_task(monkeypatch, "import time; time.sleep(30)", task_id="slow")
    first = runner.start("slow", check_needs=False)
    with pytest.raises(runner.RunError, match="still running"):
        runner.start("slow", check_needs=False)
    time.sleep(1)
    runner.stop(first["run_id"])
    run = _wait(first["run_id"], timeout=15)
    assert run["status"] == "stopped"


def test_unknown_task_and_missing_prerequisites_are_explained(monkeypatch):
    with pytest.raises(runner.RunError, match="unknown task"):
        runner.start("rm -rf /")
    from support.panel import preflight
    monkeypatch.setattr(preflight, "failing", lambda ids: [{"label": "سرور Ollama", "fix": "start Ollama"}])
    with pytest.raises(runner.RunError, match="start Ollama"):
        runner.start("stage2_rag")


def test_dead_wrapper_is_reconciled_as_lost():
    rid = registry.create_run(1, "x", "batch", ["x"], "test", Path("x.log"), {})
    registry.update_run(rid, status="running", pid=999_999_9)
    runner.reconcile()
    assert registry.get_run(rid)["status"] == "lost"


def test_stop_before_start_wins():
    rid = registry.create_run(1, "x", "batch", ["x"], "test", Path("x.log"), {})
    registry.update_run(rid, status="stopped")
    assert registry.mark_running(rid, 123) is False
    assert registry.get_run(rid)["status"] == "stopped"


# ---------- tools (service) ----------

def test_update_settings_reports_errors_and_affected_stages(monkeypatch, tmp_path):
    from support import settings as st
    from support.panel import service
    path = tmp_path / "project.yaml"
    monkeypatch.setattr(service, "apply_changes", lambda ch: st.apply_changes(ch, path))
    monkeypatch.setattr(service, "load", lambda: st.load(path))
    bad = service.update_settings({"rag.k": 99})
    assert bad["ok"] is False and bad["errors"][0]["loc"] == "rag.k"
    good = service.update_settings({"rag.k": 5})
    assert good["ok"] and good["changed"] == {"rag.k": {"old": 3, "new": 5}} and 2 in good["stages_to_rerun"]
    assert registry.last_event(kind="settings_changed")["detail"]["rag.k"]["new"] == 5


def test_claude_cannot_change_its_own_permissions():
    from support.panel import service
    out = service.update_settings({"claude.allow_runs": True}, origin="claude")
    assert out["ok"] is False


def test_read_project_file_blocks_secrets_and_escapes():
    from support.panel import service
    assert "def decide" in service.read_project_file("src/support/decision.py")["text"]
    for bad in (".env", "../outside.txt", ".git/config"):
        with pytest.raises((ValueError, FileNotFoundError)):
            service.read_project_file(bad)


def test_tool_schemas_are_complete():
    from support.panel import service
    for fn in service.ALL_TOOLS:
        sch = service.tool_schema(fn)
        assert sch["description"] and "origin" not in sch["input_schema"]["properties"]
        for name, prop in sch["input_schema"]["properties"].items():
            assert prop.get("type"), f"{fn.__name__}.{name} has no JSON type"


def test_compare_runs_shows_parameter_and_metric_deltas():
    from support.panel import service
    a = registry.create_run(4, "stage4_thresholds", "batch", [], "test", Path("a"), {"rag": {"k": 3}})
    b = registry.create_run(4, "stage4_thresholds", "batch", [], "test", Path("b"), {"rag": {"k": 5}})
    registry.update_run(a, status="succeeded", metrics={"dev automation rate": 0.6})
    registry.update_run(b, status="succeeded", metrics={"dev automation rate": 0.7})
    c = service.compare_runs(a, b)
    assert c["params_changed"] == {"rag.k": {"a": 3, "b": 5}}
    assert c["metrics"]["dev automation rate"]["delta"] == pytest.approx(0.1)


# ---------- advice and results ----------

def _checks(**ok):
    ids = ["python", "pkg_core", "ollama", "ollama_model", "disk", "venv", "data_splits", "intent_model",
           "anthropic_key", "claude_desktop", "git"]
    return [{"id": i, "label": i, "ok": ok.get(i, True), "level": "error" if not ok.get(i, True) else "ok",
             "detail": "", "fix": f"fix {i}"} for i in ids]


def test_advice_points_to_stage0_first_and_is_ordered(monkeypatch, tmp_path):
    from support.panel import advisor, results
    monkeypatch.setattr(results, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(advisor, "RESULTS_DIR", tmp_path)
    items = advisor.advice(_checks(data_splits=False, ollama=False))
    levels = [i["level"] for i in items]
    assert levels == sorted(levels, key=["error", "warn", "info"].index)
    assert any(i["action"] == {"type": "run", "task": "stage0_data"} for i in items)
    assert any("Ollama" in i["title"] or i["title"] == "ollama" for i in items if i["level"] == "error")


def test_advice_flags_stale_results_after_a_parameter_change(monkeypatch, tmp_path):
    from support.panel import advisor
    from support.settings import Settings
    old = Settings().model_dump(mode="json")
    rid = registry.create_run(2, "stage2_rag", "batch", [], "test", Path("x"), old)
    registry.update_run(rid, status="succeeded")
    new = Settings.model_validate({**old, "rag": {**old["rag"], "k": 5}})
    stale = advisor._settings_drift(new)
    assert stale and stale[0]["stage"] == 2 and "rag.k: 3 → 5" in stale[0]["text"]


def test_results_read_stage_files(monkeypatch, tmp_path):
    from support.panel import results
    monkeypatch.setattr(results, "RESULTS_DIR", tmp_path)
    assert results.stage_results(6)["available"] is False
    (tmp_path / "stage6_summary.json").write_text(json.dumps({
        "n": 20, "task_success": 0.8, "automation_rate": 0.7, "false_automation_rate": 0.05,
        "policy_violation_rate": 0.0, "unnecessary_handoff_rate": 0.1, "mean_turns": 3, "task_success_ci95": [0.6, 0.95]}))
    labels = [m["label"] for m in results.stage_results(6)["metrics"]]
    # Automation Rate is never shown without False Automation Rate next to it
    assert labels.index("false automation rate") == labels.index("automation rate") + 1
    (tmp_path / "stage9_ab.json").write_text("{not json")
    assert results.stage_results(9)["available"] is False      # a broken file must not break the panel


# ---------- Claude Desktop config, .env ----------

def test_claude_desktop_install_merges_and_backs_up(tmp_path):
    from support.panel import claude_desktop
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}, "theme": "dark"}))
    claude_desktop.install([cfg])
    data = json.loads(cfg.read_text())
    assert data["theme"] == "dark" and "other" in data["mcpServers"]
    entry = data["mcpServers"]["support-agent"]
    assert entry["command"] == sys.executable and entry["args"] == ["-m", "support.panel.mcp_server"]
    assert list(tmp_path.glob("claude_desktop_config.backup-*.json"))
    claude_desktop.uninstall([cfg])
    assert "support-agent" not in json.loads(cfg.read_text())["mcpServers"]


def test_envfile_keeps_other_lines_and_masks(tmp_path, monkeypatch):
    from support.panel import envfile
    monkeypatch.setattr(envfile, "ENV_PATH", tmp_path / ".env")
    (tmp_path / ".env").write_text("# comment\nHF_TOKEN=abc\n")
    envfile.set_value("ANTHROPIC_API_KEY", "sk-ant-api03-abcdefghijklmnop")
    text = (tmp_path / ".env").read_text()
    assert "HF_TOKEN=abc" in text and "# comment" in text
    assert envfile.mask("sk-ant-api03-abcdefghijklmnop") == "sk-ant-…mnop"
    with pytest.raises(KeyError):
        envfile.set_value("PATH", "x")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


# ---------- MCP server and Claude chat ----------

def test_mcp_server_exposes_all_tools_without_origin():
    pytest.importorskip("mcp")
    import asyncio
    from support.panel import mcp_server, service
    tools = asyncio.run(mcp_server.build().list_tools())
    names = {t.name for t in tools}
    assert names == {f.__name__ for f in service.ALL_TOOLS}
    for t in tools:
        schema = getattr(t, "input_schema", None) or t.inputSchema
        assert "origin" not in schema.get("properties", {})


class _Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _FakeMessages:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def create(self, **kw):
        self.calls.append(kw)
        return self.replies.pop(0)


def test_claude_chat_runs_tools_and_returns_the_answer(monkeypatch):
    from support.panel import claude_chat, service
    usage = _Block(input_tokens=10, output_tokens=5)
    replies = [
        _Block(stop_reason="tool_use", usage=usage, model="m",
               content=[_Block(type="tool_use", id="t1", name="get_settings", input={"section": "rag"})]),
        _Block(stop_reason="end_turn", usage=usage, model="m", content=[_Block(type="text", text="k is 3")]),
    ]
    fake = _Block(beta=_Block(messages=_FakeMessages(replies)), messages=_FakeMessages([]))

    class FakeAnthropic:
        class AuthenticationError(Exception): ...
        class RateLimitError(Exception): ...
        class APIConnectionError(Exception): ...
        class APIStatusError(Exception): ...

    monkeypatch.setattr(claude_chat, "_client", lambda: (FakeAnthropic, fake))
    chat = claude_chat.ClaudeChat()
    out = chat.send("t", "what is rag.k?")
    assert out["reply"] == "k is 3" and out["tool_calls"][0]["tool"] == "get_settings"
    sent = fake.beta.messages.calls
    assert sent[0]["model"] == "claude-opus-5-5" and sent[0]["fallbacks"] == "default"
    tool_result = sent[1]["messages"][2]["content"][0]      # user, assistant(tool_use), user(tool_result), ...
    assert tool_result["tool_use_id"] == "t1" and json.loads(tool_result["content"])["k"]["value"] == service.get_settings("rag")["k"]["value"]
    assert usage.input_tokens * 2 == out["usage"]["input_tokens"]


# ---------- web API ----------

def test_web_api_main_endpoints(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from support.panel import web
    c = TestClient(web.app, headers={"X-Panel": "1"})
    assert c.get("/").status_code == 200
    assert len(c.get("/api/catalog").json()["stages"]) == 10
    stage = c.get("/api/stage/4").json()
    assert stage["tasks"] and "decision" in stage["settings_values"]
    s = c.get("/api/settings").json()
    assert s["values"]["rag"]["k"] >= 1 and "$defs" in s["schema"]
    assert c.post("/api/settings", json={"changes": {"rag.k": 99}}).json()["ok"] is False
    assert c.post("/api/runs", json={"task": "nope"}).status_code == 400
    assert c.get("/results/../configs/project.yaml").status_code == 404
    # another website in the same browser cannot drive the panel
    assert TestClient(web.app).post("/api/runs", json={"task": "tests_all"}).status_code == 403
    assert c.get("/api/catalog", headers={"host": "evil.example"}).status_code == 403


def test_tutorial_docs_are_readable_from_the_panel():
    from support.panel import service
    for path, needle in [("docs/jepa.md", "SIGReg"), ("docs/research_2026.md", "pass^k")]:
        f = service.read_project_file(path, max_chars=200_000)
        assert needle in f["text"] and not f.get("truncated"), path

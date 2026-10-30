"""The lesson engine: every solution passes its check, every starter fails, notebooks and the CLI work."""
import json
import sys

import pytest

from learn import api, notebooks
from learn import notebook as nbmod


@pytest.fixture(autouse=True)
def tmp_work(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "WORK", tmp_path / "work")


def test_selftest_all_lessons():
    assert api.selftest() == []


def test_progress_hints_solution_gate_and_diary():
    lesson = "p01_faq_search"
    assert api.next_step(lesson) == "step01_chunk_markdown"
    assert api.solution(lesson, 1)["ok"] is False                      # needs an attempt first
    out = api.check(lesson, 1)                                         # the untouched starter
    assert out["passed"] is False and all(r.get("todo") for r in out["results"])
    assert api.progress()[lesson]["step01_chunk_markdown"]["attempts"] == 1
    assert [api.hint(lesson, 1)["level"] for _ in range(4)] == [1, 2, 3, 3]
    sol = api.solution(lesson, 1)
    assert sol["ok"] and "def chunk_markdown" in sol["code"]
    assert api.progress()[lesson]["step01_chunk_markdown"]["solution_viewed"] is True


def test_passing_answer_is_recorded_and_next_step_advances():
    lesson = "p01_faq_search"
    f = api.answer_file(lesson, 1)
    f.write_text((api.LESSONS / lesson / "step01_chunk_markdown" / "solution.py").read_text(encoding="utf-8"), encoding="utf-8")
    out = api.check(lesson, 1)
    assert out["passed"] and api.progress()[lesson]["step01_chunk_markdown"]["passed"]
    assert api.next_step(lesson) == "step02_bm25"


def test_crash_and_syntax_error_in_student_code_are_reported_not_raised():
    lesson = "p01_faq_search"
    f = api.answer_file(lesson, 2)
    f.write_text("def tokenize(:\n", encoding="utf-8")
    out = api.check(lesson, 2)
    assert not out["passed"] and "SyntaxError" in out["results"][0]["message"]
    f.write_text("raise ZeroDivisionError('oops')\n", encoding="utf-8")
    out = api.check(lesson, 2)
    assert "ZeroDivisionError" in out["results"][0]["message"]
    assert "ZeroDivisionError" in (api.WORK / "errors.md").read_text(encoding="utf-8")


def test_infinite_loop_times_out():
    f = api.answer_file("p01_faq_search", 1)
    f.write_text("while True:\n    pass\n", encoding="utf-8")
    out = api.check("p01_faq_search", 1, timeout=3)
    assert not out["passed"] and "timeout" in out["results"][0]["message"]


def test_notebook_is_valid_and_checks_run_against_notebook_globals(capsys):
    nb = notebooks.build("p01_faq_search")
    assert nb["nbformat"] == 4 and any("Open In Colab" in "".join(c["source"]) for c in nb["cells"])
    assert sum(c["cell_type"] == "code" for c in nb["cells"]) == 1 + 2 * 5          # setup + (starter, check) per step
    json.dumps(nb)
    ns = {}
    exec((api.LESSONS / "p01_faq_search" / "step01_chunk_markdown" / "solution.py").read_text(encoding="utf-8"), ns)
    nbmod.check_cell("p01_faq_search", "step01_chunk_markdown", ns)
    assert "PASSED" in capsys.readouterr().out


def test_quiz_files_are_well_formed():
    for lid in api.lessons():
        for s in api.steps(lid):
            qs = api.quiz(lid, s)
            assert len(qs) >= 3, (lid, s)
            for q in qs:
                assert 0 <= q["answer"] < len(q["options"]) and q["why"], (lid, s, q["q"])


def test_cli_list_and_check(capsys):
    from learn.__main__ import main
    assert main(["list"]) == 0
    assert "p22_agentic_rag" in capsys.readouterr().out
    assert main(["check", "p01_faq_search", "1"]) == 1
    assert main(["show", "nope"]) == 2


def test_index_is_up_to_date():
    from learn import build
    before = (api.LESSONS / "README.md").read_text(encoding="utf-8")
    build.build()
    assert (api.LESSONS / "README.md").read_text(encoding="utf-8") == before, "run `python -m learn build` and commit lessons/README.md"


def test_teacher_tools_hide_solutions(monkeypatch):
    from support.panel import service
    monkeypatch.delenv("LEARN_REVEAL_SOLUTIONS", raising=False)
    with pytest.raises(ValueError):
        service.read_project_file("lessons/p01_faq_search/step01_chunk_markdown/solution.py")
    assert "solution.py" not in service.read_project_file("lessons/p01_faq_search/step01_chunk_markdown")["entries"]
    names = {f.__name__ for f in service.ALL_TOOLS}
    assert {"lessons_list", "lesson_step", "lesson_check", "lesson_hint", "lessons_progress"} <= names
    assert "lesson_solution" not in names and "solution" not in " ".join(names)
    monkeypatch.setenv("LEARN_REVEAL_SOLUTIONS", "1")
    assert "def chunk_markdown" in service.read_project_file("lessons/p01_faq_search/step01_chunk_markdown/solution.py")["text"]


def test_provider_env_defaults_to_offline(monkeypatch):
    from learn import llm
    monkeypatch.delenv("LEARN_PROVIDER", raising=False)
    assert llm.get().chat([{"role": "user", "content": "x"}]).content.startswith("(offline")
    assert sys.version_info >= (3, 10)


# ---------- panel API for the lessons page ----------

@pytest.fixture
def client():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from support.panel.web import app
    return TestClient(app), {"X-Panel": "1"}


def test_panel_lessons_flow(client):
    c, H = client
    tree = c.get("/api/lessons").json()
    assert {t["lesson"] for t in tree["tree"] if t["interactive"]} >= {"p01_faq_search", "p22_agentic_rag", "p17_jepa_basics", "m01_compare_models"}
    d = c.get("/api/lessons/p01_faq_search/1").json()
    assert d["is_starter"] and d["hints_total"] == 3 and len(d["quiz"]) == 3 and "answer" not in d["quiz"][0] and d["next"] == "step02_bm25"
    sol = (api.LESSONS / "p01_faq_search" / "step01_chunk_markdown" / "solution.py").read_text(encoding="utf-8")
    bad = c.post("/api/lessons/p01_faq_search/1/check", json={}, headers=H).json()
    assert bad["passed"] is False
    good = c.post("/api/lessons/p01_faq_search/1/check", json={"code": sol}, headers=H).json()
    assert good["passed"] is True
    assert c.get("/api/lessons/p01_faq_search/1").json()["code"] == sol            # saved by the check call
    assert [t for t in c.get("/api/lessons").json()["tree"] if t["lesson"] == "p01_faq_search"][0]["steps"][0]["passed"] is True
    h = c.post("/api/lessons/p01_faq_search/1/hint", json={}, headers=H).json()
    assert h["level"] == 1 and h["of"] == 3
    q = c.post("/api/lessons/p01_faq_search/1/quiz", json={"answers": [1, 1, 1]}, headers=H).json()
    assert q["score"] == 3 and q["wrong"] == []
    assert c.post("/api/lessons/p01_faq_search/1/quiz", json={"answers": [0, 0]}, headers=H).status_code == 400
    assert c.post("/api/lessons/p01_faq_search/1/reset", json={}, headers=H).json()["ok"]
    assert c.get("/api/lessons/p01_faq_search/1").json()["is_starter"] is True


def test_panel_lessons_provider_and_guards(client):
    c, H = client
    assert c.post("/api/lessons/provider", json={"provider": "nope"}, headers=H).status_code == 400
    assert c.post("/api/lessons/provider", json={"provider": "opencode", "model": "claude"}, headers=H).status_code == 400
    assert c.post("/api/lessons/provider", json={"provider": "openai_compatible", "model": "m", "api_base": "ftp://x"}, headers=H).status_code == 400
    ok = c.post("/api/lessons/provider", json={"provider": "ollama", "model": "qwen2.5:7b", "budget_usd": 1}, headers=H).json()
    assert ok["provider"] == "ollama" and c.get("/api/lessons/provider").json()["budget_usd"] == 1
    c.post("/api/lessons/provider", json={"provider": "offline"}, headers=H)
    t = c.post("/api/lessons/provider/test", headers=H).json()
    assert t["ok"] and t["reply"].startswith("(offline")
    assert c.get("/api/lessons/nope/1").status_code == 404
    assert c.put("/api/lessons/p01_faq_search/1/answer", json={"code": "x"}).status_code == 403   # writes need the X-Panel header
    assert c.put("/api/lessons/p01_faq_search/1/answer", json={"code": "x" * 300_000}, headers=H).status_code == 400
    assert c.get("/api/lessons/p01_faq_search/..%2F..%2Fx").status_code in (404, 400)


def test_run_answer_uses_the_chosen_provider_env():
    api.set_provider({"provider": "offline"})
    f = api.answer_file("p01_faq_search", 5)
    f.write_text("import os\nprint('PROVIDER=' + os.environ['LEARN_PROVIDER'])\n", encoding="utf-8")
    out = api.run_answer("p01_faq_search", 5, timeout=30)
    assert out["ok"] and "PROVIDER=offline" in out["stdout"]

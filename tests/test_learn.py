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

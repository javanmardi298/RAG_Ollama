"""Build guides: the files a learner copies must work on their own, outputs.json must match a real run, pages are up to date."""
import json
import os
import shutil
import subprocess
import sys

import pytest

from learn import guides


def test_guides_load_and_reference_existing_files():
    assert set(guides.ids()) >= {"p01_faq_search", "p22_agentic_rag", "p17_jepa_basics"}
    for gid in guides.ids():
        g = guides.load(gid)
        assert g["repo"] and g["steps"] and g["readme"] and g["outputs"].get("cells"), gid
        for s in g["steps"]:
            assert s["title"] and s.get("where"), (gid, s)
        placeholders = set(__import__("re").findall(r"\{(\w+)\}", g["readme"] + "".join(s.get("cv", "") for s in g["steps"])))
        assert placeholders <= set(g.get("fill", {})), (gid, placeholders - set(g.get("fill", {})))
        nb = guides.notebook(gid)
        assert nb["nbformat"] == 4 and sum(c["cell_type"] == "code" for c in nb["cells"]) == len(g["outputs"]["cells"]), gid


@pytest.mark.parametrize("gid", ["p01_faq_search", "p22_agentic_rag", "p17_jepa_basics"])
def test_copied_files_pass_their_own_tests(gid, tmp_path):
    if gid == "p17_jepa_basics":
        pytest.importorskip("torch")
    work = tmp_path / gid
    shutil.copytree(guides.GUIDES / gid / "files", work)
    for cmd in (["check_setup.py"], ["-m", "pytest", "-q", "-p", "no:cacheprovider"]):
        p = subprocess.run([sys.executable, *cmd], cwd=work, capture_output=True, text=True, timeout=300,
                           env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
        assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-1500:]


@pytest.mark.parametrize("gid", ["p01_faq_search", "p22_agentic_rag"])
def test_notebooks_run_and_outputs_json_is_current(gid):
    pytest.importorskip("nbclient")
    pytest.importorskip("ipykernel")
    fresh = guides.verify(gid, save=False)
    saved = guides.load(gid)["outputs"]
    assert fresh["cells"] == saved["cells"] and fresh["results"] == saved["results"], "run `python -m learn.guides verify` and commit"


def test_jepa_guide_notebook_runs():
    pytest.importorskip("torch")
    pytest.importorskip("nbclient")
    if not os.environ.get("LEARN_SLOW"):
        pytest.skip("set LEARN_SLOW=1 (about 2 minutes)")
    out = guides.verify("p17_jepa_basics", save=False)
    assert out["results"]["verdict"]["collapsed"] == ["naive"]


def test_guide_markdown_is_current_and_html_builds(tmp_path):
    for gid in guides.ids():
        assert (guides.GUIDES / gid / "GUIDE.md").read_text(encoding="utf-8") == guides.markdown(gid), "run `python -m learn.guides build`"
    out = tmp_path / "g.html"
    guides.html(out)
    page = out.read_text(encoding="utf-8")
    assert "<title>" in page and "__DATA__" not in page and "</script" not in page.split("const DATA = ")[1].split(";\nconst $")[0]
    data = json.loads(page.split("const DATA = ")[1].split(";\nconst $ =")[0].replace("<\\/", "</"))
    assert len(data["guides"]) == len(guides.ids())

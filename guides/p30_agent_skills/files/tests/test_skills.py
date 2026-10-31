import json
import subprocess
import sys

from skills_kit import activate, activation_report, context_cost, load_skills, validate


def test_skills_are_valid():
    assert validate(load_skills()) == []


def test_validation_catches_mistakes(tmp_path):
    d = tmp_path / "skills" / "Bad_Name"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: Bad_Name\ndescription: does things\n---\nRun `scripts/missing.py`.\n")
    probs = " ".join(validate(load_skills(tmp_path / "skills")))
    assert "name must equal" in probs and "40-1024" in probs and "Use when" in probs and "missing file" in probs


def test_progressive_disclosure_saves_context():
    c = context_cost(load_skills())
    assert c["always_loaded_tokens"] < c["if_all_in_prompt_tokens"]


def test_activation():
    skills = load_skills()
    assert activate("check the totals of this invoice", skills) == "invoice-check"
    assert activate("write a poem about autumn", skills) is None
    assert activation_report(skills)["correct"] >= 6


def test_invoice_script(tmp_path):
    script = "skills/invoice-check/scripts/validate_invoice.py"
    ok = subprocess.run([sys.executable, script, "examples/invoice_ok.json"], capture_output=True, text=True)
    bad = subprocess.run([sys.executable, script, "examples/invoice_bad.json"], capture_output=True, text=True)
    assert ok.returncode == 0 and "invoice ok" in ok.stdout and "******************3000" in ok.stdout.replace(" ", "")
    assert bad.returncode == 1 and "missing field: number" in bad.stdout and "in the future" in bad.stdout and "not net" in bad.stdout
    json.loads(open("examples/invoice_bad.json").read())

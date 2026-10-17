"""configs/project.yaml: defaults, validation, atomic updates, and how stage 4 output reaches the agent."""
import json

import pytest

pytest.importorskip("pydantic")

from support import settings as st  # noqa: E402


def test_committed_project_yaml_is_valid_and_matches_defaults():
    assert st.load() == st.Settings()


def test_seed_in_config_comes_from_project_yaml():
    from support.config import SEED
    assert SEED == st.load().project.seed


def test_apply_changes_saves_valid_values(tmp_path):
    path = tmp_path / "project.yaml"
    new, diff = st.apply_changes({"rag.k": 5, "llm.chat_model": "llama3.1:8b"}, path)
    assert new.rag.k == 5 and diff == {"rag.k": (3, 5), "llm.chat_model": ("qwen2.5:7b", "llama3.1:8b")}
    assert st.load(path).rag.k == 5
    assert path.read_text(encoding="utf-8").startswith("# Experiment parameters")


@pytest.mark.parametrize("changes", [
    {"rag.k": 0},                                  # out of range
    {"rag.mode": "magic"},                          # not an allowed value
    {"decision.error_budget_high": 0.5},            # riskier intents must get a stricter budget
    {"llm.host": "localhost:11434"},                # no scheme
])
def test_invalid_changes_save_nothing(tmp_path, changes):
    path = tmp_path / "project.yaml"
    st.apply_changes({"rag.k": 4}, path)
    with pytest.raises(Exception):
        st.apply_changes({"evaluation.n_run": 50, **changes}, path)
    s = st.load(path)
    assert s.rag.k == 4 and s.evaluation.n_run == 20     # the valid part of the batch was not saved either


def test_unknown_setting_is_rejected(tmp_path):
    with pytest.raises(KeyError):
        st.apply_changes({"rag.top_k": 5}, tmp_path / "project.yaml")


def test_policy_numbers_are_not_settings():
    keys = {f"{sec}.{k}" for sec, fields in st.Settings().model_dump().items() for k in fields}
    assert not any("auto_approve" in k or "withdrawal" in k or "return_days" in k for k in keys)


def test_tuned_thresholds_follow_the_switch(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "RESULTS_DIR", tmp_path)
    (tmp_path / "thresholds.json").write_text(json.dumps({"low": 0.4, "medium": 0.6, "high": 0.9}))
    monkeypatch.setattr(st, "settings", lambda: st.Settings())
    assert st.tuned_thresholds() == {"low": 0.4, "medium": 0.6, "high": 0.9}
    off = st.Settings.model_validate({"decision": {"use_tuned_thresholds": False}})
    monkeypatch.setattr(st, "settings", lambda: off)
    assert st.tuned_thresholds() is None


def test_schema_has_descriptions_for_every_field():
    sch = st.schema()
    for name, ref in sch["properties"].items():
        props = sch["$defs"][ref["$ref"].split("/")[-1]]["properties"]
        missing = [k for k, v in props.items() if not v.get("description")]
        assert not missing, f"{name}: {missing}"

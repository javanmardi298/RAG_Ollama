"""The prose policies must state the same numbers as configs/policy_rules.yaml."""
import re

import pytest

from support.config import POLICY_DIR, rules

r = rules()
CHECKS = {
    "returns": [r["returns"]["legal_withdrawal_days"], r["returns"]["store_return_days"]],
    "refunds": [r["refunds"]["auto_approve_max_eur"], r["refunds"]["issue_within_days"]],
    "damaged_items": [r["damaged_items"]["report_within_days"], r["damaged_items"]["auto_replace_max_eur"]],
    "shipping": [r["shipping"]["delayed_after_days"]],
}


@pytest.mark.parametrize("lang", ["en", "de"])
@pytest.mark.parametrize("doc, numbers", CHECKS.items())
def test_numbers_appear_in_prose(lang, doc, numbers):
    text = (POLICY_DIR / lang / f"{doc}.md").read_text(encoding="utf-8")
    found = {int(n) for n in re.findall(r"\b\d+\b", text)}
    for n in numbers:
        assert int(n) in found, f"{lang}/{doc}.md does not mention {n}"


def test_both_languages_have_the_same_documents():
    names = lambda lang: {p.name for p in (POLICY_DIR / lang).glob("*.md")}  # noqa: E731
    assert names("en") == names("de")

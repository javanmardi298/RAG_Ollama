from conftest import edge
from support import policy


def test_return_boundaries(shop):
    assert policy.can_return(edge(shop, "return_day_store_limit"), False).allowed
    assert policy.can_return(edge(shop, "return_day_legal_limit"), False).allowed
    d = policy.can_return(edge(shop, "return_one_day_too_late"), False)
    assert not d.allowed and d.reason == "return_window_passed"


def test_custom_made_cannot_be_returned(shop):
    o = edge(shop, "custom_made_recent")
    assert policy.can_return(o, bool(o["custom_made"])).reason == "custom_made_excluded"


def test_refund_limit_is_inclusive():
    assert not policy.refund_decision(150.00).needs_human
    assert policy.refund_decision(150.01).needs_human


def test_damage_window(shop):
    assert policy.damage_decision(edge(shop, "damage_report_last_day")).allowed
    assert not policy.damage_decision(edge(shop, "damage_report_too_late")).allowed


def test_cancel_and_delay(shop):
    assert policy.can_cancel(edge(shop, "processing_can_cancel")).allowed
    assert policy.can_cancel(edge(shop, "shipped_delayed")).reason == "already_shipped"
    assert policy.delivery_status(edge(shop, "shipped_delayed")).reason == "delayed"
    assert policy.delivery_status(edge(shop, "shipped_not_yet_delayed")).reason == "in_transit"

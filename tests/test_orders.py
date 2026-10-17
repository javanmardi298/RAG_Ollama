"""Invariants the order database must satisfy. If one fails, every later stage would learn from bad data."""
from datetime import date

from support.config import reference_date, rules
from support.orders import build_database


def rows(db, sql):
    return [dict(r) for r in db.execute(sql)]


def test_dates_follow_the_order_lifecycle(db):
    for o in rows(db, "SELECT * FROM orders"):
        if o["shipped_at"]:
            assert o["ordered_at"] <= o["shipped_at"]
        if o["delivered_at"]:
            assert o["shipped_at"] and o["shipped_at"] <= o["delivered_at"]
        for col in ("ordered_at", "shipped_at", "delivered_at", "returned_at"):
            if o[col]:
                assert date.fromisoformat(o[col]) <= reference_date(), "no events in the future"


def test_status_matches_dates(db):
    for o in rows(db, "SELECT * FROM orders"):
        s = o["status"]
        if s == "processing":
            assert o["shipped_at"] is None
        if s == "shipped":
            assert o["shipped_at"] and o["delivered_at"] is None and o["tracking_no"]
        if s in ("delivered", "returned"):
            assert o["delivered_at"]
        if s == "cancelled":
            assert o["cancelled_at"] and o["shipped_at"] is None


def test_every_status_occurs(db):
    statuses = {r["status"] for r in rows(db, "SELECT DISTINCT status FROM orders")}
    assert statuses >= {"processing", "shipped", "delivered", "cancelled"}


def test_edge_cases_exist(db):
    scenarios = {r["scenario"] for r in rows(db, "SELECT scenario FROM orders WHERE scenario IS NOT NULL")}
    assert {"return_one_day_too_late", "refund_just_above_auto_limit", "shipped_delayed"} <= scenarios


def test_refund_status_follows_auto_limit(db):
    limit = rules()["refunds"]["auto_approve_max_eur"]
    for r in rows(db, "SELECT * FROM refunds"):
        assert (r["status"] == "pending_review") == (r["amount_eur"] > limit)


def test_build_is_deterministic(tmp_path, fake_wands):
    a, b = tmp_path / "a.db", tmp_path / "b.db"
    for p in (a, b):
        build_database(fake_wands, p, n_customers=20, n_products=50, n_orders=100)
    import sqlite3
    dump = lambda p: list(sqlite3.connect(p).iterdump())  # noqa: E731
    assert dump(a) == dump(b)

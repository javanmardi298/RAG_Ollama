"""Stage 3/4: store policy as pure functions.

Every function takes plain data (an order dict, a date) and returns a Decision.
No database, no LLM, no side effects: that makes each rule testable on its own and
lets the agent, the guardrails and the evaluation all use exactly the same logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .config import reference_date, rules


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str                       # machine-readable code, e.g. "already_shipped"
    needs_human: bool = False         # allowed in principle, but a person must approve
    facts: dict = field(default_factory=dict)  # numbers the answer may quote


def _days_since(iso: str | None, today: date) -> int | None:
    return (today - date.fromisoformat(iso)).days if iso else None


def can_cancel(order: dict, today: date | None = None) -> Decision:
    allowed_statuses = rules()["cancellation"]["allowed_statuses"]
    if order["status"] == "cancelled":
        return Decision(False, "already_cancelled")
    if order["status"] in allowed_statuses:
        return Decision(True, "ok", facts={"refund_eur": order["total_eur"]})
    if order["status"] == "shipped":
        return Decision(False, "already_shipped", facts={"next_step": "return_after_delivery"})
    return Decision(False, f"status_{order['status']}")


def can_return(order: dict, custom_made: bool, today: date | None = None) -> Decision:
    today = today or reference_date()
    r = rules()["returns"]
    if order["status"] == "returned":
        return Decision(False, "already_returned")
    if order["status"] != "delivered":
        return Decision(False, "not_delivered_yet", facts={"status": order["status"]})
    if custom_made:
        return Decision(False, "custom_made_excluded")
    days = _days_since(order["delivered_at"], today)
    facts = {"days_since_delivery": days, "limit_days": r["store_return_days"]}
    if days <= r["store_return_days"]:
        return Decision(True, "ok", facts=facts)
    return Decision(False, "return_window_passed", facts=facts)


def refund_decision(amount_eur: float) -> Decision:
    limit = rules()["refunds"]["auto_approve_max_eur"]
    facts = {"amount_eur": amount_eur, "auto_limit_eur": limit}
    if amount_eur <= limit:
        return Decision(True, "ok", facts=facts)
    return Decision(True, "above_auto_limit", needs_human=True, facts=facts)


def damage_decision(order: dict, today: date | None = None) -> Decision:
    today = today or reference_date()
    r = rules()["damaged_items"]
    if order["status"] not in ("delivered", "returned"):
        return Decision(False, "not_delivered_yet")
    days = _days_since(order["delivered_at"], today)
    facts = {"days_since_delivery": days, "limit_days": r["report_within_days"]}
    if days > r["report_within_days"]:
        return Decision(False, "report_window_passed", needs_human=True, facts=facts)
    if order["total_eur"] > r["auto_replace_max_eur"]:
        return Decision(True, "above_auto_limit", needs_human=True, facts=facts)
    return Decision(True, "ok", facts=facts)


def delivery_status(order: dict, today: date | None = None) -> Decision:
    today = today or reference_date()
    limit = rules()["shipping"]["delayed_after_days"]
    facts = {"status": order["status"], "carrier": order.get("carrier"),
             "tracking_no": order.get("tracking_no")}
    if order["status"] != "shipped":
        return Decision(True, order["status"], facts=facts)
    days = _days_since(order["shipped_at"], today)
    facts["days_in_transit"] = days
    if days > limit:
        return Decision(True, "delayed", needs_human=True, facts=facts)
    return Decision(True, "in_transit", facts=facts)


def can_change_address(order: dict) -> Decision:
    if order["status"] in rules()["shipping"]["address_change_statuses"]:
        return Decision(True, "ok")
    return Decision(False, "already_shipped" if order["status"] == "shipped" else f"status_{order['status']}")

"""Stage 3: the tools the agent can call.

Security rules built into the code, not left to the prompt:
* The customer's identity comes from the session (after verify_customer), never from
  arguments the LLM writes. The LLM cannot ask for "customer C0042's orders".
* Every action checks policy.py first and is written to an audit table.
* Actions are idempotent: a second cancel/return/refund for the same order is refused,
  so a retry or a confused model cannot pay out twice.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import date
from pathlib import Path

from . import policy
from .config import DB_PATH, reference_date

AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS actions (
    action_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   TEXT NOT NULL REFERENCES orders(order_id),
    action     TEXT NOT NULL,
    details    TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (order_id, action)               -- idempotency: one cancel / return per order
);
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT,
    order_id   TEXT,
    reason     TEXT NOT NULL,
    summary    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

# Tools that change something: the agent must get an explicit "yes" from the customer first.
NEEDS_CONFIRMATION = {"cancel_order", "start_return", "report_damage", "change_address"}


def connect(path: str | Path = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")      # SQLite has foreign keys OFF by default
    con.executescript(AUDIT_SCHEMA)
    return con


def _result(ok: bool, reason: str, **facts) -> dict:
    return {"ok": ok, "reason": reason, "facts": facts}


class ToolBox:
    def __init__(self, con: sqlite3.Connection, today: date | None = None):
        self.con = con
        self.today = today or reference_date()
        self.customer_id: str | None = None      # set only by verify_customer

    # ---------- helpers ----------
    def _order(self, order_id: str) -> dict | None:
        row = self.con.execute(
            "SELECT o.*, p.name AS product, p.custom_made FROM orders o "
            "JOIN products p USING (product_id) WHERE o.order_id = ?", (order_id,)).fetchone()
        return dict(row) if row else None

    def _own_order(self, order_id: str) -> tuple[dict | None, dict | None]:
        """Return (order, None) if it belongs to the verified customer, else (None, error)."""
        if not self.customer_id:
            return None, _result(False, "not_verified")
        order = self._order(order_id)
        # Same answer for "does not exist" and "belongs to someone else": no information leak.
        if not order or order["customer_id"] != self.customer_id:
            return None, _result(False, "order_not_found")
        return order, None

    def _log(self, order_id: str, action: str, details: dict) -> bool:
        try:
            with self.con:                          # one transaction: all or nothing
                self.con.execute(
                    "INSERT INTO actions (order_id, action, details, created_at) VALUES (?, ?, ?, ?)",
                    (order_id, action, json.dumps(details), self.today.isoformat()))
            return True
        except sqlite3.IntegrityError:              # UNIQUE(order_id, action) -> already done
            return False

    # ---------- tools ----------
    def verify_customer(self, order_id: str, email: str) -> dict:
        row = self.con.execute(
            "SELECT c.customer_id, c.language FROM orders o JOIN customers c USING (customer_id) "
            "WHERE o.order_id = ? AND lower(c.email) = lower(?)", (order_id.strip(), email.strip())).fetchone()
        if not row:
            return _result(False, "verification_failed")
        self.customer_id = row["customer_id"]
        return _result(True, "ok", language=row["language"])

    def list_orders(self) -> dict:
        if not self.customer_id:
            return _result(False, "not_verified")
        rows = self.con.execute(
            "SELECT o.order_id, o.status, o.ordered_at, o.total_eur, p.name AS product "
            "FROM orders o JOIN products p USING (product_id) WHERE customer_id = ? "
            "ORDER BY ordered_at DESC LIMIT 10", (self.customer_id,)).fetchall()
        return _result(True, "ok", orders=[dict(r) for r in rows])

    def get_order(self, order_id: str) -> dict:
        order, err = self._own_order(order_id)
        if err:
            return err
        keep = ("order_id", "status", "product", "total_eur", "ordered_at", "shipped_at",
                "delivered_at", "carrier", "tracking_no")
        return _result(True, "ok", **{k: order[k] for k in keep})

    def track_order(self, order_id: str) -> dict:
        order, err = self._own_order(order_id)
        if err:
            return err
        d = policy.delivery_status(order, self.today)
        return _result(True, d.reason, needs_human=d.needs_human, **d.facts)

    def cancel_order(self, order_id: str) -> dict:
        order, err = self._own_order(order_id)
        if err:
            return err
        d = policy.can_cancel(order, self.today)
        if not d.allowed:
            return _result(False, d.reason, **d.facts)
        if not self._log(order_id, "cancel", {"refund_eur": order["total_eur"]}):
            return _result(False, "already_requested")
        refund = policy.refund_decision(order["total_eur"])
        with self.con:
            self.con.execute("UPDATE orders SET status='cancelled', cancelled_at=? WHERE order_id=?",
                             (self.today.isoformat(), order_id))
            self.con.execute(
                "INSERT INTO refunds (refund_id, order_id, amount_eur, status, created_at) VALUES (?,?,?,?,?)",
                (f"R-{order_id[3:]}", order_id, order["total_eur"],
                 "pending_review" if refund.needs_human else "approved", self.today.isoformat()))
        return _result(True, "cancelled", refund_eur=order["total_eur"],
                       refund_needs_review=refund.needs_human)

    def start_return(self, order_id: str) -> dict:
        order, err = self._own_order(order_id)
        if err:
            return err
        d = policy.can_return(order, bool(order["custom_made"]), self.today)
        if not d.allowed:
            return _result(False, d.reason, **d.facts)
        if not self._log(order_id, "return", d.facts):
            return _result(False, "already_requested")
        return _result(True, "return_label_sent", **d.facts)

    def refund_status(self, order_id: str) -> dict:
        order, err = self._own_order(order_id)
        if err:
            return err
        row = self.con.execute("SELECT amount_eur, status, created_at FROM refunds WHERE order_id=?",
                               (order_id,)).fetchone()
        return _result(True, "ok", **dict(row)) if row else _result(False, "no_refund")

    def report_damage(self, order_id: str, description: str) -> dict:
        order, err = self._own_order(order_id)
        if err:
            return err
        d = policy.damage_decision(order, self.today)
        if not d.allowed or d.needs_human:
            return _result(False, d.reason, needs_human=True, **d.facts)
        if not self._log(order_id, "damage", {"description": description[:500]}):
            return _result(False, "already_requested")
        return _result(True, "replacement_or_refund_started", **d.facts)

    def change_address(self, order_id: str, new_address: str) -> dict:
        order, err = self._own_order(order_id)
        if err:
            return err
        d = policy.can_change_address(order)
        if not d.allowed:
            return _result(False, d.reason)
        n = self.con.execute("SELECT COUNT(*) FROM actions WHERE order_id=? AND action LIKE 'address_change%'",
                             (order_id,)).fetchone()[0]
        self._log(order_id, f"address_change_{n + 1}", {"new_address": new_address[:200]})
        return _result(True, "address_changed")

    def handoff(self, reason: str, summary: str, order_id: str | None = None) -> dict:
        with self.con:
            cur = self.con.execute(
                "INSERT INTO tickets (customer_id, order_id, reason, summary, created_at) VALUES (?,?,?,?,?)",
                (self.customer_id, order_id, reason, summary[:2000], self.today.isoformat()))
        return _result(True, "handed_off", ticket_id=cur.lastrowid)

    def call(self, name: str, arguments: dict) -> dict:
        """Dispatch a tool call coming from the LLM. Unknown tools and bad arguments are errors, not crashes."""
        if name not in TOOL_NAMES:
            return _result(False, "unknown_tool")
        try:
            return getattr(self, name)(**arguments)
        except TypeError as e:                        # wrong or missing arguments
            return _result(False, "bad_arguments", error=str(e))


def _fn(_name: str, _doc: str, **params: str) -> dict:
    return {"type": "function", "function": {
        "name": _name, "description": _doc,
        "parameters": {"type": "object",
                       "properties": {p: {"type": "string", "description": d} for p, d in params.items()},
                       "required": list(params)}}}


TOOL_SCHEMAS = [
    _fn("verify_customer", "Verify the customer. Required before any order information is shown.",
        order_id="Order number, e.g. HH-100042", email="Email address used for the order"),
    _fn("list_orders", "List the verified customer's recent orders."),
    _fn("get_order", "Show details of one order.", order_id="Order number"),
    _fn("track_order", "Delivery status and tracking number of an order.", order_id="Order number"),
    _fn("cancel_order", "Cancel an order that has not shipped yet. Only after the customer confirmed.",
        order_id="Order number"),
    _fn("start_return", "Start a return for a delivered order. Only after the customer confirmed.",
        order_id="Order number"),
    _fn("refund_status", "Status of the refund for an order.", order_id="Order number"),
    _fn("report_damage", "Report a damaged item. Only after the customer confirmed.",
        order_id="Order number", description="What is damaged"),
    _fn("change_address", "Change the delivery address of an order that has not shipped. Only after confirmation.",
        order_id="Order number", new_address="Full new address"),
    _fn("handoff", "Hand the conversation to a human agent.",
        reason="Short reason code", summary="Summary of the case for the human agent"),
]
TOOL_NAMES = {t["function"]["name"] for t in TOOL_SCHEMAS}

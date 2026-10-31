"""A synthetic but realistic order database for the support agent.

Everything is generated from a fixed seed and a fixed reference date, so the same
command always produces the same database (and the same test results).
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .config import SEED, reference_date, rules

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    language    TEXT NOT NULL CHECK (language IN ('de', 'en'))
);

CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    product_class TEXT,
    price_eur    REAL NOT NULL CHECK (price_eur > 0),
    custom_made  INTEGER NOT NULL DEFAULT 0 CHECK (custom_made IN (0, 1))
);

CREATE TABLE orders (
    order_id       TEXT PRIMARY KEY,
    customer_id    TEXT NOT NULL REFERENCES customers(customer_id),
    product_id     INTEGER NOT NULL REFERENCES products(product_id),
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    total_eur      REAL NOT NULL,
    payment_method TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN
                   ('processing', 'shipped', 'delivered', 'cancelled', 'returned')),
    ordered_at     TEXT NOT NULL,
    shipped_at     TEXT,
    delivered_at   TEXT,
    cancelled_at   TEXT,
    returned_at    TEXT,
    carrier        TEXT,
    tracking_no    TEXT,
    scenario       TEXT          -- set only for hand-made edge cases, used later in tests/eval
);

CREATE TABLE refunds (
    refund_id  TEXT PRIMARY KEY,
    order_id   TEXT NOT NULL REFERENCES orders(order_id),
    amount_eur REAL NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('pending_review', 'approved', 'issued')),
    created_at TEXT NOT NULL
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
"""

FIRST = ["Anna", "Lukas", "Mia", "Leon", "Emma", "Paul", "Sofia", "Jonas", "Lea", "Elias",
         "Hannah", "Noah", "Amira", "Mehmet", "Sara", "David", "Laura", "Reza", "Julia", "Tim"]
LAST = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
        "Hoffmann", "Koch", "Yilmaz", "Kaya", "Nowak", "Rahimi", "Klein", "Wolf"]
PAYMENTS = ["paypal", "credit_card", "sepa", "klarna"]
CARRIERS = ["DHL", "Hermes"]
CUSTOM_WORDS = r"custom|personali[sz]ed|monogram|engraved"


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


def make_products(wands: pd.DataFrame, n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Sample products from WANDS. WANDS has no prices, so we simulate a skewed price distribution."""
    sample = wands.sample(n=min(n, len(wands)), random_state=int(rng.integers(1_000_000)))
    prices = np.clip(rng.lognormal(mean=np.log(120), sigma=0.9, size=len(sample)), 8, 2500)
    by_name = sample["product_name"].str.contains(CUSTOM_WORDS, case=False, na=False).to_numpy()
    custom = by_name | (rng.random(len(sample)) < 0.02)
    return pd.DataFrame({
        "product_id": sample["product_id"].astype(int).to_numpy(),
        "name": sample["product_name"].to_numpy(),
        "product_class": sample["product_class"].to_numpy(),
        "price_eur": np.floor(prices) + 0.99,
        "custom_made": custom.astype(int),
    })


def make_customers(n: int, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        slug = f"{first}.{last}".lower().replace("ü", "ue")
        rows.append({
            "customer_id": f"C{i:04d}",
            "name": f"{first} {last}",
            "email": f"{slug}.{i}@example.com",   # example.com is reserved for examples (RFC 2606)
            "language": "de" if rng.random() < 0.6 else "en",
        })
    return pd.DataFrame(rows)


def _timeline(rng: np.random.Generator, today: date, age_days: int) -> dict:
    """Simulate one order's life and return its state as of `today`."""
    ordered = today - timedelta(days=age_days)
    state = {"ordered_at": ordered, "status": "processing", "shipped_at": None,
             "delivered_at": None, "cancelled_at": None, "returned_at": None}

    if rng.random() < 0.06:  # some customers cancel before shipping
        cancel_day = ordered + timedelta(days=int(rng.integers(0, 2)))
        if cancel_day <= today:
            state.update(status="cancelled", cancelled_at=cancel_day)
            return state

    shipped = ordered + timedelta(days=int(rng.integers(1, 4)))
    if shipped > today:
        return state
    state.update(status="shipped", shipped_at=shipped)

    lost = rng.random() < 0.04  # never arrives -> becomes "delayed" after enough days
    delivered = shipped + timedelta(days=int(rng.integers(2, 9)))
    if lost or delivered > today:
        return state
    state.update(status="delivered", delivered_at=delivered)

    if rng.random() < 0.08:
        returned = delivered + timedelta(days=int(rng.integers(3, 25)))
        if returned <= today:
            state.update(status="returned", returned_at=returned)
    return state


def make_orders(customers, products, n, rng, today) -> pd.DataFrame:
    rows = []
    for i in range(n):
        product = products.iloc[int(rng.integers(len(products)))]
        qty = 1 if rng.random() < 0.85 else 2
        state = _timeline(rng, today, age_days=int(rng.integers(0, 75)))
        shipped = state["shipped_at"] is not None
        rows.append({
            "order_id": f"HH-{100001 + i}",
            "customer_id": customers["customer_id"].iloc[int(rng.integers(len(customers)))],
            "product_id": int(product["product_id"]),
            "quantity": qty,
            "total_eur": round(qty * float(product["price_eur"]), 2),
            "payment_method": rng.choice(PAYMENTS),
            "carrier": rng.choice(CARRIERS) if shipped else None,
            "tracking_no": f"TRK{rng.integers(10**9, 10**10)}" if shipped else None,
            "scenario": None,
            **{k: _iso(v) if k != "status" else v for k, v in state.items()},
        })
    return pd.DataFrame(rows)


def edge_cases(customers, products, today, start_id: int) -> pd.DataFrame:
    """Hand-made orders that sit exactly on policy boundaries.

    Bugs hide at boundaries (day 14 vs 15, 150.00 vs 150.01 EUR), so we make sure they exist.
    """
    r = rules()
    std = products[products["custom_made"] == 0].iloc[0]
    custom = products[products["custom_made"] == 1].iloc[0]
    cust = customers["customer_id"].iloc[0]
    d = lambda days: today - timedelta(days=days)  # noqa: E731

    specs = [
        # scenario,                       product, total,  status,      ship_ago, deliv_ago
        ("return_day_legal_limit",         std,   59.99,  "delivered", 18, r["returns"]["legal_withdrawal_days"]),
        ("return_day_store_limit",         std,   59.99,  "delivered", 33, r["returns"]["store_return_days"]),
        ("return_one_day_too_late",        std,   59.99,  "delivered", 34, r["returns"]["store_return_days"] + 1),
        ("refund_at_auto_limit",           std,   r["refunds"]["auto_approve_max_eur"], "delivered", 8, 5),
        ("refund_just_above_auto_limit",   std,   r["refunds"]["auto_approve_max_eur"] + 0.01, "delivered", 8, 5),
        ("custom_made_recent",             custom, float(custom["price_eur"]), "delivered", 6, 3),
        ("damage_report_last_day",         std,   89.99,  "delivered", 10, r["damaged_items"]["report_within_days"]),
        ("damage_report_too_late",         std,   89.99,  "delivered", 11, r["damaged_items"]["report_within_days"] + 1),
        ("shipped_delayed",                std,   45.99,  "shipped",   r["shipping"]["delayed_after_days"] + 2, None),
        ("shipped_not_yet_delayed",        std,   45.99,  "shipped",   r["shipping"]["delayed_after_days"] - 2, None),
        ("processing_can_cancel",          std,   45.99,  "processing", None, None),
    ]
    rows = []
    for i, (scenario, prod, total, status, ship_ago, deliv_ago) in enumerate(specs):
        ordered = d((ship_ago or 0) + 1)
        rows.append({
            "order_id": f"HH-{start_id + i}", "customer_id": cust,
            "product_id": int(prod["product_id"]), "quantity": 1, "total_eur": round(total, 2),
            "payment_method": "paypal", "status": status,
            "ordered_at": _iso(ordered),
            "shipped_at": _iso(d(ship_ago)) if ship_ago is not None else None,
            "delivered_at": _iso(d(deliv_ago)) if deliv_ago is not None else None,
            "cancelled_at": None, "returned_at": None,
            "carrier": "DHL" if ship_ago is not None else None,
            "tracking_no": f"TRK90000000{i:02d}" if ship_ago is not None else None,
            "scenario": scenario,
        })
    return pd.DataFrame(rows)


def make_refunds(orders: pd.DataFrame, today: date) -> pd.DataFrame:
    limit = rules()["refunds"]["auto_approve_max_eur"]
    days = rules()["refunds"]["issue_within_days"]
    rows = []
    for o in orders[orders["status"] == "returned"].itertuples():
        returned = date.fromisoformat(o.returned_at)
        if o.total_eur > limit:
            status = "pending_review"
        elif (today - returned).days >= days:
            status = "issued"
        else:
            status = "approved"
        rows.append({"refund_id": f"R-{o.order_id[3:]}", "order_id": o.order_id,
                     "amount_eur": o.total_eur, "status": status, "created_at": o.returned_at})
    return pd.DataFrame(rows, columns=["refund_id", "order_id", "amount_eur", "status", "created_at"])


def build_database(wands: pd.DataFrame, db_path: str | Path, n_customers: int = 400,
                   n_products: int = 1500, n_orders: int = 2500, seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    today = reference_date()

    products = make_products(wands, n_products, rng)
    if not products["custom_made"].any():          # guarantee the edge case is buildable
        products.loc[products.index[-1], "custom_made"] = 1
    customers = make_customers(n_customers, rng)
    orders = make_orders(customers, products, n_orders, rng, today)
    orders = pd.concat([orders, edge_cases(customers, products, today, 100001 + n_orders)],
                       ignore_index=True)
    refunds = make_refunds(orders, today)

    db_path = Path(db_path)
    db_path.unlink(missing_ok=True)                # rebuild from scratch every time
    with sqlite3.connect(db_path) as con:
        con.executescript(SCHEMA)
        for name, table in [("customers", customers), ("products", products),
                            ("orders", orders), ("refunds", refunds)]:
            table.to_sql(name, con, if_exists="append", index=False)
    return {name: len(t) for name, t in
            [("customers", customers), ("products", products), ("orders", orders), ("refunds", refunds)]}

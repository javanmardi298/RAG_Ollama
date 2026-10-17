import sqlite3

import pandas as pd
import pytest

from support.orders import build_database


@pytest.fixture(scope="session")
def fake_wands() -> pd.DataFrame:
    """A tiny stand-in for WANDS product.csv with the same columns we use."""
    names = [f"oak table {i}" for i in range(195)] + [f"personalized mug {i}" for i in range(5)]
    return pd.DataFrame({"product_id": range(200), "product_name": names,
                         "product_class": ["Tables"] * 195 + ["Mugs"] * 5})


@pytest.fixture(scope="session")
def db(tmp_path_factory, fake_wands):
    path = tmp_path_factory.mktemp("db") / "shop.db"
    build_database(fake_wands, path, n_customers=50, n_products=150, n_orders=400)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    yield con
    con.close()


@pytest.fixture()
def shop(tmp_path, fake_wands):
    """A fresh, writable database per test (tools change data)."""
    from support.tools import connect
    path = tmp_path / "shop.db"
    build_database(fake_wands, path, n_customers=30, n_products=120, n_orders=200)
    con = connect(path)
    yield con
    con.close()


def edge(con, scenario):
    row = con.execute("SELECT o.*, c.email, p.custom_made FROM orders o JOIN customers c USING (customer_id) "
                      "JOIN products p USING (product_id) WHERE scenario = ?", (scenario,)).fetchone()
    return dict(row)

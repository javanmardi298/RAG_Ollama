from conftest import edge
from support.tools import ToolBox


def verified(shop, scenario):
    o = edge(shop, scenario)
    tb = ToolBox(shop)
    assert tb.verify_customer(o["order_id"], o["email"].upper())["ok"]   # email match ignores case
    return tb, o


def test_nothing_without_verification(shop):
    o = edge(shop, "processing_can_cancel")
    assert ToolBox(shop).get_order(o["order_id"])["reason"] == "not_verified"


def test_wrong_email_fails(shop):
    o = edge(shop, "processing_can_cancel")
    assert not ToolBox(shop).verify_customer(o["order_id"], "someone@example.com")["ok"]


def test_cannot_see_other_customers_orders(shop):
    tb, _ = verified(shop, "processing_can_cancel")
    other = shop.execute("SELECT order_id FROM orders WHERE customer_id != ? LIMIT 1", (tb.customer_id,)).fetchone()[0]
    assert tb.get_order(other)["reason"] == "order_not_found"


def test_cancel_once_and_refund_created(shop):
    tb, o = verified(shop, "processing_can_cancel")
    first = tb.cancel_order(o["order_id"])
    assert first["ok"] and first["reason"] == "cancelled"
    assert shop.execute("SELECT status FROM orders WHERE order_id=?", (o["order_id"],)).fetchone()[0] == "cancelled"
    assert shop.execute("SELECT COUNT(*) FROM refunds WHERE order_id=?", (o["order_id"],)).fetchone()[0] == 1
    assert not tb.cancel_order(o["order_id"])["ok"]                       # second time refused


def test_return_twice_is_refused(shop):
    tb, o = verified(shop, "return_day_store_limit")
    assert tb.start_return(o["order_id"])["ok"]
    assert tb.start_return(o["order_id"])["reason"] == "already_requested"


def test_delayed_parcel_needs_human(shop):
    tb, o = verified(shop, "shipped_delayed")
    assert tb.track_order(o["order_id"])["facts"]["needs_human"]


def test_unknown_tool_and_bad_arguments(shop):
    tb = ToolBox(shop)
    assert tb.call("drop_table", {})["reason"] == "unknown_tool"
    assert tb.call("get_order", {"wrong": 1})["reason"] == "bad_arguments"

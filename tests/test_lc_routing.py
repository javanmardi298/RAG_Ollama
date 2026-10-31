"""Routing of the LangGraph graph. Plain functions, so no LangChain install is needed to test them."""
from support.lc import routing


class Msg:
    def __init__(self, tool_calls=None):
        self.tool_calls = tool_calls or []


def test_decide_route_maps_actions_to_nodes():
    assert routing.decide_route("track_order", 0.95, [], 0, 0)[0] == "agent"
    assert routing.decide_route("check_refund_policy", 0.95, [], 0, 0)[0] == "rag"
    assert routing.decide_route("cancel_order", 0.95, ["legal_threat"], 0, 0)[0] == "handoff"
    assert routing.decide_route("newsletter_subscription", 0.99, [], 0, 0)[0] == "decline"
    assert routing.decide_route("cancel_order", 0.40, [], 0, 0)[0] == "clarify"


def test_after_agent_sends_actions_to_confirmation():
    assert routing.after_agent({"messages": [Msg()]}) == "guard_output"
    assert routing.after_agent({"messages": [Msg([{"name": "get_order", "args": {}, "id": "1"}])]}) == "tools"
    calls = [{"name": "verify_customer", "args": {}, "id": "1"}, {"name": "cancel_order", "args": {}, "id": "2"}]
    assert routing.after_agent({"messages": [Msg(calls)]}) == "confirm"


def test_after_tools_and_output():
    assert routing.after_tools({"handoff_reason": "delayed"}) == "handoff"
    assert routing.after_tools({"steps": routing.MAX_AGENT_STEPS}) == "handoff"
    assert routing.after_tools({"steps": 1}) == "agent"
    assert routing.after_output({"output_ok": True}) == routing.END
    assert routing.after_output({"output_ok": False, "output_retries": 1}) == "agent"
    assert routing.after_output({"output_ok": False, "output_retries": 2}) == "handoff"
    assert routing.after_rag({"answered": False}) == "handoff"

REQUIRES = ["labkit"]

DICTS = [{"id": "returns#0", "doc_id": "returns", "heading": "Returns", "text": "You can return items within 30 days."},
         {"id": "refunds#0", "doc_id": "refunds", "heading": "Refunds", "text": "Money comes back within 14 days."}]


class FakeLLM:
    """Replies by looking at the JSON schema; records every call."""

    def __init__(self, relevant=True, supported=True, route="retrieve", text="30 days [returns#0] [ghost#9]"):
        self.relevant, self.supported, self.route, self.text = relevant, supported, route, text
        self.json_calls, self.chat_calls = [], []

    def json(self, messages, schema):
        props = schema.get("properties", {})
        self.json_calls.append(next(iter(props)))
        if "relevant" in props:
            return {"relevant": self.relevant}
        if "route" in props:
            return {"route": self.route}
        if "queries" in props:
            return {"queries": ["other words"]}
        return {"supported": self.supported, "unsupported_claims": []}

    def chat(self, messages, tools=None, json_schema=None):
        self.chat_calls.append(messages)

        class R:
            content = self.text
        return R()


def _search(m, dicts=DICTS):
    chunks = m.to_chunks(dicts)
    return lambda q: chunks[:1]


def check_to_chunks(m):
    """dicts become labkit chunks (heading kept in meta)"""
    cs = m.to_chunks(DICTS)
    assert [c.chunk_id for c in cs] == ["returns#0", "refunds#0"] and cs[0].meta["heading"] == "Returns" and cs[1].doc_id == "refunds", cs


def check_answer_filters_citations(m):
    """citations are real chunk ids only"""
    llm = FakeLLM()
    text, cites = m.make_answer(llm)("how long?", m.to_chunks(DICTS))
    assert cites == ["returns#0"], cites
    sent = llm.chat_calls[0][-1]["content"]
    assert "[returns#0]" in sent and "how long?" in sent, sent


def check_agent_answers_with_all_components(m):
    """a relevant, supported answer flows through route, grade, answer, verify"""
    llm = FakeLLM()
    out = m.make_agent(_search(m), llm).run("how long to return?")
    assert not out.abstained and out.citations == ["returns#0"], out
    assert {"route", "relevant", "supported"} <= set(llm.json_calls), llm.json_calls


def check_agent_abstains_when_grader_says_no(m):
    """grader says irrelevant -> abstain after the round budget"""
    llm = FakeLLM(relevant=False)
    out = m.make_agent(_search(m), llm, max_rounds=2).run("ceo phone?")
    assert out.abstained and out.rounds <= 2, out


def check_agent_abstains_when_verifier_says_no(m):
    """verifier says unsupported -> abstain"""
    out = m.make_agent(_search(m), FakeLLM(supported=False), max_rounds=1).run("how long?")
    assert out.abstained, out


def check_direct_route_skips_search(m):
    """a direct question never searches"""
    called = []
    agent = m.make_agent(lambda q: called.append(q) or [], FakeLLM(route="direct", text="Hello!"))
    out = agent.run("hello")
    assert out.answer == "Hello!" and out.route == "direct" and called == [], (out, called)

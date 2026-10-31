from agentic_rag import (agentic_search, chunk_all, grade, load_data, make_llm_components, make_search, plain_rag, report,
                         rewrite, route, run_agent, verify)

C = [{"id": "returns#0", "heading": "Returns > Return window", "text": "You can return most items within 30 days of delivery."}]


def test_route():
    assert route("Hello!") == "direct" and route("2+2") == "direct" and route("how long to return a sofa") == "retrieve"


def test_grade_uses_ratio_and_synonyms():
    assert grade("how long do I have to send back a sofa", C[0])
    warranty = {"id": "w#1", "heading": "Warranty", "text": "Send a photo of the defect and your order number to support."}
    assert not grade("what is the CEO's phone number", warranty)          # one shared word of three


def test_loop_is_bounded_and_rewrites():
    out = agentic_search("q", lambda s: [], lambda q, c: True, lambda q, t: [f"q{len(t)}"], max_rounds=3)
    assert out["rounds"] == 3 and out["chunks"] == []
    assert rewrite("how to send back a sofa", [])[0] == "how to return a sofa"


def test_verify_rejects_invented_claims():
    assert verify("You can return items within 30 days [returns#0]", C)
    assert not verify("Gold members get free returns [returns#0]", C)


def test_agent_beats_plain_rag_on_unanswerable_questions():
    docs, questions = load_data()
    search = make_search(chunk_all(docs))
    agent = report([run_agent(q["question"], search) for q in questions], questions)
    plain = report([plain_rag(q["question"], search) for q in questions], questions)
    assert agent["answered_unanswerable"] < plain["answered_unanswerable"]
    assert agent["answered_correctly"] >= plain["answered_correctly"] - 1


def test_model_components_with_a_fake_model():
    def fake(msgs):
        p = msgs[-1]["content"]
        if "route" in p:
            return '{"route": "retrieve"}'
        if "relevant" in p:
            return '{"relevant": true}'
        if "supported" in p:
            return '{"supported": true}'
        return "You have 30 days [returns#0] [made_up#1]"
    out = run_agent("how long to return", lambda q: C, **make_llm_components(fake))
    assert not out["abstained"] and out["citations"] == ["returns#0"]

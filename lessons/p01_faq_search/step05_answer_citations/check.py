CHUNKS = [{"id": "returns#0", "heading": "Returns > Return window", "text": "You can return most items within 30 days."},
          {"id": "refunds#0", "heading": "Refunds > Timing", "text": "Money comes back within 14 days."}]


class Fake:
    """Stands in for a model: returns a prepared text and counts calls."""

    def __init__(self, text):
        self.text, self.calls, self.messages = text, 0, None

    def chat(self, messages, tools=None, json_schema=None):
        self.calls += 1
        self.messages = messages

        class R:
            content = self.text
        return R()


def check_prompt_lists_sources(m):
    """the prompt contains every source with its id, and the question"""
    msgs = m.build_messages("how long?", CHUNKS)
    assert [x["role"] for x in msgs] == ["system", "user"], [x["role"] for x in msgs]
    u = msgs[1]["content"]
    assert "[returns#0]" in u and "30 days" in u and "[refunds#0]" in u and "how long?" in u, u


def check_extract_valid_only(m):
    """only real ids are kept, once each, in order"""
    got = m.extract_citations("A [refunds#0] and B [fake#9] and again [refunds#0] and [returns#0]", {"returns#0", "refunds#0"})
    assert got == ["refunds#0", "returns#0"], got


def check_answer_with_citation(m):
    """a cited answer is accepted"""
    llm = Fake("You have 30 days [returns#0].")
    out = m.answer("how long?", CHUNKS, llm)
    assert out == {"answer": "You have 30 days [returns#0].", "citations": ["returns#0"], "abstained": False}, out


def check_fabricated_citation_rejected(m):
    """an answer that cites only invented ids is rejected"""
    out = m.answer("q", CHUNKS, Fake("Sure, 90 days [policy#42]."))
    assert out["abstained"] and out["answer"] is None, out


def check_no_chunks_no_model_call(m):
    """without sources the model is not even called"""
    llm = Fake("anything [x#1]")
    out = m.answer("q", [], llm)
    assert out["abstained"] is True and llm.calls == 0, (out, llm.calls)


def check_uncited_answer_rejected(m):
    """an answer without any citation is not trusted"""
    out = m.answer("q", CHUNKS, Fake("I think it is 30 days."))
    assert out["abstained"] and out["citations"] == [], out

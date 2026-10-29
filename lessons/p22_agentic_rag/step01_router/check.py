def check_greetings_are_direct(m):
    """greetings and thanks are answered directly"""
    for q in ["hello", "Hello!", "  thanks. ", "thank you"]:
        assert m.route(q) == "direct", f"{q!r} -> {m.route(q)}"


def check_arithmetic_is_direct(m):
    """pure arithmetic is direct"""
    assert m.route("2+2") == "direct" and m.route("(3 + 4) * 5") == "direct"


def check_normal_question_retrieves(m):
    """a normal question retrieves"""
    assert m.route("how long do I have to return a sofa") == "retrieve"
    assert m.route("is there a tracking link?") == "retrieve"


def check_multi_hop(m):
    """a compound question is multi_hop"""
    assert m.route("how long to return and when do I get my money back") == "multi_hop"


def check_and_alone_is_not_enough(m):
    """'and' without two question words stays a normal lookup"""
    assert m.route("return and refund policy") == "retrieve", m.route("return and refund policy")


def check_math_inside_text_is_not_math(m):
    """a question that merely contains digits is not arithmetic"""
    assert m.route("what is 2+2 days of delivery") == "retrieve"

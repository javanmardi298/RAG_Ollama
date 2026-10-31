REFUND = {"id": "refunds#0", "heading": "Refunds > Timing", "text": "We send your money back to the original payment method within 14 days."}
INVOICE = {"id": "payment#1", "heading": "Payment > Invoices", "text": "The invoice is attached to your order confirmation email."}
WARRANTY = {"id": "warranty#1", "heading": "Warranty > How to claim", "text": "Send a photo of the defect and your order number to support."}


def check_content_words(m):
    """content words: lowercase, no stop words, simple plurals"""
    assert m.content_words("The Invoices, are 14 days!") == {"invoice", "14", "day"}, m.content_words("The Invoices, are 14 days!")


def check_relevant_chunk_kept(m):
    """a matching chunk is relevant"""
    assert m.grade("when do I get my money back", REFUND) is True


def check_synonym_expansion(m):
    """'send back' finds return text"""
    ret = {"id": "returns#0", "heading": "Returns > Return window", "text": "You can return most items within 30 days."}
    assert m.grade("how long do I have to send back a sofa", ret) is True


def check_single_word_question(m):
    """a one-word question can still match"""
    assert m.grade("where is my invoice", INVOICE) is True


def check_unrelated_rejected(m):
    """the CEO question must not match the 'order number' chunk"""
    assert m.grade("what is the CEO's phone number", WARRANTY) is False, "one shared word ('number') of three is not enough"
    assert m.grade("can I pay by cheque", WARRANTY) is False


def check_empty_question(m):
    """a question with no content words is never relevant"""
    assert m.grade("how do you do", WARRANTY) is False


def check_min_ratio_parameter(m):
    """min_ratio is honoured"""
    assert m.grade("order number photo", WARRANTY, min_ratio=1.0) is True
    assert m.grade("order number cheque", WARRANTY, min_ratio=1.0) is False
    assert m.grade("order number cheque", WARRANTY, min_ratio=0.5) is True

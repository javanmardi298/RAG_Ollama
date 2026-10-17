from support.rag import BM25, Retriever, load_chunks, rrf


def test_chunks_carry_title_and_both_languages():
    chunks = load_chunks()
    assert {c.lang for c in chunks} == {"en", "de"}
    assert all(c.indexed_text.startswith(c.title) for c in chunks)


def test_bm25_prefers_matching_doc():
    s = BM25(["return within thirty days", "shipping takes days", "pay with paypal"]).scores("return days")
    assert s.argmax() == 0


def test_rrf_rewards_agreement():
    assert rrf([[1, 2, 3], [2, 1, 3]])[:2] in ([1, 2], [2, 1])
    assert rrf([[3, 1], [1, 3], [1, 2]])[0] == 1


def test_retrieval_finds_policy_per_language():
    r = Retriever(load_chunks())
    assert r.search("How long do I have to return an item", "en", 3, mode="bm25")[0].doc_id == "returns"
    top = r.search("Welche Zahlungsarten gibt es, PayPal oder Klarna?", "de", 3, mode="bm25")[0]
    assert top.doc_id == "payment_invoices" and top.lang == "de"

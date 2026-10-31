from faq_search import (BM25, Searcher, answer, chunk_all, chunk_markdown, evaluate, extract_citations, load_data,
                        reciprocal_rank, recall_at_k, rrf, trigram_search)

SAMPLE = "# Returns\n\n## Return window\nYou can return items\nwithin 30 days.\n\n## Exceptions\nCustom items cannot be returned.\n"


def test_chunks_keep_heading_path():
    cs = chunk_markdown(SAMPLE, "returns")
    assert [c["id"] for c in cs] == ["returns#0", "returns#1"]
    assert cs[0]["heading"] == "Returns > Return window" and cs[0]["text"] == "You can return items within 30 days."


def test_bm25_ranks_and_excludes_zero_scores():
    bm = BM25(["refund your money", "standard delivery days", "warranty for defects"])
    assert bm.search("money refund")[0] == 0
    assert bm.search("bitcoin") == []
    assert bm.idf("warranty") > 0


def test_trigram_survives_typos_and_rrf_fuses():
    texts = ["standard delivery takes three days", "we refund the money"]
    assert trigram_search("standrd delivry", texts)[0] == 0
    assert rrf([[2, 0, 1], [2, 1, 0]])[0] == 2 and rrf([[0, 1], [1, 0]]) == [0, 1]


def test_metrics():
    assert recall_at_k(["a", "b"], {"b"}, 2) == 1.0 and recall_at_k(["a", "b"], {"b"}, 1) == 0.0
    assert reciprocal_rank(["x", "y"], {"y"}) == 0.5


def test_hybrid_is_at_least_as_good_as_bm25_on_the_faq():
    docs, questions = load_data()
    s = Searcher(chunk_all(docs))
    assert evaluate(s, questions, "hybrid")["recall@3"] >= evaluate(s, questions, "bm25")["recall@3"] - 0.1


def test_answers_cite_real_sources_or_abstain():
    chunks = [{"id": "returns#0", "heading": "Returns", "text": "30 days."}]
    assert answer("q", [], lambda m: "x [returns#0]")["abstained"]                       # no evidence: model not called
    assert answer("q", chunks, lambda m: "90 days [fake#1]")["abstained"]                # invented citation
    ok = answer("q", chunks, lambda m: "You have 30 days [returns#0].")
    assert ok["citations"] == ["returns#0"] and not ok["abstained"]
    assert extract_citations("[a] [b] [a]", {"a", "b"}) == ["a", "b"]

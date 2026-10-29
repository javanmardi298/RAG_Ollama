def check_trigrams(m):
    """trigrams of a word are padded with spaces"""
    assert m.trigrams("ab") == {" ab", "ab "}, m.trigrams("ab")
    assert "ref" in m.trigrams("Refund") and " re" in m.trigrams("Refund") and "nd " in m.trigrams("Refund")


def check_trigram_typo(m):
    """a misspelled word still finds its document"""
    texts = ["standard delivery takes three days", "we refund the money", "warranty for furniture"]
    assert m.trigram_rank("standrd delivry", texts)[0] == 0, m.trigram_rank("standrd delivry", texts)


def check_trigram_zero_excluded(m):
    """no shared trigram -> not returned"""
    assert m.trigram_rank("qqq", ["abc def"]) == []


def check_rrf_order(m):
    """a document high in both lists wins"""
    assert m.rrf([[2, 0, 1], [2, 1, 0]])[0] == 2
    assert m.rrf([[0, 1], [1, 0]]) == [0, 1], "tie -> smaller index"


def check_rrf_union_and_scores(m):
    """documents in only one list are kept; scores use 1/(k+rank)"""
    out = m.rrf([[5], [7, 5]], k=60)
    assert out == [5, 7], out
    assert m.rrf([[1, 2]], k=1) == [1, 2]


def check_hybrid_recovers_typos(m):
    """hybrid finds the right text where BM25 alone fails"""
    texts = ["Standard delivery takes 3 to 5 working days.", "We send your money back within 14 days.",
             "Furniture has a 2 year warranty.", "Returns are free within 30 days."]
    bm = m.SimpleBM25(texts)
    q = "how fast is standrd delivry"
    assert bm.search(q, k=4)[:1] != [0], "(demo precondition) BM25 alone should miss the typo query"
    assert m.hybrid(q, bm, texts, top=1) == [0], m.hybrid(q, bm, texts, top=1)

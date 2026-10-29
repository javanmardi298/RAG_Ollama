DOCS = ["You can return items within 30 days of delivery",
        "We refund your money to the original payment method within 14 days",
        "Standard delivery takes 3 to 5 working days",
        "Furniture has a 2 year warranty against defects"]


def check_tokenize(m):
    """tokenize lowercases, keeps words and numbers, drops stop words"""
    assert m.tokenize("The Refund, is 14 days!") == ["refund", "14", "days"], m.tokenize("The Refund, is 14 days!")


def check_rare_words_weigh_more(m):
    """a rare word has a higher idf than a common one"""
    bm = m.BM25(DOCS)
    assert bm.idf("warranty") > bm.idf("within"), (bm.idf("warranty"), bm.idf("within"))
    assert bm.idf("within") > 0, "idf must stay positive"


def check_ranking(m):
    """the matching document comes first"""
    bm = m.BM25(DOCS)
    assert bm.search("refund money", k=2)[0] == 1, bm.search("refund money", k=2)
    assert bm.search("warranty defects")[0] == 3
    assert bm.search("standard working days")[0] == 2, bm.search("standard working days")


def check_zero_scores_excluded(m):
    """documents without any query word are not returned"""
    bm = m.BM25(DOCS)
    assert bm.search("bitcoin") == [], bm.search("bitcoin")
    assert len(bm.scores("bitcoin")) == 4 and sum(bm.scores("bitcoin")) == 0


def check_length_normalisation(m):
    """with the same tf, the shorter document scores higher"""
    bm = m.BM25(["refund", "refund policy of the shop is long and has many other words inside", "unrelated text"])
    s = bm.scores("refund")
    assert s[0] > s[1] > 0, s


def check_deterministic_ties(m):
    """equal scores are ordered by index"""
    bm = m.BM25(["alpha beta", "alpha beta", "gamma"])
    assert bm.search("alpha", k=2) == [0, 1]

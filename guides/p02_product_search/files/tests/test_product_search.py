from product_search import BM25, bootstrap, evaluate, load_data, mrr, ndcg, product_text, recall, rrf, top_k, trigram_scores


def test_metrics():
    rel = {10: 2, 11: 1, 12: 0}
    assert ndcg([10, 11, 12], rel) == 1.0 and ndcg([12, 11, 10], rel) < 1
    assert recall([10], rel) == 1.0 and mrr([12, 10], rel) == 0.5


def test_rich_text_contains_structured_features():
    p = load_data()[0][0]
    assert "|" not in product_text(p) and "color: " in product_text(p) and "Category" not in product_text(p, rich=False)


def test_search_and_fusion():
    texts = ["grey velvet sofa", "oak dining table", "brass floor lamp"]
    assert top_k(BM25(texts).scores("velvet sofa"), [1, 2, 3])[0] == 1
    assert top_k(trigram_scores("dinning tabel", texts), [1, 2, 3])[0] == 2
    assert rrf([[3, 1], [3, 2]])[0] == 3


def test_rich_text_beats_basic_on_the_sample():
    products, queries, qrels = load_data()
    ids = [p["product_id"] for p in products]
    res = {}
    for rich in (False, True):
        bm = BM25([product_text(p, rich) for p in products])
        res[rich] = evaluate({q: top_k(bm.scores(t), ids, 10) for q, t in queries.items()}, qrels)
    assert res[True][1]["ndcg@10"] > res[False][1]["ndcg@10"]
    sig = bootstrap({q: v["ndcg@10"] for q, v in res[False][0].items()}, {q: v["ndcg@10"] for q, v in res[True][0].items()})
    assert sig["diff"] > 0 and sig["low"] <= sig["diff"] <= sig["high"]

"""Run once after installing: checks Python, the data and the metrics."""
import sys

from product_search import load_data, ndcg, product_text, recall

print("Python", sys.version.split()[0])
products, queries, qrels = load_data()
print(len(products), "products,", len(queries), "queries,", sum(len(v) for v in qrels.values()), "labels")
print(product_text(products[0]))
rel = {10: 2, 11: 1, 12: 0}
print(ndcg([10, 11, 12], rel), round(ndcg([12, 11, 10], rel), 3), recall([10], rel))
print("setup ok")

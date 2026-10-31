# Product search for a furniture shop

![tests](https://github.com/<your-user>/product_search/actions/workflows/tests.yml/badge.svg)

Search over a furniture catalogue, measured with graded relevance labels. Compares basic vs rich product text (structured
features), BM25, typo-tolerant character trigrams and hybrid fusion (RRF), with a bootstrap test for every difference.

## Results (`results/results.json`, 24 queries)
| method | nDCG@10 | recall@10 | MRR |
|---|---|---|---|
| BM25, basic text | {basic_ndcg} | {basic_recall} | {basic_mrr} |
| BM25, rich text | {rich_ndcg} | {rich_recall} | {rich_mrr} |
| trigram, rich text | {tri_ndcg} | {tri_recall} | {tri_mrr} |
| hybrid (RRF) | {hyb_ndcg} | {hyb_recall} | {hyb_mrr} |

Rich text vs basic: nDCG difference {rich_diff} (95% bootstrap interval {rich_low} to {rich_high}).

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_product_search.ipynb` and run all cells. Optional dense search: `pip install sentence-transformers`.

## Limitations
- Synthetic catalogue with rule-based labels; the next step is the real WANDS dataset (Wayfair, MIT licence).
- 24 queries: read the bootstrap interval, not only the mean.

## Licence
MIT

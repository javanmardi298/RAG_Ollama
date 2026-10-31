# FAQ search with grounded answers

![tests](https://github.com/<your-user>/faq_search/actions/workflows/tests.yml/badge.svg)

Customer questions are answered from a shop's FAQ pages. Search is built from scratch and measured on labelled questions;
answers must cite their sources or abstain.

## What it does
- **Chunking** by markdown section, keeping the heading path (`Returns > Return window`) with every chunk.
- **Search**: BM25 (exact words), character trigrams (typos), and a **hybrid** that fuses both with Reciprocal Rank Fusion.
- **Evaluation**: recall@3 and MRR on 12 answerable questions; 3 more questions have no answer on purpose.
- **Grounded answers**: the model sees the top 3 chunks and must cite them; invented citations are removed and an
  answer without a valid citation is not returned.
- Any model through one function: offline (no model), Ollama, Claude API or OpenCode (`FAQ_PROVIDER`).

## Results (`results/results.json`)
| method | recall@3 | MRR |
|---|---|---|
| BM25 | {bm25_recall} | {bm25_mrr} |
| trigram | {trigram_recall} | {trigram_mrr} |
| hybrid (RRF) | {hybrid_recall} | {hybrid_mrr} |

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Then open `01_faq_search.ipynb` and run all cells.

## Limitations
- 15 labelled questions: enough to learn and compare roughly, not to claim small differences.
- Plain RAG still answers unanswerable questions when retrieval returns something; evidence grading and abstention
  (agentic RAG) is the next step.
- English only, regular-expression tokenisation.

## Licence
MIT

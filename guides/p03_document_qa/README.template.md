# Company document Q&A with citations

![tests](https://github.com/<your-user>/document_qa/actions/workflows/tests.yml/badge.svg)

Employees ask questions about internal policies (markdown, text, HTML; PDF and Word optional). Answers cite their
source section; every number in an answer must appear in the cited text; without enough evidence the system abstains.

## Results (`results/results.json`, 18 questions: 15 answerable, 3 not covered by the documents)
| | right source | wrong source | wrong abstentions | right abstentions | answered unanswerable |
|---|---|---|---|---|---|
| offline (extractive) | {correct} | {wrong} | {wrong_abstain} | {right_abstain} | {unanswerable} |

## How it works
load (md / txt / html / pdf / docx) → chunk by heading, long sections as overlapping windows → BM25 → evidence check
(half of the question's content words) → answer with citations (offline extractive, Ollama, Claude or OpenCode) →
citation and number checks → abstain if any check fails.

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_document_qa.ipynb` and run all cells. Optional model: `DOCQA_PROVIDER=ollama|anthropic|opencode`.

## Limitations
- Four short documents and 18 questions: the perfect score says the set is small, not that the system is.
- Word-overlap evidence check; tables and scanned PDFs need OCR / table extraction.

## Licence
MIT

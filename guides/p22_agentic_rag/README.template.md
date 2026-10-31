# Agentic RAG: answer with evidence or abstain

![tests](https://github.com/<your-user>/agentic_rag/actions/workflows/tests.yml/badge.svg)

Plain RAG always answers, even when the search found nothing useful. This agent routes each question, grades the
evidence, rewrites the query when needed (at most 3 rounds), verifies the answer against the evidence and abstains
otherwise. Every decision is a small function with a rule-based and a model-based (Ollama / Claude / OpenCode) version.

## Results (`results/results.json`, 16 questions: 12 answerable, 3 unanswerable, 1 greeting)
| system | answered (answerable) | wrong abstentions | right abstentions | answered unanswerable |
|---|---|---|---|---|
| plain RAG | {plain_correct} | {plain_wrong_abstain} | {plain_right_abstain} | {plain_unanswerable} |
| agentic (rules) | {agent_correct} | {agent_wrong_abstain} | {agent_right_abstain} | {agent_unanswerable} |

## How it works
`route` (direct or retrieve) → `search` → `grade` (half of the question's content words must appear) → `rewrite`
(synonyms, content words) → `answer` (cited) → `verify` (every content word of the answer is in the evidence) → abstain.

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_agentic_rag.ipynb` and run all cells. Optional model: `AGENT_PROVIDER=ollama|anthropic|opencode`.

## Limitations
- Small labelled set; the rule grader is word overlap, not meaning.
- In the model version the same model answers and verifies.

## Licence
MIT

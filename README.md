# Marketplace Support Agent

An LLM-powered customer-support agent for an online store: it understands what the customer wants, answers policy questions from the store's documents, looks up and changes orders through tools, and decides when to hand over to a human. Every part is evaluated.

> Status: code for **all stages (0-9)** is in place with 66 unit tests, in two versions: plain Python (`src/support/`) and LangChain / LangGraph (`src/support/lc/`). Fill in the result tables below by running each stage. See `docs/design.md` for the plan and metrics, and the PDF guide for explanations.

## Results (fill from `results/`)
| Metric | Value |
|---|---|
| Intent macro-F1 (test) | ? |
| Intent ECE after temperature scaling | ? |
| Policy retrieval recall@3 (hybrid) | ? |
| Task success, simulated conversations (95% CI) | ? |
| Automation rate / false automation rate | ? / ? |
| Policy violations | ? |
| p95 latency per turn | ? |

## Stages
| # | Stage | Main skill |
|---|---|---|
| 0 | Data, order database, policies | data design, leakage-free splits |
| 1 | Intent classification | classical vs embedding vs LLM classifiers |
| 2 | Policy RAG | retrieval with citations (EN/DE) |
| 3 | Tools and multi-turn agent | tool calling, dialogue state |
| 4 | Decision and handoff | calibration, selective automation |
| 5 | Guardrails | policy checks, prompt-injection defence |
| 6 | Evaluation framework | automation, containment, false automation, LLM judge |
| 7 | German and noisy input | robustness |
| 8 | Serving and monitoring | FastAPI, Docker, latency, drift |
| 9 | Experiments | A/B simulation, LoRA fine-tuning |

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                                              # 66 tests, no data or model needed
jupyter lab notebooks/00_setup_data.ipynb             # stage 0
# then scripts/stage1_intents.py ... scripts/stage9_ab.py (each '# %%' is a cell in VS Code)
```
To reuse WANDS from the product-search project: `export WANDS_DIR=/path/to/product-search-rag/data/wands` before starting Jupyter.

## LangChain / LangGraph version
```bash
pip install -r requirements-lc.txt
python scripts/lc_stage3_chat.py        # the agent as a LangGraph state graph (SQLite checkpointer, interrupts)
python scripts/lc_stage6_compare.py     # plain vs LangGraph vs create_agent on the same scenarios
langgraph dev                           # LangGraph Studio
uvicorn app.main_lc:app --port 8001     # API with persistent sessions and streaming
```
Policy, tools, guardrails, decisions and evaluation are framework-free and shared by both versions.

## Layout
```
configs/      policy_rules.yaml (single source of truth), intents.yaml (routing)
policies/     store policies in en/ and de/
src/support/  shared code used by every stage
src/support/lc/  LangChain / LangGraph orchestration of the same stages
scripts/      one runnable script per stage
app/          FastAPI service (stage 8)
eval/         hand-written policy questions
notebooks/    stage 0 notebook
tests/        66 unit tests (no model or download needed)
results/      numbers reported in this README
docs/         design and decisions
```

## Data and licences
- Bitext customer-support dataset: CDLA-Sharing-1.0. Not committed; downloaded on first run.
- WANDS (Wayfair): MIT. Not committed.
- CLINC150 out-of-scope examples: see the licence in the clinc/oos-eval repository. Not committed.
- Orders, customers and prices are synthetic.

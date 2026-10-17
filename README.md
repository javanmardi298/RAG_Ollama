# Marketplace Support Agent

An LLM-powered customer-support agent for an online store: it understands what the customer wants, answers policy questions from the store's documents, looks up and changes orders through tools, and decides when to hand over to a human. Every part is evaluated.

> Status: code for **all stages (0-9)** is in place with 140 unit tests, in two versions: plain Python (`src/support/`) and LangChain / LangGraph (`src/support/lc/`), plus a **local control panel** that runs every stage, manages all parameters and connects to **Claude** (Claude Desktop via MCP, or the API). Fill in the result tables below by running each stage. See `docs/design.md` for the plan and metrics, `docs/panel.md` for the panel, and the PDF guide for explanations.

## Control panel (Windows)
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\setup.ps1            # venv, packages, .env, Ollama model, tests
windows\start_panel.bat         # http://127.0.0.1:8765
windows\install_claude_desktop.bat   # optional: Claude Desktop gets the same tools (MCP)
```
**Learning roadmap:** 16 real-world project presets from basic to advanced (FAQ search, product search, document QA, ticket triage, invoice extraction workflow, Text-to-SQL, email workflow, this agent, multilingual RAG, deep-research agent, code assistant, multi-agent claims, GraphRAG, LLMOps, fine-tuning/distillation, LLM security) in `presets/`, each with stages, data, metrics, pitfalls, interview questions and a runnable starter scaffolded into `projects/`. Building blocks they need beyond the agent live in `src/labkit/`.

Other systems: `pip install -r requirements.txt -r requirements-panel.txt && pip install -e . && python -m support.panel`.

The panel shows, per stage: what to learn (concepts, why this method, steps, pitfalls, interview questions, the advanced next step), its parameters as a validated form (`configs/project.yaml`), allow-listed tasks with live logs, results with charts, and run-to-run comparison. A code-based advisor lists what is missing or stale. Every run is recorded with its settings, git commit and headline metrics (`results/panel.db`).

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
pytest -q                                              # 140 tests, no data or model needed
python scripts/stage0_data.py                         # stage 0 (or notebooks/00_setup_data.ipynb)
# then scripts/stage1_intents.py ... scripts/stage9_ab.py (each '# %%' is a cell in VS Code), or run them from the panel
# all parameters (models, k, error budgets, sample sizes...) are in configs/project.yaml
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
configs/      policy_rules.yaml (single source of truth for policy), intents.yaml (routing),
              project.yaml (every experiment parameter, validated by src/support/settings.py)
policies/     store policies in en/ and de/
src/support/  shared code used by every stage
src/support/lc/  LangChain / LangGraph orchestration of the same stages
src/support/panel/  control panel, MCP server for Claude Desktop, Claude API chat (docs/panel.md)
src/labkit/   building blocks for the presets: loaders, chunking, retrieval, metrics, structured output,
              SQL guard, workflow engine, cache/ledger/router/prompts, knowledge graph, memory
presets/      16 project presets, components.yaml (what is ready / in labkit / external), settings presets
scripts/      one runnable script per stage
app/          FastAPI service (stage 8)
eval/         hand-written policy questions
notebooks/    stage 0 notebook
tests/        140 unit tests (no model or download needed)
windows/      setup.ps1, start_panel.bat, install_claude_desktop.bat
results/      numbers reported in this README
docs/         design and decisions
```

## Data and licences
- Bitext customer-support dataset: CDLA-Sharing-1.0. Not committed; downloaded on first run.
- WANDS (Wayfair): MIT. Not committed.
- CLINC150 out-of-scope examples: see the licence in the clinc/oos-eval repository. Not committed.
- Orders, customers and prices are synthetic.

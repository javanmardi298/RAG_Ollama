# Decisions

One entry per decision: what we chose, what else we considered, why.

## Stage 0

**Intent data: Bitext customer support.**
Considered ABCD, CLINC150, Banking77, MASSIVE, MultiWOZ/SGD. Bitext is the only public set with our exact intents (cancel_order, track_order, get_refund). Gaps (no out-of-scope, English only, single turn, template-generated) are covered by CLINC150 out-of-scope messages (stage 1), a German test set (stage 7) and scripted conversations (stage 6).

**Deduplication: normalized key (lowercase, placeholders masked, punctuation removed).**
Considered exact-only, MinHash/LSH, embedding similarity. Key-based is cheap and transparent and catches template variants. Revisit if dev scores look suspiciously high.

**Split: StratifiedGroupKFold, ~70/15/15, grouped by key.**
Random split leaks near-duplicates. Test split is locked until the end of each stage.

**Order data: synthetic SQLite with a fixed reference date and seed.**
Considered JSON, PostgreSQL, a mock REST API. SQLite gives real SQL, constraints and transactions with no server. FastAPI goes in front of it in stage 8.

**Policy: numbers only in configs/policy_rules.yaml; prose in policies/{en,de} checked by a test.**
Prevents the bot from saying one thing and doing another.

**Architecture: workflow outside, small agent loop only on the tool route.**
Considered one agent with all tools, and a framework. Fixed routes are easier to test and keep policy checks in code. A single-agent baseline is compared in stage 3.

## Version 2: LangChain / LangGraph

**Framework only at the edges.** Policy, tools, guardrails, decision and evaluation stay plain Python;
LangChain / LangGraph replace only the orchestration (chains, retrievers, the state graph). Both versions
run on the same tests and scenarios, so the comparison is fair and a framework upgrade cannot silently change business rules.

**Custom StateGraph over create_agent.** Considered create_agent with HumanInTheLoopMiddleware (kept as a baseline).
The custom graph keeps the router, RAG route, calibrated thresholds, identity-from-state and output checks explicit and testable.

**Confirmation via interrupt() in its own node.** On resume a node re-runs from the top, so nothing with side effects
happens before the interrupt; tools run in the next node (and are idempotent anyway).

**SQLite checkpointer.** Removes the in-memory session limitation of the plain API. Postgres for several hosts.

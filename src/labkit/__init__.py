"""labkit: small, framework-free building blocks for the project presets (RAG, agents, workflows, production).

The support agent in `support/` is one complete project. The presets (presets/*.yaml) describe other real-world
projects; most of what they need is already in `support/` (BM25, RRF, guardrails, evaluation, decisions,
experiments, monitoring) and the rest lives here, each piece with tests:

    loaders     read txt / md / html / pdf / docx into Documents
    chunking    fixed, recursive, by heading, Python code (AST)
    retrieval   one index over any Documents: BM25, dense, hybrid (RRF), MMR, reranker, multi-query rewriting
    metrics     recall@k, precision@k, MRR, nDCG (graded), field-level extraction F1, exact match
    structured  validate LLM JSON against a pydantic model, with one repair round
    sqlguard    allow only a single read-only SELECT on allowed tables, enforce a LIMIT
    workflow    steps with retries, idempotency keys, human approval and an audit log
    ops         response cache, usage/cost ledger, metered LLM wrapper, cheap-to-strong router, prompt registry
    graph       knowledge graph (triples, k-hop neighbourhood, paths, LLM triple extraction) for GraphRAG
    memory      conversation memory: recent turns + running summary + exact facts

Every module works without a model: the LLM, the encoder and the reranker are passed in.
"""

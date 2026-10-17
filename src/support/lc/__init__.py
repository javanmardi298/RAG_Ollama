"""LangChain / LangGraph versions of the project's stages.

The plain-Python modules in src/support stay the reference implementation.
Everything here reuses them (policy, tools, guardrails, decision, evaluation) and only
replaces the orchestration, so the two versions can be compared on the same tests and scenarios.
"""

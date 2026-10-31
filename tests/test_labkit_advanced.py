"""Research-driven labkit modules: agentic RAG, contextual retrieval, context packing, GEPA-style optimisation,
self-consistency, capability-based injection defence, pass^k. No model or network needed."""
import pytest

pytest.importorskip("pydantic")

from labkit import capsec, context, metrics, optimize, reasoning  # noqa: E402
from labkit.agentic_rag import AgenticRAG  # noqa: E402
from labkit.chunking import Chunk  # noqa: E402
from labkit.contextual import contextualize  # noqa: E402
from labkit.loaders import Document  # noqa: E402
from labkit.retrieval import Index  # noqa: E402

CH = [Chunk("returns#1", "returns", "Items can be returned within 30 days."),
      Chunk("custom#1", "custom", "Custom-made furniture cannot be returned."),
      Chunk("ship#1", "ship", "Delivery takes 3 to 5 days.")]
IDX = Index(CH)


def answer_from(question, chunks):
    return " ".join(c.text for c in chunks), [c.chunk_id for c in chunks]


def test_agentic_rag_corrects_a_failed_search_by_rewriting():
    rag = AgenticRAG(search=lambda q: IDX.search(q, k=2, mode="bm25"), answer=answer_from,
                     grade=lambda q, c: "return" in c.text.lower(),
                     rewrite=lambda q, tried: ["returned"] if "returned" not in tried else [])
    out = rag.run("send back sofa")
    kinds = [s.kind for s in out.trace]
    assert not out.abstained and out.rounds == 2 and "rewrite" in kinds
    assert set(out.citations) <= {"returns#1", "custom#1"}


def test_agentic_rag_abstains_when_nothing_supports_the_answer():
    rag = AgenticRAG(search=lambda q: IDX.search(q, k=2, mode="bm25"), answer=answer_from,
                     verify=lambda q, a, cs: False, rewrite=lambda q, tried: [], max_rounds=2)
    out = rag.run("returned items")
    assert out.abstained and out.trace[-1].kind == "abstain"


def test_agentic_rag_routes_direct_questions_without_retrieval():
    calls = []
    rag = AgenticRAG(search=lambda q: calls.append(q) or [], answer=answer_from,
                     route=lambda q: "direct", direct=lambda q: "hello!")
    assert rag.run("hi").answer == "hello!" and calls == []


def test_agentic_rag_drops_citations_it_never_retrieved():
    rag = AgenticRAG(search=lambda q: CH[:1], answer=lambda q, cs: ("x", ["returns#1", "made-up#9"]))
    assert rag.run("q").citations == ["returns#1"]


def test_contextual_retrieval_prefixes_context_and_caches(tmp_path):
    class LLM:
        n = 0

        def chat(self, messages):
            self.n += 1
            return type("R", (), {"content": "This is the exceptions part of the returns policy."})()

    doc = Document("policy", "Returns ... Custom-made furniture cannot be returned.", {"title": "Returns policy"})
    llm, cache = LLM(), tmp_path / "ctx.json"
    out = contextualize(llm, doc, [CH[1]], cache_file=cache)
    assert out[0].indexed_text.startswith("Returns policy. This is the exceptions part")
    contextualize(llm, doc, [CH[1]], cache_file=cache)
    assert llm.n == 1                                  # second indexing reused the cache


def test_context_pack_keeps_required_and_stable_prefix_first():
    pieces = [context.Piece("system", "rules " * 50, 100, required=True),
              context.Piece("chunks", "retrieved " * 200, 50, stable=False),
              context.Piece("history", "turn " * 100, 80),
              context.Piece("old_notes", "note " * 400, 10)]
    kept, rep = context.pack(pieces, budget_tokens=750)
    names = [p.name for p in kept]
    assert names[0] == "system" and names[-1] == "chunks" and "old_notes" in rep["dropped"]
    with pytest.raises(ValueError):
        context.pack([context.Piece("system", "x" * 4000, 1, required=True)], 100)


def test_tool_output_truncation_and_stale_clearing():
    t = context.truncate_tool_output("A" * 10_000 + "END", max_tokens=100, keep_tail=10)
    assert t.endswith("END") and "characters cut" in t and len(t) < 600
    msgs = [{"role": "tool", "content": f"r{i}"} for i in range(5)]
    out = context.clear_stale_tool_results(msgs, keep_last=2)
    assert [m["content"] for m in out][-2:] == ["r3", "r4"] and out[0]["content"].startswith("[tool result cleared")


def test_gepa_style_optimizer_selects_on_validation_and_penalises_bloat():
    # A toy "model": the prompt works for an example if it mentions the example's keyword.
    def evaluate(prompt, ex):
        ok = ex["kw"] in prompt
        return (1.0 if ok else 0.0), ("ok" if ok else f"missing rule about {ex['kw']}")

    def propose(prompt, failures):
        return prompt + " " + " ".join(sorted({f[0]["kw"] for f in failures}))

    train = [{"kw": "dates"}, {"kw": "units"}, {"kw": "trivia"}]          # "trivia" is train-only noise
    val = [{"kw": "dates"}, {"kw": "units"}]
    out = optimize.optimize("Answer.", train, val, evaluate, propose, budget=4)
    assert out["best"].val_score > out["seed"].val_score
    assert "dates" in out["best"].prompt and "units" in out["best"].prompt
    assert optimize.pareto_front(out["history"])


def test_self_consistency_and_best_of_n():
    answers = iter(["42", "42", "41", " 42 ", "40"])
    top, agree, _ = reasoning.self_consistency(lambda: next(answers), n=5)
    assert top == "42" and agree == 0.6
    gen = iter(["a", "bbb", "cc"])
    best, s, _ = reasoning.best_of_n(lambda: next(gen), score=len, n=3)
    assert best == "bbb" and s == 3


def test_capability_policy_blocks_values_from_untrusted_sources():
    pol = capsec.Policy({"send_money": {"recipient"}}, needs_confirmation={"send_money"})
    page = capsec.from_untrusted("attacker@evil.example", "web:evil.example")
    amount = capsec.from_user(50)
    with pytest.raises(capsec.PolicyViolation, match="recipient"):
        capsec.call_tool(pol, "send_money", lambda recipient, amount: "sent", {"recipient": page, "amount": amount}, True)
    mixed = capsec.derive(lambda a, b: a + b, capsec.from_user("lea"), page)     # taint propagates
    assert not mixed.trusted
    ok = capsec.call_tool(pol, "send_money", lambda recipient, amount: "sent",
                          {"recipient": capsec.from_user("lea@example.com"), "amount": amount}, confirmed=True)
    assert ok.value == "sent" and not ok.trusted
    with pytest.raises(capsec.PolicyViolation, match="confirmation"):
        pol.check("send_money", {"recipient": capsec.from_user("x")})


def test_pass_hat_k_is_harsher_than_pass_at_k():
    assert metrics.pass_hat_k(4, 4, 4) == 1.0 and metrics.pass_hat_k(4, 2, 2) == pytest.approx(1 / 6)
    assert metrics.pass_at_k(4, 2, 2) == pytest.approx(5 / 6)
    rep = metrics.reliability_report({"a": [True, True, True], "b": [True, False, True]})
    assert rep["pass^1"] == pytest.approx(5 / 6) and rep["pass^3"] == pytest.approx(0.5) and rep["pass@3"] == 1.0

"""labkit: the building blocks the presets need beyond the support agent. No model, network or data needed."""
import sqlite3

import numpy as np
import pytest

pytest.importorskip("pydantic")

from labkit import chunking, metrics, ops, sqlguard  # noqa: E402
from labkit.loaders import Document, drop_repeated_lines, html_to_text, load_file  # noqa: E402
from labkit.retrieval import Index  # noqa: E402
from labkit.structured import extract, parse_json  # noqa: E402
from labkit.workflow import Step, Workflow  # noqa: E402


# ---------- loaders ----------

def test_html_keeps_headings_and_drops_scripts():
    text = html_to_text("<h1>Returns</h1><script>x=1</script><p>Within <b>30</b> days&nbsp;only.</p>")
    assert text.startswith("# Returns") and "x=1" not in text and "30 days" in text


def test_repeated_headers_and_page_numbers_are_removed():
    pages = [f"ACME Handbook\nreal content {i}\nPage {i}" for i in range(1, 6)]
    cleaned = drop_repeated_lines(pages)
    assert all("ACME Handbook" not in p and "Page" not in p for p in cleaned)
    assert cleaned[2].strip() == "real content 3"


def test_load_markdown_file(tmp_path):
    (tmp_path / "policy.md").write_text("# Title\n\nSome-\nthing here.", encoding="utf-8")
    [doc] = load_file(tmp_path / "policy.md")
    assert doc.doc_id == "policy" and "Something here." in doc.text


# ---------- chunking ----------

DOC = Document("returns", "# Returns\n\nYou can return items within 30 days.\n\n## Exceptions\n\nCustom-made items cannot be returned.",
               {"title": "Policy"})


def test_heading_chunks_carry_their_path():
    chunks = chunking.headings(DOC)
    assert [c.meta["section"] for c in chunks] == ["Returns", "Exceptions"]
    assert chunks[1].meta["context"] == "Policy > Returns > Exceptions"
    assert chunks[1].indexed_text.startswith("Policy > Returns > Exceptions.")


def test_fixed_chunks_overlap_and_cover_everything():
    doc = Document("d", " ".join(f"w{i}" for i in range(100)))
    chunks = chunking.fixed(doc, size=30, overlap=10)
    assert chunks[0].text.split()[-10:] == chunks[1].text.split()[:10]
    assert chunks[-1].text.split()[-1] == "w99"
    with pytest.raises(ValueError):
        chunking.fixed(doc, size=10, overlap=10)


def test_recursive_respects_max_words():
    doc = Document("d", "\n\n".join(" ".join(["word"] * 40) + "." for _ in range(6)))
    assert all(len(c.text.split()) <= 50 for c in chunking.recursive(doc, max_words=50))


def test_python_code_chunks_are_whole_functions():
    src = "import os\n\n@cache\ndef a(x):\n    '''Add one.'''\n    return x + 1\n\nclass B:\n    def m(self):\n        pass\n"
    chunks = chunking.python_code(Document("mod", src, {"title": "mod.py"}))
    assert [c.meta["symbol"] for c in chunks] == ["a", "B"]
    assert chunks[0].text.startswith("@cache") and chunks[0].meta["docstring"] == "Add one."


# ---------- retrieval ----------

class ToyEncoder:
    """Bag of words over a fixed vocabulary; enough to test dense/hybrid/MMR logic."""
    vocab = ["return", "refund", "money", "back", "ship", "delivery", "days", "custom"]

    def encode(self, texts, normalize_embeddings=True):
        out = np.array([[t.lower().count(w) for w in self.vocab] for t in texts], float) + 1e-6
        return out / np.linalg.norm(out, axis=1, keepdims=True)


CHUNKS = [chunking.Chunk("r1", "returns", "Return items within 30 days.", {"lang": "en"}),
          chunking.Chunk("r2", "refunds", "Refund money back to your card.", {"lang": "en"}),
          chunking.Chunk("s1", "shipping", "Delivery takes 3 days.", {"lang": "en"}),
          chunking.Chunk("r1de", "returns", "Rücksendung innerhalb von 30 Tagen.", {"lang": "de"})]


def test_bm25_hybrid_and_metadata_filter():
    idx = Index(CHUNKS, encoder=ToyEncoder())
    assert idx.search("return items", k=1, mode="bm25")[0].chunk_id == "r1"
    assert idx.search("money back", k=1, mode="hybrid")[0].chunk_id == "r2"
    de = idx.search("30", k=3, mode="bm25", where=lambda c: c.meta["lang"] == "de")
    assert [c.chunk_id for c in de] == ["r1de"]        # filter applied before ranking


def test_reranker_reorders_top_candidates():
    idx = Index(CHUNKS)
    rerank = lambda q, texts: [1.0 if "Delivery" in t else 0.0 for t in texts]  # noqa: E731
    assert idx.search("days", k=1, mode="bm25", reranker=rerank)[0].chunk_id == "s1"


def test_dense_without_encoder_is_an_error():
    with pytest.raises(ValueError):
        Index(CHUNKS).search("x", mode="dense")


# ---------- metrics ----------

def test_retrieval_metrics():
    assert metrics.recall_at_k(["a", "b", "c"], {"a", "c"}, 2) == 0.5
    assert metrics.mrr(["x", "a"], {"a"}) == 0.5
    assert metrics.ndcg_at_k(["a", "b"], {"a": 2, "b": 1}, 2) == pytest.approx(1.0)
    assert metrics.ndcg_at_k(["b", "a"], {"a": 2, "b": 1}, 2) < 1.0


def test_extraction_report_normalises_values():
    gold = {"vendor": "ACME GmbH", "total": "1.234,50", "date": "2026-10-01"}
    pred = {"vendor": "acme  gmbh", "total": "1234.5", "date": "2026-10-02", "iban": "DE00"}
    r = metrics.extraction_report([(pred, gold)])
    assert r["per_field"]["vendor"] == 1.0 and r["per_field"]["total"] == 1.0
    assert r["per_field"]["date"] == 0.0 and r["exact_match"] == 0.0
    assert r["precision"] == pytest.approx(2 / 4) and r["recall"] == pytest.approx(2 / 3)


# ---------- structured ----------

def test_structured_extract_repairs_once():
    from pydantic import BaseModel, model_validator

    class Invoice(BaseModel):
        net: float
        vat: float
        total: float

        @model_validator(mode="after")
        def adds_up(self):
            if abs(self.net + self.vat - self.total) > 0.01:
                raise ValueError("net + vat must equal total")
            return self

    class LLM:
        def __init__(self):
            self.replies = ['{"net": 100, "vat": 19, "total": 120}', '```json\n{"net": 100, "vat": 19, "total": 119}\n```']
            self.seen = []

        def chat(self, messages):
            self.seen.append(messages)
            return type("R", (), {"content": self.replies.pop(0)})()

    llm = LLM()
    out = extract(llm, Invoice, "extract")
    assert out.ok and out.value.total == 119 and out.attempts == 2
    assert "net + vat must equal total" in llm.seen[1][-1]["content"]
    assert parse_json('Here: {"a": 1} thanks') == {"a": 1}


# ---------- sqlguard ----------

@pytest.fixture()
def shopdb(tmp_path):
    path = tmp_path / "s.db"
    con = sqlite3.connect(path)
    con.executescript("CREATE TABLE orders (id INT, total REAL); CREATE TABLE secrets (pw TEXT);"
                      "INSERT INTO orders VALUES (1, 10), (2, 30);")
    con.commit(); con.close()
    return str(path)


@pytest.mark.parametrize("sql, problem", [
    ("DELETE FROM orders", "only SELECT"),
    ("SELECT * FROM orders; DROP TABLE orders", "multiple statements"),
    ("SELECT pw FROM secrets", "table not allowed"),
    ("SELECT * FROM orders o JOIN secrets s ON 1=1", "table not allowed"),
    ("WITH x AS (SELECT 1) UPDATE orders SET total = 0", "forbidden keyword"),
])
def test_sqlguard_rejects(sql, problem):
    v = sqlguard.check_sql(sql, {"orders"})
    assert not v.ok and any(problem in p for p in v.problems)


def test_sqlguard_allows_select_and_caps_limit(shopdb):
    assert sqlguard.check_sql("SELECT * FROM orders", {"orders"}).sql.endswith("LIMIT 200")
    assert sqlguard.check_sql("select * from orders limit 9999", {"orders"}, max_rows=50).sql.endswith("limit 50")
    assert sqlguard.check_sql("SELECT 'it''s' AS t FROM orders LIMIT 5000", {"orders"}).sql.endswith("LIMIT 200")
    assert sqlguard.check_sql("SELECT 'drop table' AS t FROM orders", {"orders"}).ok   # keyword inside a string
    assert sqlguard.check_sql("WITH big AS (SELECT * FROM orders) SELECT * FROM big", {"orders"}).ok
    con = sqlguard.readonly_connection(shopdb)
    out = sqlguard.run_guarded(con, "SELECT SUM(total) AS s FROM orders", {"orders"})
    assert out["ok"] and out["rows"] == [{"s": 40.0}]
    with pytest.raises(sqlite3.OperationalError):
        con.execute("DELETE FROM orders")                       # the connection itself is read-only
    assert sqlguard.execution_match(con, "SELECT id FROM orders WHERE total > 5", "SELECT id FROM orders")


# ---------- workflow ----------

def test_workflow_approval_retry_idempotency_and_resume(tmp_path):
    calls = {"pay": 0, "flaky": 0}

    def flaky(ctx):
        calls["flaky"] += 1
        if calls["flaky"] < 2:
            raise TimeoutError("llm timeout")
        return {"category": "office"}

    def pay(ctx):
        calls["pay"] += 1
        return {"paid": ctx["amount"]}

    def steps():
        return [Step("classify", flaky, retries=2),
                Step("approve", approval=lambda c: c["amount"] > 500),
                Step("pay", pay, idempotency_key=lambda c: f"pay:{c['invoice']}")]

    wf = Workflow("invoice", steps(), db=str(tmp_path / "wf.db"), sleep=lambda s: None)
    run = wf.start({"invoice": "INV-1", "amount": 900})
    assert wf.state(run)["status"] == "waiting_approval" and wf.state(run)["step"] == "approve"
    assert wf.decide(run, True, by="lea") == "done" and calls["pay"] == 1
    assert wf.state(run)["ctx"]["paid"] == 900

    # the same invoice again (e.g. a duplicate email): payment is NOT repeated
    wf2 = Workflow("invoice", steps(), db=str(tmp_path / "wf.db"), sleep=lambda s: None)
    run2 = wf2.start({"invoice": "INV-1", "amount": 100})
    assert wf2.state(run2)["status"] == "done" and calls["pay"] == 1
    events = [e["event"] for e in wf2.audit(run2)]
    assert "idempotent_skip" in events
    assert [e["event"] for e in wf.audit(run)].count("error") == 1      # one retry recorded


def test_workflow_rejection_and_failure(tmp_path):
    wf = Workflow("w", [Step("approve", approval=lambda c: True), Step("x", lambda c: {})], sleep=lambda s: None)
    run = wf.start({})
    assert wf.decide(run, False, by="boss") == "rejected"
    with pytest.raises(ValueError):
        wf.decide(run, True, by="boss")
    boom = Workflow("w", [Step("x", lambda c: 1 / 0, retries=1)], sleep=lambda s: None)
    r = boom.start({})
    assert boom.state(r)["status"] == "failed"


# ---------- ops ----------

def test_metered_llm_caches_and_records_cost():
    class LLM:
        model, temperature, n = "m", 0.0, 0

        def chat(self, messages, **kw):
            self.n += 1
            return type("R", (), {"content": "answer " * 10, "tool_calls": []})()

    llm, ledger = LLM(), ops.Ledger()
    m = ops.Metered(llm, ledger, ops.Cache(), ops.Price(1.0, 2.0), feature="faq")
    msgs = [{"role": "user", "content": "x" * 400}]
    m.chat(msgs); m.chat(msgs)
    assert llm.n == 1
    [row] = ledger.summary()
    assert row["calls"] == 2 and row["cache_hit_rate"] == 0.5 and row["tokens_in"] == 100 and row["cost"] > 0


def test_prompt_registry_versions_by_content():
    reg = ops.PromptRegistry()
    v1 = reg.register("answer", "Answer {question} from {sources}.")
    v2 = reg.register("answer", "Answer briefly: {question}. Sources: {sources}")
    assert v1 != v2 and reg.versions("answer") == [v1, v2]
    text, v = reg.render("answer", question="q", sources="s")
    assert v == v2 and text.startswith("Answer briefly")
    with pytest.raises(KeyError):
        reg.render("answer", v1, question="q")


# ---------- graph, memory, router, multi-query ----------

def test_graph_multi_hop_path_and_entities():
    from labkit.graph import Graph, Triple
    g = Graph([Triple("Oak Table", "made_by", "Holz AG", "c1"), Triple("Holz AG", "located_in", "Germany", "c2"),
               Triple("Oak Table", "has_defect", "wobbly leg", "c3")])
    g.alias("Holz Aktiengesellschaft", "Holz AG")
    chain = g.path("oak table", "germany")
    assert [t.r for t in chain] == ["made_by", "located_in"] and [t.source for t in chain] == ["c1", "c2"]
    assert len(g.neighbourhood("Holz Aktiengesellschaft", hops=1)) == 2
    assert g.entities_in("Where is the maker of the Oak Table based?") == ["oak table"]
    assert g.path("oak table", "nowhere") is None


def test_memory_keeps_facts_and_summarises_old_turns():
    from labkit.memory import Memory
    m = Memory(keep_turns=2, summarize=lambda old, dropped: (old + f" {len(dropped)} turns").strip())
    m.remember("order_id", "HH-100042")
    for i in range(5):
        m.add("user", f"message {i}")
    ctx = m.context("You are support.")
    assert len(ctx) == 3 and "order_id=HH-100042" in ctx[0]["content"] and "Earlier" in ctx[0]["content"]
    assert ctx[-1]["content"] == "message 4"


def test_router_escalates_only_when_needed():
    reply = lambda text: type("R", (), {"content": text})()  # noqa: E731

    class Cheap:
        def chat(self, messages, **kw):
            return reply("unsure" if "hard" in messages[0]["content"] else "fine")

    class Strong:
        def chat(self, messages, **kw):
            return reply("strong")

    r = ops.Router(Cheap(), Strong(), accept=lambda rep: rep.content != "unsure")
    assert r.chat([{"role": "user", "content": "easy"}]).content == "fine"
    assert r.chat([{"role": "user", "content": "hard"}]).content == "strong"
    assert r.escalation_rate == 0.5


def test_multi_query_finds_synonym_misses():
    from labkit.retrieval import multi_query_search
    idx = Index(CHUNKS)
    assert [c.chunk_id for c in idx.search("send back", k=3, mode="bm25")] == ["r2"]   # BM25 alone misses the synonym
    out = multi_query_search(idx, "send back", lambda q: ["return items", "return the product"], k=1, mode="bm25")
    assert out[0].chunk_id == "r1"

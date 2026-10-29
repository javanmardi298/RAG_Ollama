SAMPLE = "# Returns\n\n## Return window\nYou can return   items\nwithin 30 days.\n\n## Exceptions\nCustom items cannot be returned.\n"


def check_one_chunk_per_section(m):
    """one chunk per ## section"""
    cs = m.chunk_markdown(SAMPLE, "returns")
    assert len(cs) == 2, f"expected 2 chunks, got {len(cs)}"


def check_heading_path(m):
    """heading keeps 'Title > Section'"""
    cs = m.chunk_markdown(SAMPLE, "returns")
    assert cs[0]["heading"] == "Returns > Return window", f"got {cs[0]['heading']!r}"
    assert cs[1]["heading"] == "Returns > Exceptions", f"got {cs[1]['heading']!r}"


def check_text_is_clean(m):
    """text has no heading line and normalised spaces"""
    cs = m.chunk_markdown(SAMPLE, "returns")
    assert cs[0]["text"] == "You can return items within 30 days.", f"got {cs[0]['text']!r}"


def check_ids(m):
    """ids are doc_id#0, doc_id#1, ... and doc_id is stored"""
    cs = m.chunk_markdown(SAMPLE, "returns")
    assert [c["id"] for c in cs] == ["returns#0", "returns#1"], [c["id"] for c in cs]
    assert all(c["doc_id"] == "returns" for c in cs)


def check_no_empty_chunks(m):
    """a heading without text makes no chunk (ids stay consecutive)"""
    cs = m.chunk_markdown("# Title\n## A\n\n## B\nbody\n", "d")
    assert [c["text"] for c in cs] == ["body"], cs
    assert cs[0]["id"] == "d#0", cs[0]["id"]


def check_real_faq(m):
    """works on the real FAQ pages"""
    from learn.data import faq_docs
    total = sum(len(m.chunk_markdown(t, n)) for n, t in faq_docs().items())
    assert total >= 12, f"only {total} chunks from the FAQ pages"

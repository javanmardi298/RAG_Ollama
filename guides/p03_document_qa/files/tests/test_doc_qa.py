from doc_qa import BM25, answer, chunk, chunk_all, enough_evidence, evaluate, load_documents, load_questions, numbers_grounded


def test_all_formats_load_with_headings():
    docs = load_documents()
    assert set(docs) == {"employee_handbook", "it_security", "travel_policy", "expenses"}
    assert docs["it_security"].startswith("# IT Security Policy") and "## Passwords" in docs["it_security"]
    assert docs["travel_policy"].startswith("# Travel Policy") and "## Hotels" in docs["travel_policy"]


def test_long_sections_become_overlapping_windows():
    text = "# T\n## S\n" + " ".join(f"w{i}" for i in range(200))
    cs = chunk(text, "d", max_words=80, overlap=20)
    assert len(cs) == 3 and cs[0]["text"].split()[-20:] == cs[1]["text"].split()[:20] and cs[0]["heading"] == "T > S"


def test_numbers_must_come_from_the_source():
    src = [{"id": "e#0", "text": "Submit expenses within 30 days."}]
    assert numbers_grounded("Within 30 days [e#0]", src) and not numbers_grounded("Within 60 days [e#0]", src)


def test_wrong_number_and_fake_citation_are_rejected():
    index = BM25(chunk_all(load_documents()))
    assert answer("when do I have to submit expenses", index, lambda q, cs: f"Within 60 days [{cs[0]['id']}]")["reason"] == "number not in the source"
    assert answer("when do I have to submit expenses", index, lambda q, cs: "Within 30 days [policy#9]")["reason"] == "no valid citation"


def test_evaluation_on_the_question_set():
    r = evaluate(load_questions(), BM25(chunk_all(load_documents())))
    assert r["answered_unanswerable"] == 0 and r["correct_source"] >= 13
    assert not enough_evidence("what is the CEO's phone number", {"heading": "Probation", "text": "The probation period is 6 months."})

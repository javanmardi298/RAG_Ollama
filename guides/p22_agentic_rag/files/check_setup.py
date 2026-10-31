"""Run once after installing: checks Python, the data and one full agent run."""
import sys

from agentic_rag import chunk_all, load_data, make_search, run_agent

print("Python", sys.version.split()[0])
docs, questions = load_data()
chunks = chunk_all(docs)
print(len(chunks), "chunks,", len(questions), "questions")
search = make_search(chunks)
print("answerable:", run_agent("how do I claim the warranty", search)["citations"])
print("unanswerable:", "ABSTAIN" if run_agent("what is the CEO's phone number", search)["abstained"] else "answered")
print("setup ok")

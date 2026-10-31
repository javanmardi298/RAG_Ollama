"""Run once after installing: checks Python, the data file and the core functions."""
import sys

from faq_search import BM25, chunk_all, load_data

print("Python", sys.version.split()[0])
docs, questions = load_data()
chunks = chunk_all(docs)
print(len(docs), "documents,", len(chunks), "chunks,", len(questions), "questions")
bm = BM25([c["text"] for c in chunks])
print("BM25 top hit for 'refund money':", chunks[bm.search("refund money", k=1)[0]]["id"])
print("setup ok")

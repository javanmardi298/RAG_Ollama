"""Run once after installing: checks Python, the documents in all formats and one answer."""
import sys

from doc_qa import BM25, answer, chunk_all, load_documents

print("Python", sys.version.split()[0])
docs = load_documents()
for name, text in docs.items():
    print(f"{name:18s} {len(text.split()):4d} words, first line: {text.splitlines()[0]}")
index = BM25(chunk_all(docs))
print(answer("how long must my password be", index)["answer"])
print("setup ok")

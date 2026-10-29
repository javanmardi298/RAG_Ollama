## Hint 1
هیچ منطق تازه‌ای در این گام نیست؛ وصل‌کاری است. `labkit.agentic_rag` همه‌ی توابع `llm_*` را دارد؛ فقط باید آن‌ها را درست به `AgenticRAG` بدهی. مدل فقط از طریق `llm.chat` و `llm.json` استفاده می‌شود.

## Hint 2
`to_chunks`: یک list comprehension با `Chunk(chunk_id=..., doc_id=..., text=..., meta={"heading": ...})`. `make_answer`: همان منطق prompt و ارجاع p01 گام ۵ ولی با `c.chunk_id` و `c.text`. `direct`: یک lambda که `llm.chat([{"role": "user", "content": q}]).content` را برمی‌گرداند.

## Hint 3
`AgenticRAG(search=search, answer=make_answer(llm), grade=llm_grader(llm), rewrite=llm_rewriter(llm), verify=llm_verifier(llm), route=llm_router(llm), direct=lambda q: ..., max_rounds=max_rounds)`. حل کامل: `python -m learn solution p22_agentic_rag 5`.

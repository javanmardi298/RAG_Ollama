## Hint 1
سه تابع کوچک و مستقل‌اند. اول فقط prompt را بساز و چاپ کن تا ببینی مدل چه چیزی می‌بیند. بعد استخراج ارجاع را جدا امتحان کن، و در آخر آن‌ها را در `answer` به هم وصل کن.

## Hint 2
`re.findall(r"\[([^\]]+)\]", text)` همه‌ی محتواهای داخل کروشه را می‌دهد. فیلتر کن با `in allowed_ids` و تکراری‌ها را با چک `not in seen` حذف کن. در `answer` اول `if not chunks: return {...}` و بعد `llm.chat(...).content`.

## Hint 3
`sources = "\n".join(f"[{c['id']}] {c['heading']}: {c['text']}" for c in chunks)`؛ user = `f"Sources:\n{sources}\n\nQuestion: {question}"`. در `answer`: اگر `cites` خالی بود امتناع. حل کامل: `python -m learn solution p01_faq_search 5`.

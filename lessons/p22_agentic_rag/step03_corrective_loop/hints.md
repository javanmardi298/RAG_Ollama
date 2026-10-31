## Hint 1
دو تابع جدا: `rewrite` فقط فهرستی از query های تازه می‌سازد (هیچ جست‌وجویی نمی‌کند)؛ `agentic_search` حلقه است. حلقه را روی کاغذ با شبه‌کد بالای درس بنویس.

## Hint 2
در `rewrite` کاندیدها را در یک لیست بساز و با شرط `cand and cand not in tried and cand not in out` فیلتر کن. در حلقه: `while queries and rounds < max_rounds`; بعد از پردازش queryهای این دور، اگر `len(relevant) >= min_relevant` با `break` خارج شو؛ وگرنه `queries = rewrite(...)`.

## Hint 3
`relevant.setdefault(c["id"], c)` تکرار را حذف می‌کند. `tried.append(q)` را قبل از `search` انجام بده. ساختار کامل در درس و `python -m learn solution p22_agentic_rag 3`.

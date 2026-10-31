## Hint 1
هر معیار یک سؤال ساده را جواب می‌دهد. recall: «چند درصد درست‌ها در k تای اول‌اند؟» MRR: «اولین درست در چندمین جایگاه است؟».

## Hint 2
recall: `len(set(ranked[:k]) & relevant) / len(relevant)`. MRR: روی `enumerate(ranked)` بگرد و با اولین `doc in relevant` مقدار `1 / (i + 1)` را برگردان. در `evaluate` یکتا کردن با `list(dict.fromkeys(ranking))` ترتیب را نگه می‌دارد.

## Hint 3
ساختار `evaluate`: حلقه روی سؤال‌ها؛ `if not q["relevant"]: continue`؛ `ranked = list(dict.fromkeys(search(q["question"])))`؛ دو لیست `rec` و `rr` پر کن؛ اگر `r == 0` سؤال را در `misses` بگذار؛ میانگین‌ها را با تقسیم بر `n` (و محافظت از `n == 0`) برگردان. کلید recall باید `f"recall@{k}"` باشد. حل کامل: `python -m learn solution p01_faq_search 3`.

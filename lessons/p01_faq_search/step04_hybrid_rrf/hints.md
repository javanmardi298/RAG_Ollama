## Hint 1
تکه‌ی اول: سه‌حرفی‌ها. هر کلمه را با فاصله اول و آخر بپوشان (`f" {w} "`) و پنجره‌های سه‌تایی بگیر. تکه‌ی دوم: Jaccard یعنی اشتراک تقسیم بر اجتماع دو مجموعه.

## Hint 2
`rrf`: یک دیکشنری امتیاز؛ برای هر فهرست و هر `(rank, doc)` با `enumerate(ranking, start=1)` مقدار `1 / (k + rank)` را اضافه کن؛ بعد با `sorted(score, key=lambda d: (-score[d], d))` مرتب کن. `hybrid` فقط دو فهرست می‌سازد و به `rrf` می‌دهد.

## Hint 3
`rrf([bm25.search(query, k=len(texts)), trigram_rank(query, texts)])[:top]`. برای trigram: `q = trigrams(query)`؛ برای هر متن `len(q & g) / len(q | g)`؛ مرتب‌سازی `(-sims[i], i)` و فیلتر `sims[i] > 0`. حل کامل: `python -m learn solution p01_faq_search 4`.

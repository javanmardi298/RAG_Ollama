# p01 — جست‌وجوی FAQ از صفر (chunk → BM25 → hybrid → جواب با ارجاع)

**سطح:** پایه · **زمان:** ۴ تا ۶ ساعت · **نیاز:** Python (بدون GPU، بدون مدل زبانی؛ گام ۵ اختیاری با مدل واقعی)

## چه می‌سازی
یک سیستم پرسش‌وپاسخ برای صفحه‌های FAQ یک فروشگاه: سؤال مشتری ← پیدا کردن تکه‌ی درست ← جواب با ارجاع، یا «نمی‌دانم» وقتی شاهد نیست. همه‌ی اجزا را خودت می‌نویسی تا بدانی هر کتابخانه‌ای زیرِ پوشش چه می‌کند.

## گام‌ها
| گام | موضوع | چه می‌نویسی | تست |
|---|---|---|---|
| [۱](step01_chunk_markdown/lesson.md) | chunking | `chunk_markdown` | ۶ بررسی |
| [۲](step02_bm25/lesson.md) | BM25 | `tokenize`، `BM25` | ۶ بررسی |
| [۳](step03_metrics/lesson.md) | ارزیابی | recall@k، MRR، `evaluate` | ۶ بررسی |
| [۴](step04_hybrid_rrf/lesson.md) | hybrid | trigram، `rrf`، `hybrid` | ۶ بررسی |
| [۵](step05_answer_citations/lesson.md) | جواب و امتناع | prompt، ارجاع، `answer` | ۶ بررسی |

## چطور کار کنیم
```bash
python -m learn start p01_faq_search     # درس گام اول + ساخت فایل پاسخ در work/
# فایل work/p01_faq_search/step01_chunk_markdown/answer.py را کامل کن
python -m learn check p01_faq_search     # تست خودکار
python -m learn hint p01_faq_search      # گیر کردی؟ راهنمایی (سه سطح)
python -m learn quiz p01_faq_search 1    # امتحان کوتاه
```
یا در Jupyter/Colab: `lessons/p01_faq_search/p01_faq_search.ipynb`.

## بعد از این پروژه
- با `labkit.retrieval.Index` همین کار را با embedding و reranker واقعی تکرار کن؛ اسکلت: `python -m support.panel.presets scaffold p01_faq_search`.
- [پریست p01 در نقشه‌ی راه](../../presets/projects/p01_faq_search.yaml) سؤال‌های مصاحبه، داده‌ی بزرگ‌تر و نسخه‌ی پیشرفته را دارد.
- درس بعد: [p22 — Agentic RAG](../p22_agentic_rag/README.md).

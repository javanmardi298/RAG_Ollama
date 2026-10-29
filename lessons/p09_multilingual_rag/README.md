# RAG چندزبانه (فارسی، انگلیسی، آلمانی)
_Multilingual and cross-lingual RAG (FA / EN / DE)_ · سطح میانی · 2–3 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p09_multilingual_rag` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
شرکت‌های چندملیتی و دولتی: سند به یک زبان، سؤال به زبان دیگر؛ پشتیبانی فارسی‌زبان روی مستندات انگلیسی.
## مسئله
توکن‌سازی فارسی (نیم‌فاصله، ی/ي و ک/ك عربی)، مدل‌های embedding انگلیسی‌محور، و سؤال و سند به زبان‌های مختلف.
## هدف
بازیابی هم‌زبان و بین‌زبانی را برای هر زبان جدا اندازه بگیری و با نرمال‌سازی و ترجمه‌ی query بهتر کنی.

## پیش‌نیاز
- [p01_faq_search](../p01_faq_search/README.md)

## داده
- [MIRACL](https://huggingface.co/datasets/miracl/miracl) · Apache 2.0 · ۱۸ زبان شامل فارسی، آلمانی و انگلیسی، با qrels انسانی
- سیاست‌های EN/DE همین repo (`policies/`) · سؤال فارسی روی سند آلمانی بنویس

## قطعه‌ها
- `chunking` chunking (fixed / recursive / heading): labkit.chunking
- `bm25` BM25: support.rag.BM25
- `dense` dense retrieval (embedding): labkit.retrieval.Index
- `hybrid_rrf` hybrid با RRF: support.rag.rrf
- `query_rewriting` بازنویسی query / multi-query: labkit.retrieval.multi_query_search
- `metadata_filter` فیلتر metadata (زبان، دسترسی، تاریخ): labkit.retrieval.Index.search
- `retrieval_metrics` recall@k، MRR، nDCG: labkit.metrics
- `citations` جواب با ارجاع به منبع: support.rag.answer_question
- `llm_judge` LLM judge اعتبارسنجی‌شده (kappa): support.evaluation

## گام 1: نرمال‌سازی متن فارسی
**یاد بگیر**
- ی/ي، ک/ك، نیم‌فاصله (ZWNJ)، اعداد فارسی/عربی
- اثر نرمال‌سازی روی BM25

**بساز**
- تابع normalize قبل از index و query
- BM25 با و بدون نرمال‌سازی روی MIRACL-fa

**بسنج:** recall@10 فارسی قبل و بعد

**دام:** اگر سند را نرمال کنی و query را نه، هیچ چیز پیدا نمی‌شود.

## گام 2: embedding چندزبانه
**یاد بگیر**
- فضای برداری مشترک بین زبان‌ها
- چرا مدل انگلیسی روی فارسی شکست می‌خورد

**بساز**
- دو مدل embedding را روی هر سه زبان مقایسه کن

**بسنج:** recall@10 به تفکیک زبان

**دام:** میانگین روی همه‌ی زبان‌ها افت یک زبان را پنهان می‌کند؛ همیشه به تفکیک گزارش کن.

## گام 3: بازیابی بین‌زبانی
**یاد بگیر**
- سؤال فارسی، سند آلمانی: dense مستقیم یا ترجمه‌ی query
- multi-query با ترجمه

**بساز**
- multi_query_search با ترجمه‌ی query به زبان سندها

**بسنج:** recall@10 بین‌زبانی برای هر روش

**دام:** ترجمه‌ی ماشینی اسم‌های خاص را خراب می‌کند؛ نمونه را دستی چک کن.

## گام 4: جواب به زبان کاربر با citation به زبان سند
**یاد بگیر**
- تولید به زبان کاربر، استناد به منبع اصلی

**بساز**
- prompt با زبان هدف؛ citation به chunk اصلی
- judge برای «زبان درست»

**بسنج:** نرخ جواب به زبان درست، fact rate

**دام:** مدل‌های کوچک وسط جواب زبان را عوض می‌کنند.

## معیارها
- recall@10 per language
- cross-lingual recall@10
- answer-in-user-language rate

## سؤال مصاحبه
- چالش‌های فارسی در بازیابی؟
- بین‌زبانی را چطور ارزیابی کردی؟
- چرا گزارش به تفکیک زبان؟

## نسخه‌ی پیشرفته
- fine-tune embedding روی جفت فارسی-انگلیسی
- تشخیص زبان با fastText lid
- ارزیابی گویش‌ها و فینگلیش

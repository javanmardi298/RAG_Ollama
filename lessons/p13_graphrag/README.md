# GraphRAG: پرسش چندپرشی با گراف دانش
_GraphRAG: multi-hop QA over a knowledge graph_ · سطح پیشرفته · 3 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p13_graphrag` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
زنجیره‌ی تأمین، داروسازی، هوش تجاری: «کدام تأمین‌کننده‌ی محصولی که بیشترین مرجوعی را دارد آلمانی است؟» جواب در یک سند نیست.
## مسئله
vector RAG قطعه‌های شبیه سؤال را می‌آورد، نه زنجیره‌ی واقعیت‌ها را؛ استخراج triple خطا دارد؛ موجودیت‌ها نام‌های مختلف دارند.
## هدف
گراف از اسناد بسازی، بازیابی گرافی و vector را روی سؤال‌های چندپرشی مقایسه کنی، و مسیر استدلال را به‌عنوان توضیح نشان دهی.

## پیش‌نیاز
- [p03_document_qa](../p03_document_qa/README.md)
- [p10_research_agent](../p10_research_agent/README.md)

## داده
- [MuSiQue / 2WikiMultiHopQA](https://github.com/StonyBrookNLP/musique) · CC BY 4.0 · سؤال‌های واقعاً چندپرشی
- shop.db + WANDS · گراف محصول ← تأمین‌کننده ← کشور ← مرجوعی؛ سؤال و جواب با SQL

## قطعه‌ها
- `knowledge_graph` گراف دانش (triples، multi-hop): labkit.graph
- `structured_output` خروجی ساختاریافته + اعتبارسنجی + repair: labkit.structured
- `chunking` chunking (fixed / recursive / heading): labkit.chunking
- `hybrid_rrf` hybrid با RRF: support.rag.rrf
- `retrieval_metrics` recall@k، MRR، nDCG: labkit.metrics
- `citations` جواب با ارجاع به منبع: support.rag.answer_question
- `llm_judge` LLM judge اعتبارسنجی‌شده (kappa): support.evaluation
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger

## گام 1: استخراج triple
**یاد بگیر**
- واژگان رابطه‌ی ثابت
- provenance: هر triple از کدام chunk

**بساز**
- labkit.graph.extract_triples با relations ثابت
- دقت استخراج روی ۵۰ chunk برچسب‌خورده

**بسنج:** precision/recall triple

**دام:** رابطه‌های آزاد («ساخته‌شده توسط»، «تولیدکننده‌اش»، «made by») گراف را بی‌استفاده می‌کند.

## گام 2: entity resolution
**یاد بگیر**
- یک موجودیت، چند نام
- alias و نرمال‌سازی

**بساز**
- Graph.alias برای نام‌های تکراری؛ ادغام با شباهت embedding

**بسنج:** تعداد موجودیت قبل و بعد، دقت ادغام

**دام:** ادغام بیش از حد دو شرکت متفاوت را یکی می‌کند.

## گام 3: بازیابی گرافی
**یاد بگیر**
- موجودیت‌های سؤال ← همسایگی k-پرشی ← context
- path به‌عنوان توضیح

**بساز**
- entities_in + neighbourhood/path
- hybrid: گراف + chunkهای منبع tripleها

**بسنج:** دقت جواب روی سؤال‌های ۲ و ۳ پرشی

**دام:** همسایگی ۳-پرشی در گراف شلوغ هزاران triple است؛ محدود و رتبه‌بندی کن.

## گام 4: مقایسه با vector RAG
**یاد بگیر**
- کجا گراف برنده است و کجا بازنده

**بساز**
- همان سؤال‌ها با RAG معمولی؛ paired bootstrap

**بسنج:** دقت به تفکیک تعداد پرش، هزینه‌ی ساخت گراف

**دام:** هزینه‌ی ساخت گراف (LLM روی همه‌ی اسناد) را در مقایسه بیاور.

## معیارها
- triple precision/recall
- multi-hop answer accuracy
- path validity
- build cost

## سؤال مصاحبه
- GraphRAG کی ارزش دارد؟
- entity resolution را چطور انجام دادی؟
- هزینه‌ی ساخت گراف چقدر بود؟

## نسخه‌ی پیشرفته
- Microsoft GraphRAG (community summaries)
- Text-to-Cypher با همان ایده‌ی sqlguard
- گراف زمانی (رابطه‌ها با تاریخ)

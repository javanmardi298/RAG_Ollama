# Contextual Retrieval و RAG چندوجهی (ColPali) روی PDF واقعی
_Contextual retrieval and multimodal RAG (ColPali) on real PDFs_ · سطح میانی · 2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p23_contextual_multimodal_rag` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
گزارش‌های مالی، دفترچه‌ی فنی، اسلاید: جدول و نمودار و chunk بی‌زمینه («درآمد ۳٪ رشد کرد» — کدام شرکت؟ کدام فصل؟).
## مسئله
chunk ها بدون زمینه بازیابی نمی‌شوند و OCR جدول/نمودار را خراب می‌کند.
## هدف
contextual retrieval (جمله‌ی زمینه برای هر chunk + BM25 + reranker) را پیاده و اثرش را بسنجی؛ سپس RAG روی تصویر صفحه با late interaction (ColPali) را با OCR+متن مقایسه کنی.

## پیش‌نیاز
- [p03_document_qa](../p03_document_qa/README.md)

## داده
- [ViDoRe benchmark](https://huggingface.co/vidore) · متفاوت برای هر زیرمجموعه · بازیابی سند بصری
- PDF های خودت (گزارش سالانه) · با ۵۰ سؤال و صفحه‌ی مرجع

## قطعه‌ها
- `doc_loaders` خواندن سند (txt/md/html/pdf/docx): labkit.loaders
- `chunking` chunking (fixed / recursive / heading): labkit.chunking
- `contextual_retrieval` contextual retrieval (جمله‌ی زمینه برای هر chunk): labkit.contextual.contextualize
- `bm25` BM25: support.rag.BM25
- `dense` dense retrieval (embedding): labkit.retrieval.Index
- `hybrid_rrf` hybrid با RRF: support.rag.rrf
- `reranker` reranker (cross-encoder): labkit.retrieval.Index.search
- `late_interaction` late interaction / ColPali (RAG روی تصویر صفحه): ColPali / ColQwen + byaldi یا Vespa / Qdrant multivector
- `table_extraction` استخراج جدول از PDF: pdfplumber / Camelot / Docling
- `retrieval_metrics` recall@k، MRR، nDCG: labkit.metrics
- `cache` کش پاسخ: labkit.ops.Cache

## گام 1: baseline
**یاد بگیر**
- chunking و hybrid

**بساز**
- recall@5 روی ۵۰ سؤال

**بسنج:** recall@5، MRR

**دام:** سؤال‌هایی بساز که به جدول/نمودار نیاز دارند.

## گام 2: contextual retrieval
**یاد بگیر**
- گزارش Anthropic: ۳۵٪ کاهش شکست با embedding زمینه‌دار، ۴۹٪ با BM25 زمینه‌دار، ۶۷٪ با reranker

**بساز**
- labkit.contextual.contextualize با کش
- زمینه را هم در BM25 و هم در embedding بگذار

**بسنج:** کاهش نرخ شکست بازیابی (1-recall@20)

**دام:** هزینه‌ی یک بار LLM برای هر chunk؛ کش و prompt caching لازم است.

## گام 3: RAG روی تصویر صفحه
**یاد بگیر**
- late interaction (MaxSim)، ColPali
- MUVERA برای سرعت

**بساز**
- ایندکس تصویر صفحه با ColQwen2
- مقایسه با OCR+متن روی سؤال‌های جدولی

**بسنج:** recall@5 به تفکیک نوع سؤال

**دام:** حافظه‌ی multivector زیاد است؛ pooling یا MUVERA.

## معیارها
- retrieval failure rate
- recall@5 / MRR by question type
- index size and build time
- answer accuracy

## سؤال مصاحبه
- contextual retrieval چه مشکلی را حل می‌کند؟
- late interaction چیست؟
- کی تصویر صفحه بهتر از OCR است؟

## نسخه‌ی پیشرفته
- پاسخ با مدل بینایی-زبان روی صفحه‌ی بازیابی‌شده
- Docling برای ساختار
- ارزیابی روی ViDoRe v2

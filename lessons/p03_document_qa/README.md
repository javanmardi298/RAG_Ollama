# پرسش و پاسخ روی اسناد سازمان با ارجاع به منبع
_Document Q&A with citations (HR handbook, contracts, manuals)_ · سطح پایه · 2–3 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p03_document_qa` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
دستیار داخلی منابع انسانی، حقوقی یا فنی: «چند روز مرخصی استعلاجی دارم؟» با ارجاع به بند و صفحه‌ی آیین‌نامه.
## مسئله
اسناد PDF و Word با جدول، سرصفحه و شماره‌ی صفحه‌اند؛ جواب باید فقط از سند باشد، منبع داشته باشد و وقتی جواب نیست بگوید نمی‌دانم.
## هدف
یک pipeline کامل ingestion → chunking → بازیابی → جواب با citation بسازی و faithfulness و رد کردن سؤال بی‌جواب را اندازه بگیری.

## پیش‌نیاز
- [p01_faq_search](../p01_faq_search/README.md)

## داده
- اسناد خودت (آیین‌نامه، دفترچه‌ی محصول) · بهترین گزینه؛ ۵۰ سؤال با جواب و صفحه‌ی درست بنویس
- [CUAD (قراردادها)](https://huggingface.co/datasets/theatticusproject/cuad-qa) · CC BY 4.0 · ۵۱۰ قرارداد با بندهای برچسب‌خورده

## قطعه‌ها
- `doc_loaders` خواندن سند (txt/md/html/pdf/docx): labkit.loaders
- `table_extraction` استخراج جدول از PDF: pdfplumber / Camelot / Docling
- `ocr` OCR برای اسکن و عکس: Tesseract / docTR / PaddleOCR
- `chunking` chunking (fixed / recursive / heading): labkit.chunking
- `hybrid_rrf` hybrid با RRF: support.rag.rrf
- `reranker` reranker (cross-encoder): labkit.retrieval.Index.search
- `citations` جواب با ارجاع به منبع: support.rag.answer_question
- `grounding_check` بررسی عدد/ادعای ساختگی: support.guardrails.check_output
- `structured_output` خروجی ساختاریافته + اعتبارسنجی + repair: labkit.structured
- `retrieval_metrics` recall@k، MRR، nDCG: labkit.metrics
- `llm_judge` LLM judge اعتبارسنجی‌شده (kappa): support.evaluation
- `prompt_registry` نسخه‌گذاری prompt: labkit.ops.PromptRegistry

## گام 1: ingestion و پاک‌سازی
**یاد بگیر**
- سرصفحه/پاصفحه‌ی تکراری، کلمه‌ی شکسته در انتهای خط، جدول
- metadata: منبع، صفحه، عنوان بخش

**بساز**
- labkit.loaders.load_dir روی پوشه‌ی اسناد
- ۵ صفحه‌ی تصادفی را با چشم چک کن

**بسنج:** درصد صفحه‌های خالی (اسکن؟ → OCR)

**دام:** PDF اسکن‌شده متن ندارد؛ بدون OCR سکوت می‌کند و جواب‌ها «نمی‌دانم» می‌شوند.

## گام 2: chunking و مقایسه‌ی استراتژی
**یاد بگیر**
- chunk بر اساس عنوان، مسیر عنوان به‌عنوان زمینه
- اثر chunking روی recall

**بساز**
- fixed، recursive و headings را روی همان سؤال‌ها مقایسه کن

**بسنج:** recall@5 هر استراتژی

**دام:** جدول‌ها با chunking متنی خرد می‌شوند؛ جدول را جدا و کامل نگه دار.

## گام 3: جواب با citation و «نمی‌دانم»
**یاد بگیر**
- grounding: فقط از منابع
- خروجی ساختاریافته {answerable, answer, citations}

**بساز**
- prompt را در PromptRegistry ثبت کن
- citation باید زیرمجموعه‌ی chunkهای داده‌شده باشد؛ عددها با check_output

**بسنج:** fact rate، citation valid rate، unanswerable refused rate

**دام:** مدل وقتی منبع نیست هم با اطمینان جواب می‌دهد؛ حتماً سؤال بی‌جواب در مجموعه‌ی ارزیابی بگذار.

## گام 4: ارزیابی faithfulness
**یاد بگیر**
- faithfulness در برابر relevance
- LLM judge و اعتبارسنجی با برچسب انسانی

**بساز**
- ۳۰ جواب را خودت برچسب بزن (وفادار به منبع یا نه)
- judge را بساز و kappa را بسنج

**بسنج:** kappa قاضی، نرخ جواب وفادار

**دام:** قاضی با همان مدلی که جواب داده، خطاهای مشابه را نمی‌بیند.

## معیارها
- recall@5
- faithfulness
- citation validity
- refusal on unanswerable
- latency

## سؤال مصاحبه
- چطور جلوی جواب ساختگی را گرفتی؟
- PDF اسکن‌شده و جدول را چطور مدیریت کردی؟
- faithfulness را چطور اندازه گرفتی؟

## نسخه‌ی پیشرفته
- parent-child retrieval (chunk کوچک برای جستجو، بخش بزرگ برای جواب)
- Docling برای layout و جدول
- ارزیابی با RAGAS و مقایسه با برچسب انسانی

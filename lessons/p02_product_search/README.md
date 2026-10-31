# جستجوی محصول در فروشگاه آنلاین
_E-commerce product search (WANDS)_ · سطح پایه · 2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p02_product_search` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
جستجوی Wayfair، Amazon، Digikala: «میز ناهارخوری چوبی ۶ نفره» باید محصول درست را در صفحه‌ی اول بیاورد.
## مسئله
query کوتاه و مبهم است، محصول‌ها فیلدهای مختلف دارند (نام، دسته، ویژگی) و ارتباط درجه‌دار است: کاملاً مرتبط، تا حدی مرتبط، نامرتبط.
## هدف
یک موتور جستجوی hybrid با فیلدهای وزن‌دار بسازی و با nDCG درجه‌دار ارزیابی کنی.

## پیش‌نیاز
- [p01_faq_search](../p01_faq_search/README.md)

## داده
- [WANDS (Wayfair)](https://github.com/wayfair/WANDS) · MIT · ۴۲هزار محصول، ۴۸۰ query، ۲۳۳هزار برچسب Exact/Partial/Irrelevant

## قطعه‌ها
- `doc_loaders` خواندن سند (txt/md/html/pdf/docx): labkit.loaders
- `bm25` BM25: support.rag.BM25
- `dense` dense retrieval (embedding): labkit.retrieval.Index
- `hybrid_rrf` hybrid با RRF: support.rag.rrf
- `reranker` reranker (cross-encoder): labkit.retrieval.Index.search
- `retrieval_metrics` recall@k، MRR، nDCG: labkit.metrics
- `metadata_filter` فیلتر metadata (زبان، دسترسی، تاریخ): labkit.retrieval.Index.search
- `vector_db` پایگاه برداری: FAISS (محلی) / Qdrant / pgvector
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry

## گام 1: داده و برچسب درجه‌دار
**یاد بگیر**
- relevance درجه‌دار: Exact=2، Partial=1، Irrelevant=0
- چرا nDCG و نه recall برای جستجوی محصول

**بساز**
- product.csv، query.csv، label.csv را بخوان
- متن index: نام + دسته + ویژگی‌ها

**بسنج:** توزیع برچسب‌ها برای هر query

**دام:** محصول‌های بی‌برچسب «نامرتبط» نیستند، فقط دیده نشده‌اند؛ این nDCG را بدبینانه می‌کند.

## گام 2: BM25 با فیلدهای وزن‌دار
**یاد بگیر**
- BM25F: نام محصول مهم‌تر از توضیحات است

**بساز**
- نام را دو بار در متن index تکرار کن (ساده‌ترین وزن‌دهی) یا دو index با وزن جدا
- nDCG@10 را حساب کن

**بسنج:** nDCG@10 (labkit.metrics.ndcg_at_k)

**دام:** توضیحات طولانی امتیاز BM25 را با نرمال‌سازی طول پایین می‌کشد؛ b را تنظیم کن.

## گام 3: dense، hybrid و reranker
**یاد بگیر**
- bi-encoder برای بازیابی سریع، cross-encoder برای reranking دقیق
- هزینه‌ی تأخیر reranker

**بساز**
- hybrid را اضافه کن
- cross-encoder ms-marco-MiniLM روی ۵۰ نتیجه‌ی اول

**بسنج:** nDCG@10 و تأخیر p95 هر روش

**دام:** reranker روی کل کاتالوگ اجرا نشود؛ فقط روی candidateهای مرحله‌ی اول.

## گام 4: فیلتر و query understanding
**یاد بگیر**
- استخراج ویژگی از query (رنگ، جنس، قیمت) و تبدیل به فیلتر
- فیلتر قبل از رتبه‌بندی

**بساز**
- چند الگوی ساده (regex یا LLM با خروجی ساختاریافته) برای رنگ و دسته
- where= در Index.search

**بسنج:** nDCG@10 روی queryهای دارای ویژگی

**دام:** فیلتر سخت با استخراج اشتباه، نتیجه‌ی درست را حذف می‌کند؛ اول به‌صورت boost امتحان کن.

## معیارها
- nDCG@10
- MRR
- zero-result rate
- latency p95

## سؤال مصاحبه
- nDCG را توضیح بده و چرا برای جستجو مناسب است
- bi-encoder و cross-encoder چه فرقی دارند؟
- فیلتر را قبل یا بعد از رتبه‌بندی اعمال می‌کنی؟

## نسخه‌ی پیشرفته
- learning-to-rank (LightGBM LambdaMART) روی ویژگی‌های BM25/dense/محبوبیت
- personalization
- query autocomplete و اصلاح غلط تایپی

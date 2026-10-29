# استخراج داده از فاکتور و رسید + workflow تأیید
_Invoice / receipt extraction with an approval workflow_ · سطح میانی · 2–3 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p05_invoice_extraction` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
حسابداری و خرید (accounts payable): فاکتور ایمیل می‌شود، فیلدها استخراج، با سفارش خرید تطبیق و برای پرداخت تأیید می‌شود.
## مسئله
قالب فاکتورها متفاوت است، OCR خطا دارد، و یک رقم اشتباه یعنی پرداخت اشتباه. پرداخت تکراری فاجعه است.
## هدف
استخراج ساختاریافته با اعتبارسنجی قواعد کسب‌وکار، صف بازبینی انسانی برای موارد مشکوک، و workflow که هیچ فاکتوری را دو بار پرداخت نکند.

## پیش‌نیاز
- [p03_document_qa](../p03_document_qa/README.md)

## داده
- [SROIE](https://rrc.cvc.uab.es/?ch=13) · پژوهشی · ۱۰۰۰ رسید با شرکت، تاریخ، آدرس، مبلغ کل
- [CORD](https://huggingface.co/datasets/naver-clova-ix/cord-v2) · CC BY 4.0 · رسید با آیتم‌ها
- فاکتورهای ساختگی خودت · با جمع غلط، تاریخ آینده، فاکتور تکراری برای موارد مرزی

## قطعه‌ها
- `ocr` OCR برای اسکن و عکس: Tesseract / docTR / PaddleOCR
- `doc_loaders` خواندن سند (txt/md/html/pdf/docx): labkit.loaders
- `structured_output` خروجی ساختاریافته + اعتبارسنجی + repair: labkit.structured
- `extraction_metrics` F1 هر فیلد، exact match: labkit.metrics
- `workflow_engine` موتور workflow (retry، resume، audit): labkit.workflow
- `human_approval` تأیید انسانی در workflow: labkit.workflow
- `idempotency` idempotency عمل‌ها: support.tools / labkit.workflow
- `selective_decision` آستانه‌ی ریسک و ارجاع به انسان: support.decision
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `pii_masking` پنهان کردن PII: support.guardrails.mask_pii

## گام 1: schema و قواعد کسب‌وکار
**یاد بگیر**
- schema با pydantic
- اعتبارسنجی فراتر از نوع: جمع = خالص + مالیات، تاریخ در گذشته، IBAN معتبر

**بساز**
- مدل Invoice با validatorها
- ۲۰ فاکتور با جواب درست (gold) آماده کن

**بسنج:** پوشش قواعد روی موارد مرزی

**دام:** JSON معتبر ≠ داده‌ی درست؛ constrained decoding فقط شکل را تضمین می‌کند.

## گام 2: استخراج و repair
**یاد بگیر**
- structured output + یک دور repair با پیام خطا
- متن OCR در برابر مدل بینایی

**بساز**
- labkit.structured.extract روی متن OCR
- مقایسه با مدل بینایی روی همان فاکتورها

**بسنج:** F1 هر فیلد، exact match سند (labkit.metrics.extraction_report)

**دام:** مقایسه‌ی رشته‌ای خام «1.234,50» و «1234.5» را متفاوت می‌شمارد؛ نرمال‌سازی کن.

## گام 3: اطمینان و صف بازبینی
**یاد بگیر**
- چه زمانی انسان: قاعده‌ی شکسته، مبلغ بالا، فیلد خالی، تأمین‌کننده‌ی جدید

**بساز**
- قاعده‌های ارجاع با کد (نه LLM)
- نرخ ارجاع و دقت موارد خودکار را کنار هم گزارش کن

**بسنج:** straight-through rate در برابر خطای موارد خودکار

**دام:** Straight-through rate بالا بدون نرخ خطا گمراه‌کننده است.

## گام 4: workflow پرداخت
**یاد بگیر**
- idempotency key = شماره‌ی فاکتور + تأمین‌کننده
- تأیید انسانی بالای سقف، audit log

**بساز**
- labkit.workflow: extract → validate → match PO → approve(>سقف) → pay
- فاکتور تکراری و crash وسط کار را شبیه‌سازی کن

**بسنج:** صفر پرداخت تکراری در آزمون؛ زمان تا پرداخت

**دام:** retry یک مرحله‌ی پرداخت بدون idempotency یعنی پرداخت دوباره.

## معیارها
- field F1
- document exact match
- straight-through rate
- error among automated
- duplicate payments (=0)

## سؤال مصاحبه
- چطور جلوی پرداخت تکراری را گرفتی؟
- کی فاکتور به انسان می‌رود و چه کسی این را تصمیم می‌گیرد؟
- F1 فیلدی را چطور حساب کردی؟

## نسخه‌ی پیشرفته
- مدل layout-aware (LayoutLMv3، Donut) و fine-tune
- تطبیق سه‌طرفه با PO و رسید انبار
- یادگیری از اصلاحات اپراتور

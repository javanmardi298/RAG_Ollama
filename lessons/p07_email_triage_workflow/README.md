# workflow پاسخ به ایمیل‌های صندوق مشترک
_Shared-inbox email triage and reply workflow_ · سطح میانی · 2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p07_email_triage_workflow` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
ایمیل info@ یا support@: دسته‌بندی، استخراج شماره سفارش، پیش‌نویس جواب، تأیید اپراتور، ارسال؛ با SLA.
## مسئله
حجم بالا، ایمیل‌های تکراری و thread طولانی، و اینکه ارسال اشتباه قابل برگشت نیست.
## هدف
یک workflow قطعی با چند گام LLM: هر گام قابل تست، ارسال فقط با تأیید یا با اطمینان بالا، و هیچ ایمیلی دو بار جواب نگیرد.

## پیش‌نیاز
- [p04_ticket_triage](../p04_ticket_triage/README.md)

## داده
- ایمیل‌های ساختگی از Bitext + shop.db · پیام Bitext را با شماره سفارش واقعی shop.db ترکیب کن
- [Enron (فقط برای نویز واقعی)](https://www.cs.cmu.edu/~enron/) · عمومی · PII دارد؛ فقط برای تمرین ingestion

## قطعه‌ها
- `workflow_engine` موتور workflow (retry، resume، audit): labkit.workflow
- `human_approval` تأیید انسانی در workflow: labkit.workflow
- `idempotency` idempotency عمل‌ها: support.tools / labkit.workflow
- `intent_classifier` طبقه‌بند intent (TF-IDF / embedding / LLM): support.intents
- `structured_output` خروجی ساختاریافته + اعتبارسنجی + repair: labkit.structured
- `citations` جواب با ارجاع به منبع: support.rag.answer_question
- `grounding_check` بررسی عدد/ادعای ساختگی: support.guardrails.check_output
- `pii_masking` پنهان کردن PII: support.guardrails.mask_pii
- `memory` حافظه‌ی گفتگو (خلاصه + facts): labkit.memory
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger

## گام 1: طراحی workflow
**یاد بگیر**
- workflow در برابر agent: مسیر ثابت با گام‌های LLM
- idempotency key = Message-ID

**بساز**
- گام‌ها: parse → classify → extract → draft → check → approve → send
- labkit.workflow با audit

**بسنج:** پوشش موارد: تکراری، thread، پیوست

**دام:** agent آزاد برای ایمیل، رفتار غیرقابل‌پیش‌بینی و تست‌ناپذیر دارد.

## گام 2: گام‌های LLM قابل تست
**یاد بگیر**
- هر گام یک ورودی/خروجی مشخص و تست با ScriptedLLM

**بساز**
- classify با مدل مرحله‌ی ۱ support-agent
- extract با structured_output
- draft با RAG روی قواعد

**بسنج:** دقت هر گام جداگانه

**دام:** ارزیابی فقط end-to-end نمی‌گوید کدام گام خراب است.

## گام 3: تأیید و ارسال
**یاد بگیر**
- ارسال خودکار فقط برای دسته‌های کم‌ریسک با اطمینان بالا
- بقیه با تأیید اپراتور

**بساز**
- approval=lambda ctx: risk(ctx) != 'low' or conf < t
- صف تأیید در یک صفحه‌ی ساده

**بسنج:** نرخ ارسال خودکار در برابر نرخ ویرایش اپراتور

**دام:** نرخ ویرایش اپراتور بهترین معیار کیفیت پیش‌نویس است؛ ثبتش کن.

## گام 4: SLA و بازیابی از خطا
**یاد بگیر**
- retry با backoff، resume بعد از crash
- هشدار نزدیک شدن به SLA

**بساز**
- crash وسط workflow را شبیه‌سازی کن و resume کن
- گزارش زمان پاسخ

**بسنج:** صفر جواب تکراری، درصد پاسخ در SLA

**دام:** retry گام send بدون idempotency = دو ایمیل به مشتری.

## معیارها
- per-step accuracy
- auto-send rate
- operator edit rate
- SLA hit rate
- duplicate replies (=0)

## سؤال مصاحبه
- چرا workflow و نه agent؟
- idempotency را کجا گذاشتی؟
- کیفیت پیش‌نویس را چطور اندازه گرفتی؟

## نسخه‌ی پیشرفته
- Temporal یا Prefect برای workflow در مقیاس
- یادگیری از ویرایش‌های اپراتور (DPO روی جفت پیش‌نویس/نسخه‌ی نهایی)
- خلاصه‌ی thread طولانی با memory

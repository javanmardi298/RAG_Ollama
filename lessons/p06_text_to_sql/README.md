# دستیار تحلیل داده (Text-to-SQL)
_Text-to-SQL analytics assistant_ · سطح میانی · 2–3 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p06_text_to_sql` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
BI سلف‌سرویس (مثل Databricks Genie، Snowflake Cortex Analyst): مدیر می‌پرسد «فروش ماه قبل به تفکیک دسته» و جدول می‌گیرد.
## مسئله
مدل باید schema را بفهمد، SQL درست بنویسد، و هرگز داده را تغییر ندهد یا جدول حساس را بخواند.
## هدف
Text-to-SQL با schema linking، اجرای امن (فقط خواندن) و ارزیابی execution accuracy؛ و پرسیدن سؤال روشن‌کننده وقتی سؤال مبهم است.

## پیش‌نیاز
- [p04_ticket_triage](../p04_ticket_triage/README.md)

## داده
- shop.db همین repo (`data/shop.db`) · سفارش، مشتری، محصول، بازپرداخت: ۵۰ سؤال طلایی با SQL درست بنویس
- [Spider / BIRD mini-dev](https://bird-bench.github.io/) · CC BY-SA · بنچمارک استاندارد

## قطعه‌ها
- `sql_guard` محافظ Text-to-SQL: labkit.sqlguard
- `sql_exec_accuracy` execution accuracy برای SQL: labkit.sqlguard.execution_match
- `structured_output` خروجی ساختاریافته + اعتبارسنجی + repair: labkit.structured
- `prompt_registry` نسخه‌گذاری prompt: labkit.ops.PromptRegistry
- `tool_agent` agent با tool calling: support.agent
- `selective_decision` آستانه‌ی ریسک و ارجاع به انسان: support.decision
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `retrieval_metrics` recall@k، MRR، nDCG: labkit.metrics

## گام 1: مجموعه‌ی سؤال طلایی
**یاد بگیر**
- execution accuracy در برابر تطابق متنی SQL

**بساز**
- ۵۰ سؤال با SQL درست روی shop.db، از آسان (count) تا سخت (join + group + تاریخ)

**بسنج:** توزیع سختی

**دام:** سؤال‌های فقط آسان، دقت را ۹۰٪ نشان می‌دهند و در عمل شکست می‌خورد.

## گام 2: schema در prompt و few-shot
**یاد بگیر**
- schema linking: فقط جدول‌ها و ستون‌های مرتبط
- few-shot پویا با شبیه‌ترین سؤال‌ها

**بساز**
- DDL + چند ردیف نمونه در prompt
- few-shot با بازیابی

**بسنج:** execution accuracy (labkit.sqlguard.execution_match)

**دام:** schema کامل یک دیتابیس بزرگ context را پر می‌کند؛ اول جدول‌ها را بازیابی کن.

## گام 3: اجرای امن و repair
**یاد بگیر**
- دفاع چندلایه: validator + اتصال read-only + LIMIT + timeout
- repair با پیام خطای دیتابیس

**بساز**
- labkit.sqlguard.run_guarded با جدول‌های مجاز
- یک دور repair با خطا

**بسنج:** نرخ SQL رد شده، دقت بعد از repair

**دام:** فقط validator کافی نیست؛ اتصال هم باید read-only باشد.

## گام 4: سؤال مبهم و ارائه‌ی نتیجه
**یاد بگیر**
- تشخیص ابهام («بهترین مشتری» با چه معیاری؟)
- خلاصه‌ی نتیجه بدون عدد ساختگی

**بساز**
- مرحله‌ی clarify قبل از SQL
- خلاصه‌ی متنی که فقط عددهای جدول را دارد (check_output)

**بسنج:** نرخ سؤال روشن‌کننده‌ی بجا

**دام:** خلاصه‌ی LLM ممکن است عدد بسازد؛ همان grounding check مرحله‌ی ۵ support-agent.

## معیارها
- execution accuracy
- blocked unsafe SQL (=100%)
- clarification precision
- latency

## سؤال مصاحبه
- چطور مطمئن شدی SQL مخرب اجرا نمی‌شود؟
- execution accuracy چیست و چرا بهتر از تطابق متنی است؟
- با schema بزرگ چه می‌کنی؟

## نسخه‌ی پیشرفته
- semantic layer (dbt metrics) به‌جای SQL خام
- agent چندمرحله‌ای: کاوش schema، SQL، بررسی نتیجه
- fine-tune مدل کوچک روی سؤال‌های خودت

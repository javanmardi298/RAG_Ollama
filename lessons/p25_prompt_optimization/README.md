# بهینه‌سازی خودکار prompt (GEPA / DSPy) بدون overfitting
_Automatic prompt optimisation (GEPA / DSPy) without overfitting_ · سطح میانی · 1–2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p25_prompt_optimization` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
تنظیم prompt طبقه‌بندی تیکت، استخراج و agent با داده به جای حدس؛ GEPA (ICLR 2026) و DSPy در صنعت رایج شده‌اند.
## مسئله
prompt نویسی دستی کند و سلیقه‌ای است؛ بهینه‌سازی خودکار روی داده‌ی کم overfit می‌کند (گزارش: رشد prompt از 2.4k به 8.8k کاراکتر و افت دقت تست).
## هدف
با train/val/test جدا، بهینه‌ساز GEPA-style (بازتاب روی خطاها + پارتو + جریمه‌ی طول) را اجرا کنی و بهبود را روی test با CI گزارش کنی.

## پیش‌نیاز
- [p04_ticket_triage](../p04_ticket_triage/README.md)

## داده
- داده‌ی p04 (تیکت) یا intent های Bitext همین repo · train 50 / val 100 / test 300
- [GEPA (مقاله)](https://arxiv.org/abs/2507.19457) · arXiv · Reflective prompt evolution

## قطعه‌ها
- `prompt_optimizer` بهینه‌سازی prompt (GEPA-style، پارتو + جریمه‌ی طول): labkit.optimize.optimize
- `dspy` DSPy (برنامه‌نویسی prompt، GEPA/MIPRO): dspy (pip install dspy)
- `prompt_registry` نسخه‌گذاری prompt: labkit.ops.PromptRegistry
- `bootstrap_ci` فاصله‌ی اطمینان bootstrap: support.evaluation
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger

## گام 1: تقسیم و baseline
**یاد بگیر**
- train برای بازتاب، val برای انتخاب، test فقط یک بار

**بساز**
- prompt دستی روی هر سه

**بسنج:** دقت با CI

**دام:** انتخاب روی test = نشت.

## گام 2: بهینه‌سازی
**یاد بگیر**
- بازتاب روی خطاها، جبهه‌ی پارتو، جریمه‌ی طول

**بساز**
- labkit.optimize.optimize با llm_proposer، budget=8

**بسنج:** منحنی val و طول prompt

**دام:** رشد بی‌رویه‌ی prompt = حفظ کردن مثال‌ها.

## گام 3: گزارش و ثبت
**یاد بگیر**
- نسخه‌گذاری prompt

**بساز**
- prompt برنده را در PromptRegistry ثبت و روی test بسنج
- همان کار با DSPy GEPA (اختیاری)

**بسنج:** بهبود test با CI + هزینه‌ی بهینه‌سازی

**دام:** بهبود val بدون test گزارش نشود.

## معیارها
- test accuracy with CI
- prompt length
- optimisation cost (calls, tokens)

## سؤال مصاحبه
- GEPA چطور کار می‌کند؟
- overfitting در بهینه‌سازی prompt را چطور کنترل کردی؟
- DSPy چه چیزی اضافه می‌کند؟

## نسخه‌ی پیشرفته
- بهینه‌سازی چندهدفه (دقت، هزینه، تأخیر)
- بهینه‌سازی prompt های agent چندمرحله‌ای
- مقایسه با fine-tune کوچک

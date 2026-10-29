# Context engineering و حافظه برای agent های طولانی
_Context engineering and memory for long-running agents_ · سطح میانی · 1 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p27_context_engineering` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
agent هایی که ده‌ها ابزار صدا می‌زنند و context پر می‌شود؛ هزینه و کیفیت با مدیریت context تعیین می‌شود.
## مسئله
context بی‌رویه بزرگ می‌شود: هزینه بالا، کش شکسته، و دقت پایین‌تر روی جزئیات میانی (context rot).
## هدف
بودجه‌ی context، prefix پایدار برای prompt caching، کوتاه‌کردن و پاک‌کردن tool result های کهنه و حافظه‌ی خلاصه را پیاده و اثرشان را بر هزینه و دقت بسنجی.

## پیش‌نیاز
- [p10_research_agent](../p10_research_agent/README.md)

## داده
- trace های agent p10 یا support agent · گفت‌وگوهای طولانی با ابزار زیاد

## قطعه‌ها
- `context_budget` مدیریت context (بودجه، prefix پایدار، پاک‌کردن tool result کهنه): labkit.context.pack
- `memory` حافظه‌ی گفتگو (خلاصه + facts): labkit.memory
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `cache` کش پاسخ: labkit.ops.Cache
- `tool_agent` agent با tool calling: support.agent

## گام 1: اندازه‌گیری
**یاد بگیر**
- توکن هر بخش: system، ابزارها، تاریخچه، tool result

**بساز**
- Ledger و شمارش توکن برای ۲۰ گفت‌وگوی طولانی

**بسنج:** توزیع توکن

**دام:** بدون اندازه‌گیری، بهینه‌سازی حدس است.

## گام 2: بسته‌بندی
**یاد بگیر**
- prefix پایدار (کش)، الزامی‌ها اول
- truncate و clear_stale_tool_results

**بساز**
- labkit.context.pack با بودجه

**بسنج:** توکن و نرخ cache hit قبل/بعد

**دام:** خلاصه‌سازی زودهنگام جزئیات لازم را حذف می‌کند؛ compaction آخرین راه.

## گام 3: حافظه
**یاد بگیر**
- خلاصه + facts، بازیابی حافظه

**بساز**
- labkit.memory در گفت‌وگوی چندجلسه‌ای

**بسنج:** دقت پرسش از جزئیات قبلی

**دام:** حافظه‌ی غلط بدتر از بی‌حافظگی است؛ منبع fact را نگه دار.

## معیارها
- tokens per task
- cache hit rate
- task success
- recall of earlier facts

## سؤال مصاحبه
- context engineering چیست؟
- prompt caching را چطور حفظ کردی؟
- کی compaction؟

## نسخه‌ی پیشرفته
- sub-agent برای کار پرتوکن
- حافظه‌ی برداری با ابزار خواندن/نوشتن
- ارزیابی needle-in-haystack روی agent

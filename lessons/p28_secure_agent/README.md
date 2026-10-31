# agent امن با طراحی: provenance و policy در کد (CaMeL)
_Secure-by-design agent: provenance tracking and code policies (CaMeL)_ · سطح پیشرفته · 2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p28_secure_agent` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
دستیار ایمیل/خرید که محتوای غیرقابل‌اعتماد (ایمیل، وب) می‌خواند و می‌تواند پول جابه‌جا کند یا ایمیل بفرستد.
## مسئله
prompt injection غیرمستقیم با فیلتر قابل حل کامل نیست؛ حمله‌ی تطبیقی فیلتر را دور می‌زند.
## هدف
جریان داده را جدا کنی: planner فقط درخواست کاربر را می‌بیند، محتوای غیرقابل‌اعتماد بدون ابزار پردازش و برچسب منبع می‌خورد، و policy در کد آرگومان‌های حساس را چک می‌کند؛ نرخ موفقیت حمله و افت کارایی را بسنجی.

## پیش‌نیاز
- [p16_llm_security](../p16_llm_security/README.md)

## داده
- [AgentDojo](https://github.com/ethz-spylab/agentdojo) · MIT · معیار injection برای agent
- [CaMeL (مقاله)](https://arxiv.org/abs/2503.18813) · arXiv · Defeating prompt injections by design

## قطعه‌ها
- `capability_security` امنیت با طراحی (CaMeL: provenance + policy در کد): labkit.capsec.Policy
- `input_guardrails` guardrail ورودی (injection، red flags): support.guardrails.check_input
- `confirmation` تأیید صریح قبل از عمل: support.agent
- `tool_agent` agent با tool calling: support.agent
- `redteam_set` مجموعه‌ی red-team: eval/redteam.yaml
- `attack_scanner` اسکنر حمله‌ی خودکار: garak / PyRIT

## گام 1: مدل تهدید و baseline
**یاد بگیر**
- injection مستقیم/غیرمستقیم، exfiltration

**بساز**
- ۲۰ حمله روی agent فعلی

**بسنج:** نرخ موفقیت حمله (ASR) و موفقیت وظیفه

**دام:** فقط حمله‌های شناخته‌شده = اطمینان کاذب.

## گام 2: provenance و policy
**یاد بگیر**
- Value با منبع، derive (انتشار آلودگی)، Policy

**بساز**
- labkit.capsec: گیرنده‌ی پرداخت/ایمیل باید از کاربر یا DB باشد

**بسنج:** ASR بعد از policy

**دام:** policy خیلی سخت = agent بی‌فایده؛ موفقیت وظیفه را هم گزارش کن.

## گام 3: ارزیابی و هزینه
**یاد بگیر**
- CaMeL حدود ۲.۸ برابر توکن گزارش کرده

**بساز**
- AgentDojo یا مجموعه‌ی خودت؛ هزینه‌ی توکن

**بسنج:** ASR، utility، توکن

**دام:** حفاظت از جریان کنترل ≠ درستی متن پاسخ.

## معیارها
- attack success rate
- task utility
- token overhead

## سؤال مصاحبه
- چرا فیلتر injection کافی نیست؟
- CaMeL چطور جریان داده را جدا می‌کند؟
- هزینه‌ی امنیت چقدر بود؟

## نسخه‌ی پیشرفته
- مفسر کامل CaMeL
- policy های وابسته به زمینه
- ترکیب با classifier امنیتی

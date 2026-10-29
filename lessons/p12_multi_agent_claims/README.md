# پردازش خسارت بیمه با چند agent و تأیید انسانی
_Multi-agent insurance claims processing with human-in-the-loop_ · سطح پیشرفته · 3–4 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p12_multi_agent_claims` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
بیمه و بانک (خسارت، وام، KYC): پرونده از چند سند تشکیل شده، چند تخصص لازم است، تصمیم نهایی پول جابه‌جا می‌کند و باید قابل توضیح و audit باشد.
## مسئله
یک agent با همه‌ی ابزارها گیج می‌شود؛ قواعد بیمه‌نامه باید با کد اعمال شوند؛ تقلب باید علامت بخورد؛ هر تصمیم باید دلیل داشته باشد.
## هدف
supervisor + agentهای متخصص (اسناد، پوشش بیمه‌نامه، تقلب، محاسبه)، تصمیم نهایی با موتور قواعد، و انسان برای موارد پرریسک.

## پیش‌نیاز
- [p05_invoice_extraction](../p05_invoice_extraction/README.md)
- [p08_support_agent](../p08_support_agent/README.md)

## داده
- پرونده‌های ساختگی · مثل shop.db: ۳۰۰ پرونده با موارد مرزی (سقف پوشش، استثنا، تاریخ، تقلب کاشته‌شده) و جواب درست با کد

## قطعه‌ها
- `multi_agent` supervisor و agentهای متخصص: LangGraph supervisor (روی support.lc بساز)
- `langgraph` گراف حالت LangGraph + checkpointer: support.lc.graph
- `tool_agent` agent با tool calling: support.agent
- `structured_output` خروجی ساختاریافته + اعتبارسنجی + repair: labkit.structured
- `workflow_engine` موتور workflow (retry، resume، audit): labkit.workflow
- `human_approval` تأیید انسانی در workflow: labkit.workflow
- `idempotency` idempotency عمل‌ها: support.tools / labkit.workflow
- `citations` جواب با ارجاع به منبع: support.rag.answer_question
- `selective_decision` آستانه‌ی ریسک و ارجاع به انسان: support.decision
- `sim_user_eval` ارزیابی با کاربر شبیه‌سازی‌شده: support.evaluation
- `bootstrap_ci` فاصله‌ی اطمینان bootstrap: support.evaluation
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `tracing` tracing: OpenTelemetry / Langfuse (محلی) / LangSmith
- `pii_masking` پنهان کردن PII: support.guardrails.mask_pii

## گام 1: قواعد با کد، ground truth با کد
**یاد بگیر**
- همان اصل support-agent: تصمیم پوشش با کد، نه LLM

**بساز**
- policy engine: پوشش، فرانشیز، سقف، استثنا
- مولد پرونده‌ی ساختگی با جواب درست

**بسنج:** تست واحد روی موارد مرزی

**دام:** اگر LLM تصمیم پوشش را بگیرد، قابل audit و تکرار نیست.

## گام 2: agentهای متخصص
**یاد بگیر**
- نقش، ابزار و خروجی ساختاریافته‌ی هر agent
- supervisor: کدام متخصص بعدی

**بساز**
- document agent (استخراج)، coverage agent (بیمه‌نامه با RAG)، fraud agent (علامت‌ها)، calculator (کد)

**بسنج:** دقت هر agent جداگانه

**دام:** agentهایی که با هم چت آزاد می‌کنند هزینه و خطا را چند برابر می‌کنند؛ پیام‌ها ساختاریافته باشند.

## گام 3: تصمیم، توضیح و انسان
**یاد بگیر**
- تصمیم = موتور قواعد روی facts استخراج‌شده
- توضیح با ارجاع به سند و بند

**بساز**
- approval برای مبلغ بالا یا علامت تقلب
- audit log کامل هر پرونده

**بسنج:** دقت تصمیم، نرخ ارجاع، false approve rate

**دام:** false approve (پرداخت ناحق) و false deny (رد ناحق) هزینه‌ی متفاوت دارند؛ جدا گزارش کن.

## گام 4: مقایسه با agent تکی
**یاد بگیر**
- آیا multi-agent ارزشش را دارد؟ paired bootstrap روی همان پرونده‌ها

**بساز**
- همان پرونده‌ها با یک agent و همه‌ی ابزارها

**بسنج:** اختلاف دقت با CI، هزینه و تأخیر هر روش

**دام:** multi-agent همیشه بهتر نیست؛ گاهی فقط گران‌تر است.

## معیارها
- decision accuracy
- false approve / false deny
- referral rate
- cost and latency per claim
- explanation citation validity

## سؤال مصاحبه
- چرا چند agent؟ اندازه‌گیری‌ات چه گفت؟
- تصمیم نهایی را چه کسی می‌گیرد؟
- audit و توضیح‌پذیری را چطور تضمین کردی؟

## نسخه‌ی پیشرفته
- Claude Managed Agents یا LangGraph Platform
- ارزیابی fairness بین گروه‌ها
- یادگیری از تصمیم‌های ارزیاب انسانی

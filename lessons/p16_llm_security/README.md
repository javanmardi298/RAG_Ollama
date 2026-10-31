# آزمایشگاه امنیت برنامه‌های LLM (red-team)
_LLM application security lab (red-teaming)_ · سطح پیشرفته · 2–3 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p16_llm_security` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
تیم امنیت هر شرکتی که agent یا RAG در production دارد؛ OWASP Top 10 for LLM Applications.
## مسئله
prompt injection مستقیم و غیرمستقیم (از سند، ایمیل، صفحه‌ی وب)، نشت داده‌ی کاربران دیگر، سوءاستفاده از ابزارها، و jailbreak.
## هدف
یک مجموعه‌ی حمله‌ی قابل تکرار برای پروژه‌های قبلی بسازی، دفاع چندلایه پیاده کنی و نرخ موفقیت حمله را قبل/بعد گزارش کنی.

## پیش‌نیاز
- [p08_support_agent](../p08_support_agent/README.md)
- [p03_document_qa](../p03_document_qa/README.md)

## داده
- eval/redteam.yaml همین repo (`eval/redteam.yaml`) · نقطه‌ی شروع؛ دو known gap دارد
- [garak](https://github.com/NVIDIA/garak) · Apache 2.0 · اسکنر خودکار
- [OWASP LLM Top 10](https://genai.owasp.org/) · CC BY-SA · دسته‌بندی ریسک‌ها

## قطعه‌ها
- `input_guardrails` guardrail ورودی (injection، red flags): support.guardrails.check_input
- `pii_masking` پنهان کردن PII: support.guardrails.mask_pii
- `redteam_set` مجموعه‌ی red-team: eval/redteam.yaml
- `grounding_check` بررسی عدد/ادعای ساختگی: support.guardrails.check_output
- `safety_classifier` classifier امنیتی LLM: Llama Guard / ShieldGemma روی Ollama
- `attack_scanner` اسکنر حمله‌ی خودکار: garak / PyRIT
- `confirmation` تأیید صریح قبل از عمل: support.agent
- `idempotency` idempotency عمل‌ها: support.tools / labkit.workflow
- `tool_agent` agent با tool calling: support.agent
- `llm_judge` LLM judge اعتبارسنجی‌شده (kappa): support.evaluation
- `ci_eval` ارزیابی در CI: .github/workflows/tests.yml

## گام 1: مدل تهدید
**یاد بگیر**
- دارایی‌ها (داده‌ی مشتری، پول)، مهاجم‌ها، سطح حمله (ورودی، سند، ابزار)
- OWASP LLM01–LLM10

**بساز**
- برای support-agent: جدول تهدید ← دفاع موجود ← شکاف

**بسنج:** تعداد شکاف بدون دفاع

**دام:** تمرکز فقط روی jailbreak؛ ریسک واقعی معمولاً سوءاستفاده از ابزار و نشت داده است.

## گام 2: حمله‌ی مستقیم و غیرمستقیم
**یاد بگیر**
- injection غیرمستقیم: دستور داخل سند یا ایمیل
- data exfiltration از طریق ابزار

**بساز**
- سندی با دستور مخفی در policies کپی‌شده؛ ایمیل با دستور
- garak روی endpoint مرحله‌ی ۸

**بسنج:** attack success rate به تفکیک دسته

**دام:** تست فقط با حمله‌های انگلیسی؛ آلمانی، فارسی و base64 را هم امتحان کن.

## گام 3: دفاع چندلایه
**یاد بگیر**
- کنترل با کد (هویت از session، تأیید، idempotency) قوی‌تر از prompt
- classifier امنیتی به‌عنوان لایه‌ی اضافه

**بساز**
- known gapهای redteam.yaml را ببند
- Llama Guard روی ورودی/خروجی و مقایسه‌ی هزینه

**بسنج:** attack success قبل/بعد، false positive روی ترافیک عادی

**دام:** دفاع سخت‌گیرانه کاربران عادی را رد می‌کند؛ false positive را هم گزارش کن.

## گام 4: امنیت در CI
**یاد بگیر**
- هر حمله‌ی موفق = یک تست جدید

**بساز**
- مجموعه‌ی حمله در CI؛ شکست build اگر نرخ گرفتن افت کند

**بسنج:** پوشش دسته‌های OWASP

**دام:** مجموعه‌ی ثابت کهنه می‌شود؛ به‌روزرسانی دوره‌ای.

## معیارها
- attack success rate per category
- false positive rate
- OWASP coverage
- guardrail latency

## سؤال مصاحبه
- injection غیرمستقیم چیست و چطور دفاع کردی؟
- چرا کنترل با کد مهم‌تر از prompt است؟
- false positive دفاع را چطور سنجیدی؟

## نسخه‌ی پیشرفته
- spotlighting و جداسازی داده/دستور
- canary token برای تشخیص نشت system prompt
- ارزیابی امنیتی agentهای MCP (tool poisoning)

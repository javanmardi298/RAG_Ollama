# پلتفرم LLMOps: gateway، هزینه، ارزیابی در CI و پایش
_LLMOps platform: gateway, cost, CI evaluation, observability_ · سطح پیشرفته · 3–4 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p14_llmops_platform` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
تیم پلتفرم AI در هر شرکت متوسط به بالا: همه‌ی تیم‌ها از یک gateway به مدل‌ها وصل می‌شوند؛ هزینه، کیفیت و امنیت مرکزی کنترل می‌شود.
## مسئله
هزینه‌ی پنهان، تغییر prompt که کیفیت را بی‌صدا خراب می‌کند، مدل جدید که رفتار را عوض می‌کند، و نبود دید روی اینکه چه اتفاقی افتاده.
## هدف
یک لایه‌ی مشترک: کش، router، ledger هزینه، نسخه‌ی prompt، tracing، و eval که هر PR را قبل از merge می‌سنجد؛ روی پروژه‌ی support-agent پیاده شود.

## پیش‌نیاز
- [p08_support_agent](../p08_support_agent/README.md)

## داده
- traceهای همین repo (`results/traces.jsonl`) · و سناریوهای مرحله‌ی ۶ به‌عنوان مجموعه‌ی regression

## قطعه‌ها
- `cache` کش پاسخ: labkit.ops.Cache
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `model_router` router مدل ارزان ← قوی: labkit.ops.Router
- `prompt_registry` نسخه‌گذاری prompt: labkit.ops.PromptRegistry
- `tracing` tracing: OpenTelemetry / Langfuse (محلی) / LangSmith
- `ci_eval` ارزیابی در CI: .github/workflows/tests.yml
- `sim_user_eval` ارزیابی با کاربر شبیه‌سازی‌شده: support.evaluation
- `bootstrap_ci` فاصله‌ی اطمینان bootstrap: support.evaluation
- `ab_testing` A/B با SRM و guardrail: support.experiments
- `drift` drift با PSI: support.monitoring
- `serving` سرو با FastAPI + Docker: app/main.py
- `loadtest` load test و p95: scripts/loadtest.py
- `auth_ratelimit` احراز هویت و rate limit: FastAPI middleware / API gateway
- `streaming` پاسخ stream (SSE): FastAPI StreamingResponse (app/main_lc.py نمونه دارد)
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry

## گام 1: gateway و ledger
**یاد بگیر**
- هزینه به ازای feature و کاربر
- کش برای درخواست‌های قطعی

**بساز**
- labkit.ops.Metered دور LLMهای support-agent
- گزارش هزینه/تأخیر به تفکیک feature

**بسنج:** هزینه به ازای گفتگو، cache hit rate

**دام:** کش جواب غیرقطعی (temperature>0) یا شخصی‌شده = نشت داده بین کاربران.

## گام 2: router مدل
**یاد بگیر**
- اول مدل ارزان، ارتقا با شرط قابل اندازه‌گیری

**بساز**
- labkit.ops.Router: مدل محلی، ارتقا به Claude وقتی output check شکست خورد

**بسنج:** escalation rate، کیفیت و هزینه در برابر همیشه-قوی

**دام:** اگر بیشتر درخواست‌ها ارتقا پیدا کنند، router فقط تأخیر اضافه کرده.

## گام 3: prompt و eval در CI
**یاد بگیر**
- هر prompt یک نسخه؛ هر تغییر یک اجرای eval
- regression suite

**بساز**
- PromptRegistry برای promptهای agent
- GitHub Action: ۳۰ سناریوی مرحله‌ی ۶ با ScriptedLLM/مدل کوچک، شکست اگر task success افت کند

**بسنج:** زمان eval در CI، تشخیص regression عمدی

**دام:** eval غیرقطعی در CI تست flaky می‌سازد؛ seed و temperature 0، یا آستانه با CI.

## گام 4: tracing و پایش
**یاد بگیر**
- trace هر نوبت: گام‌ها، ابزارها، تأخیر، هزینه
- هشدار drift و افت کیفیت

**بساز**
- Langfuse محلی یا OpenTelemetry
- داشبورد p95، هزینه، handoff rate، PSI

**بسنج:** زمان پیدا کردن علت یک خطای کاشته‌شده

**دام:** trace بدون پنهان‌سازی PII خودش نشت داده است.

## معیارها
- cost per conversation
- cache hit rate
- escalation rate
- eval runtime in CI
- p95 latency

## سؤال مصاحبه
- هزینه‌ی LLM را چطور کنترل کردی؟
- چطور می‌فهمی تغییر prompt کیفیت را خراب کرد؟
- چه چیزی را trace می‌کنی؟

## نسخه‌ی پیشرفته
- LiteLLM یا Portkey به‌عنوان gateway
- prompt caching سمت API و batch API
- online eval با نمونه‌برداری از ترافیک

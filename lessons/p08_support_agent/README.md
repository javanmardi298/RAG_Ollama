# دستیار پشتیبانی چندنوبتی فروشگاه (پروژه‌ی اصلی همین repo)
_Multi-turn customer-support agent (this repository)_ · سطح میانی · 6–10 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p08_support_agent` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
دستیار پشتیبانی فروشگاه آنلاین: پیگیری، لغو، مرجوعی و بازپرداخت سفارش با ابزار؛ ارجاع به انسان در موارد پرریسک.
## مسئله
گفتگوی چندنوبتی، عمل‌هایی که پول جابه‌جا می‌کنند، دو زبان، و تصمیم بین حل خودکار و ارجاع.
## هدف
همه‌ی بندهای آگهی: agent چندنوبتی، تصمیم ارجاع، RAG چندزبانه، ارزیابی و guardrail، production، A/B.

## پیش‌نیاز
- [p03_document_qa](../p03_document_qa/README.md)
- [p04_ticket_triage](../p04_ticket_triage/README.md)

## داده
- Bitext + CLINC150 + WANDS + shop.db · پیاده‌سازی‌شده در این repo

## قطعه‌ها
- `leakage_free_split` تقسیم بدون نشت (group split): support.data
- `synthetic_data` داده‌ی ساختگی با موارد مرزی: support.orders
- `intent_classifier` طبقه‌بند intent (TF-IDF / embedding / LLM): support.intents
- `calibration` calibration (temperature scaling، ECE): support.intents
- `selective_decision` آستانه‌ی ریسک و ارجاع به انسان: support.decision
- `bm25` BM25: support.rag.BM25
- `hybrid_rrf` hybrid با RRF: support.rag.rrf
- `citations` جواب با ارجاع به منبع: support.rag.answer_question
- `grounding_check` بررسی عدد/ادعای ساختگی: support.guardrails.check_output
- `tool_agent` agent با tool calling: support.agent
- `confirmation` تأیید صریح قبل از عمل: support.agent
- `idempotency` idempotency عمل‌ها: support.tools / labkit.workflow
- `langgraph` گراف حالت LangGraph + checkpointer: support.lc.graph
- `input_guardrails` guardrail ورودی (injection، red flags): support.guardrails.check_input
- `pii_masking` پنهان کردن PII: support.guardrails.mask_pii
- `redteam_set` مجموعه‌ی red-team: eval/redteam.yaml
- `sim_user_eval` ارزیابی با کاربر شبیه‌سازی‌شده: support.evaluation
- `bootstrap_ci` فاصله‌ی اطمینان bootstrap: support.evaluation
- `llm_judge` LLM judge اعتبارسنجی‌شده (kappa): support.evaluation
- `serving` سرو با FastAPI + Docker: app/main.py
- `loadtest` load test و p95: scripts/loadtest.py
- `drift` drift با PSI: support.monitoring
- `ab_testing` A/B با SRM و guardrail: support.experiments
- `lora` fine-tune با LoRA: scripts/stage9_lora_colab.py
- `mcp` ابزارها از طریق MCP: support.panel.mcp_server
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry
- `ci_eval` ارزیابی در CI: .github/workflows/tests.yml

## گام 1: مرحله‌های ۰ تا ۹ در پنل
**یاد بگیر**
- همه در صفحه‌ی مرحله‌ها

**بساز**
- از مرحله‌ی ۰ شروع کن

**بسنج:** جدول نتایج README

**دام:** Automation Rate بدون False Automation Rate گزارش نشود.

## معیارها
- task success (CI95)
- automation / false automation
- policy violations
- recall@3
- p95

## سؤال مصاحبه
- در صفحه‌ی هر مرحله

## نسخه‌ی پیشرفته
- memory برای گفتگوی طولانی (labkit.memory)
- router مدل ارزان/قوی (labkit.ops.Router)
- tracing با Langfuse

# agent پژوهشی (deep research) با ارجاع قابل‌بررسی
_Deep-research agent with verifiable citations_ · سطح پیشرفته · 3–4 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p10_research_agent` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
تحلیلگر بازار، حقوقی یا علمی: «رقبای اصلی X در اروپا و سهم بازارشان» با گزارش و منبع برای هر ادعا.
## مسئله
سؤال چندمرحله‌ای، منابع متناقض یا بی‌کیفیت، حلقه‌ی بی‌پایان جستجو، و ادعایی که منبع واقعاً آن را نمی‌گوید.
## هدف
agent با برنامه‌ریزی، جستجوی تکراری، بودجه‌ی گام/هزینه، و بررسی اینکه هر ادعا در منبعش هست.

## پیش‌نیاز
- [p03_document_qa](../p03_document_qa/README.md)
- [p08_support_agent](../p08_support_agent/README.md)

## داده
- [HotpotQA (distractor)](https://hotpotqa.github.io/) · CC BY-SA 4.0 · سؤال چندپرشی با پاراگراف‌های پشتیبان
- [FRAMES](https://huggingface.co/datasets/google/frames-benchmark) · Apache 2.0 · سؤال‌های چندمنبعی واقعی
- [dump ویکی‌پدیا یا SearXNG محلی](https://github.com/searxng/searxng) · AGPL · جستجوی بدون API key

## قطعه‌ها
- `web_search` ابزار جستجوی وب: SearXNG (محلی) / Tavily / Brave Search API
- `doc_loaders` خواندن سند (txt/md/html/pdf/docx): labkit.loaders
- `chunking` chunking (fixed / recursive / heading): labkit.chunking
- `hybrid_rrf` hybrid با RRF: support.rag.rrf
- `reranker` reranker (cross-encoder): labkit.retrieval.Index.search
- `query_rewriting` بازنویسی query / multi-query: labkit.retrieval.multi_query_search
- `tool_agent` agent با tool calling: support.agent
- `langgraph` گراف حالت LangGraph + checkpointer: support.lc.graph
- `memory` حافظه‌ی گفتگو (خلاصه + facts): labkit.memory
- `citations` جواب با ارجاع به منبع: support.rag.answer_question
- `grounding_check` بررسی عدد/ادعای ساختگی: support.guardrails.check_output
- `llm_judge` LLM judge اعتبارسنجی‌شده (kappa): support.evaluation
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `model_router` router مدل ارزان ← قوی: labkit.ops.Router
- `tracing` tracing: OpenTelemetry / Langfuse (محلی) / LangSmith

## گام 1: حلقه‌ی ReAct با بودجه
**یاد بگیر**
- plan → search → read → reflect
- سقف گام، توکن و هزینه؛ شرط توقف

**بساز**
- ابزارها: search(query)، fetch(url)، note(fact, source)
- LangGraph با شمارنده‌ی گام و ledger هزینه

**بسنج:** میانگین گام و هزینه به ازای سؤال

**دام:** بدون بودجه، agent تا ابد جستجو می‌کند.

## گام 2: تجزیه‌ی سؤال و بازیابی چندپرشی
**یاد بگیر**
- decomposition به زیرسؤال
- multi-hop: جواب پرش اول، query پرش دوم است

**بساز**
- زیرسؤال‌ها را بساز و هر کدام را جدا جستجو کن

**بسنج:** supporting-fact recall روی HotpotQA

**دام:** زیرسؤال‌های موازی وقتی پرش دوم به جواب اول وابسته است کار نمی‌کند.

## گام 3: یادداشت با منبع و بررسی ادعا
**یاد بگیر**
- هر ادعا = (متن، url، نقل‌قول)
- claim verification: آیا نقل‌قول ادعا را پشتیبانی می‌کند

**بساز**
- گام verify: برای هر ادعا، entailment با LLM و حذف ادعای بی‌پشتوانه

**بسنج:** citation precision (ادعاهای پشتیبانی‌شده / کل)

**دام:** url درست با نقل‌قول ساختگی؛ نقل‌قول را در متن صفحه جستجو کن (با کد).

## گام 4: کیفیت منبع و گزارش
**یاد بگیر**
- اعتبار منبع، تاریخ، تناقض

**بساز**
- امتیاز منبع (دامنه، تاریخ)، گزارش تناقض‌ها
- گزارش نهایی با ارجاع

**بسنج:** دقت جواب نهایی (EM/F1 روی HotpotQA)، judge برای کامل بودن

**دام:** منبع اول نتیجه‌ی جستجو لزوماً معتبر نیست.

## معیارها
- answer F1
- supporting-fact recall
- citation precision
- steps and cost per question

## سؤال مصاحبه
- agent را چطور متوقف می‌کنی؟
- چطور مطمئن شدی citation واقعی است؟
- هزینه‌ی هر گزارش چقدر است و چطور کمش کردی؟

## نسخه‌ی پیشرفته
- multi-agent: planner، searcher، critic
- Claude با web_search سرور-ساید برای مقایسه
- ارزیابی با rubric و outcome grader

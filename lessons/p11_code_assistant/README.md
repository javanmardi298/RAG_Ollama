# دستیار کد: پرسش از codebase و agent که تست اجرا می‌کند
_Codebase assistant: repo Q&A and a test-running coding agent_ · سطح پیشرفته · 3–4 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p11_code_assistant` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
ابزارهای مثل Claude Code، Cursor، Sourcegraph Cody: «احراز هویت کجا انجام می‌شود؟» یا «این باگ را درست کن و تست را سبز کن».
## مسئله
کد ساختار دارد (تابع، کلاس، import)؛ chunk پنجره‌ای آن را خرد می‌کند. تغییر کد باید با اجرای تست تأیید شود، در محیط امن.
## هدف
بازیابی کد با AST و نماد، و agent که تغییر پیشنهاد می‌دهد، در sandbox تست اجرا می‌کند و فقط با تست سبز تمام می‌شود.

## پیش‌نیاز
- [p01_faq_search](../p01_faq_search/README.md)
- [p08_support_agent](../p08_support_agent/README.md)

## داده
- همین repo (`src/`) · ۳۰ سؤال درباره‌ی کد خودت با فایل/تابع درست
- [SWE-bench Lite](https://www.swebench.com/) · MIT · issue واقعی + تست؛ زیرمجموعه‌ی کوچک انتخاب کن

## قطعه‌ها
- `code_chunking` chunking کد با AST: labkit.chunking.python_code
- `bm25` BM25: support.rag.BM25
- `dense` dense retrieval (embedding): labkit.retrieval.Index
- `hybrid_rrf` hybrid با RRF: support.rag.rrf
- `reranker` reranker (cross-encoder): labkit.retrieval.Index.search
- `retrieval_metrics` recall@k، MRR، nDCG: labkit.metrics
- `tool_agent` agent با tool calling: support.agent
- `sandbox_exec` اجرای کد در sandbox: Docker با شبکه‌ی بسته / E2B
- `langgraph` گراف حالت LangGraph + checkpointer: support.lc.graph
- `structured_output` خروجی ساختاریافته + اعتبارسنجی + repair: labkit.structured
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `tracing` tracing: OpenTelemetry / Langfuse (محلی) / LangSmith

## گام 1: index کد
**یاد بگیر**
- chunk با AST: تابع و کلاس کامل
- نام نماد، docstring و مسیر فایل به‌عنوان زمینه

**بساز**
- labkit.chunking.python_code روی src/
- BM25 روی نام‌ها + dense روی docstring/کد

**بسنج:** recall@5 روی ۳۰ سؤال (فایل/تابع درست)

**دام:** BM25 روی snake_case و camelCase بدون شکستن نام ضعیف است؛ get_refund را به get و refund بشکن.

## گام 2: پرسش از codebase
**یاد بگیر**
- جواب با ارجاع به فایل:خط
- گراف import برای سؤال‌های «کجا صدا زده می‌شود»

**بساز**
- جواب با citation فایل:خط
- ابزار grep برای جستجوی دقیق در کنار بازیابی معنایی

**بسنج:** دقت citation

**دام:** بازیابی معنایی برای «همه‌ی جاهایی که X صدا زده می‌شود» مناسب نیست؛ grep بهتر است.

## گام 3: agent تغییر کد با تست
**یاد بگیر**
- ابزارها: read_file، search، edit، run_tests
- حلقه تا تست سبز یا بودجه

**بساز**
- sandbox Docker بدون شبکه با timeout
- agent روی ۵ باگ عمدی در کپی repo

**بسنج:** نرخ حل (تست سبز)، گام و هزینه

**دام:** agent تست را پاک یا skip می‌کند تا سبز شود؛ diff تست‌ها را ممنوع کن یا بررسی کن.

## گام 4: ارزیابی روی issue واقعی
**یاد بگیر**
- SWE-bench: patch باید تست‌های پنهان را پاس کند

**بساز**
- ۱۰ issue از SWE-bench Lite

**بسنج:** resolve rate

**دام:** اجرای کد ناشناس روی ماشین خودت بدون sandbox خطرناک است.

## معیارها
- code retrieval recall@5
- citation accuracy
- bug-fix resolve rate
- cost per fix

## سؤال مصاحبه
- کد را چطور chunk کردی؟
- agent را چطور امن اجرا کردی؟
- چطور جلوی تقلب agent با تست را گرفتی؟

## نسخه‌ی پیشرفته
- گراف فراخوانی (call graph) برای بازیابی
- MCP server برای ابزارهای repo
- ارزیابی با SWE-bench Verified

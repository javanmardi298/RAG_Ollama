# پژوهش به‌روز (اکتبر ۲۰۲۶): چه چیزی تثبیت شده، چه چیزی هنوز ادعاست، و در این repo کجا پیاده شده

> قاعدهٔ این سند: «تثبیت‌شده» = چند گروه مستقل تکرار کرده‌اند یا ابزار/استاندارد باز با استفادهٔ گسترده دارد.
> «امیدوارکننده» = نتیجهٔ خوب ولی هنوز محدود یا تکرارنشده. «احتیاط» = ادعای بزرگ با شواهد کم.
> عددها از منبع اصلی نقل شده‌اند؛ روی دادهٔ خودت دوباره بسنج.

## خلاصه در یک جدول

| حوزه | وضعیت | در این repo | پریست |
|---|---|---|---|
| Agentic RAG (route / grade / rewrite / verify / abstain) | تثبیت‌شده | `labkit.agentic_rag` | p22 |
| Contextual retrieval | تثبیت‌شده | `labkit.contextual` | p23 |
| RAG چندوجهی با late interaction (ColPali) | تثبیت‌شده برای سند بصری | ابزار بیرونی (راهنما در p23) | p23 |
| Long context در برابر RAG → مسیریابی | تثبیت‌شده (هر دو، با router) | `labkit.agentic_rag.llm_router` | p22 |
| Context engineering | تثبیت‌شده | `labkit.context` | p27 |
| بهینه‌سازی خودکار prompt (GEPA، DSPy) | تثبیت‌شده، با خطر overfitting | `labkit.optimize` | p25 |
| پایایی agent با pass^k | تثبیت‌شده | `labkit.metrics.reliability_report`، `evaluation.repeats` | p24 |
| امنیت با طراحی (CaMeL) | امیدوارکننده (هزینه بالا) | `labkit.capsec` | p28 |
| MCP (spec 2026-07-28) | استاندارد صنعتی | `support.panel.mcp_server` | p26 |
| A2A v1.0 | استاندارد نوپا (Linux Foundation) | ابزار بیرونی | p26 |
| Agent Skills (SKILL.md) | به‌سرعت در حال گسترش | قالب `skills` | p30 |
| OpenTelemetry GenAI | هنوز Development | ابزار بیرونی | p14 |
| RL با پاداش قابل‌بررسی (GRPO / RLVR) | تثبیت‌شده | ابزار بیرونی (TRL) | p29 |
| Self-consistency / best-of-n | تثبیت‌شده | `labkit.reasoning` | — |
| JEPA و world model ها | تثبیت‌شده در بینایی/ویدیو؛ پژوهشی برای LLM | `jepa_lab` + [docs/jepa.md](jepa.md) | p17–p21 |

---

## ۱. RAG

### Agentic RAG
- **چه:** بازیابی به‌صورت حلقه‌ای که سیستم کنترل می‌کند: مسیریابی (اصلاً بازیابی لازم است؟)، نمره‌دادن به شواهد، بازنویسی query وقتی چیزی پیدا نشد (corrective)، راستی‌آزمایی پاسخ، و **امتناع** وقتی شواهد کافی نیست.
- **ریشه‌ها:** [Self-RAG](https://arxiv.org/abs/2310.11511)، [Corrective RAG](https://arxiv.org/abs/2401.15884)، [Adaptive-RAG](https://arxiv.org/abs/2403.14403).
- **درس عملی:** حلقه باید **سقف** داشته باشد (`max_rounds`)، ارجاع فقط به chunk هایی که واقعاً داده شده‌اند (labkit این را فیلتر می‌کند)، و امتناع درست باید **جداگانه** ارزیابی شود (سؤال بی‌جواب در مجموعهٔ ارزیابی).
- **کجا:** `src/labkit/agentic_rag.py`؛ قالب `agentic_rag` (آفلاین با قواعد ساده اجرا می‌شود، `use_llm: true` برای Ollama).

### Contextual Retrieval
- **چه:** قبل از ایندکس، برای هر chunk یک جملهٔ زمینه (این chunk از کدام سند/بخش است) با LLM تولید و به ابتدای آن اضافه می‌شود؛ هم در embedding و هم در BM25.
- **عدد منبع** ([Anthropic](https://www.anthropic.com/news/contextual-retrieval)): کاهش شکست بازیابی top-20 به میزان ۳۵٪ با embedding زمینه‌دار، ۴۹٪ با افزودن BM25 زمینه‌دار، و ۶۷٪ با reranking.
- **هزینه:** یک فراخوانی LLM برای هر chunk → کش با hash (پیاده‌شده) و prompt caching برای متن سند.
- **کجا:** `src/labkit/contextual.py` (`meta["context"]` در `indexed_text` استفاده می‌شود).

### RAG چندوجهی و late interaction
- **چه:** به جای OCR، تصویر هر صفحه با مدل بینایی-زبان به چندین بردار (یکی برای هر patch) تبدیل و با MaxSim جست‌وجو می‌شود: [ColPali](https://arxiv.org/abs/2407.01449) / ColQwen. برای سرعت و حافظه: [MUVERA](https://arxiv.org/abs/2405.19504) (تبدیل multivector به یک بردار ثابت برای جست‌وجوی اولیه).
- **کی:** جدول، نمودار، اسلاید، فرم. برای متن ساده همان hybrid + reranker کافی و ارزان‌تر است.

### Long context در برابر RAG
- پنجره‌های ۱M توکنی RAG را حذف نکرده‌اند: هزینه/تأخیر هر سؤال بالاست و دقت روی جزئیات میانی افت می‌کند ([Lost in the Middle](https://arxiv.org/abs/2307.03172)).
- الگوی رایج: **router** — مجموعهٔ کوچک و سؤال کل‌نگر → long context؛ مجموعهٔ بزرگ یا سؤال نقطه‌ای → RAG.

---

## ۲. Agent ها

### Context engineering
- **اصول تثبیت‌شده** ([Anthropic: effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)):
  1. پنجره را بودجه بدان؛ قواعد سیستم و وظیفه را هرگز بی‌صدا حذف نکن.
  2. prefix را **پایدار** نگه دار (system، ابزارها، نوبت‌های قدیمی) تا prompt caching بخورد؛ چیزهای متغیر (chunk بازیابی‌شده، زمان) در انتها.
  3. اول برش‌های ارزان و قطعی: کوتاه‌کردن خروجی ابزار، پاک‌کردن نتایج ابزار کهنه. **خلاصه‌سازی (compaction) آخرین راه** و بعدش چک کن قواعد باقی مانده‌اند.
  4. حافظه بیرون از پنجره (فایل/پایگاه) و بازیابی در صورت نیاز.
- **کجا:** `src/labkit/context.py` (`pack`، `truncate_tool_output`، `clear_stale_tool_results`)؛ قالب `context`: در نمونهٔ آفلاین ۲۶٬۴۰۹ → ۱۰٬۸۴۵ (کوتاه‌کردن) → ۱٬۵۶۹ توکن (پاک‌کردن نتایج کهنه).

### پایایی: pass^k
- [tau-bench](https://arxiv.org/abs/2406.12045): agent ای که pass@1 خوبی دارد ممکن است در k تکرار همان وظیفه خیلی کمتر **همیشه** موفق باشد. pass^k = احتمال موفقیت در **هر** k تلاش.
- **کجا:** `labkit.metrics.pass_hat_k / reliability_report`؛ `evaluation.repeats` در `configs/project.yaml` و `scripts/stage6_eval.py`؛ پنل عدد pass^k را نشان می‌دهد. در دموی آفلاین قالب `reliability`: pass@1 = 0.875 ولی pass^4 = 0.733.

### امنیت با طراحی (CaMeL)
- [CaMeL](https://arxiv.org/abs/2503.18813): فیلترهای تشخیص injection در برابر حملهٔ تطبیقی شکست می‌خورند. راه طراحی‌محور: planner ممتاز فقط درخواست کاربر را می‌بیند؛ محتوای غیرقابل‌اعتماد در گام قرنطینه (بدون ابزار) پردازش می‌شود و هر مقدار **منبع** (provenance) دارد؛ policy نوشته‌شده در **کد** قبل از هر فراخوانی ابزار منبع آرگومان‌ها را چک می‌کند.
- **هزینه:** حدود ۲.۸ برابر توکن در گزارش اصلی؛ از کیفیت متن محافظت نمی‌کند، از جریان کنترل و داده محافظت می‌کند.
- **کجا:** `src/labkit/capsec.py`؛ قالب `capsec` (پرداخت تزریق‌شده از ایمیل مسدود می‌شود، پرداخت به گیرندهٔ مورد اعتماد با تأیید کاربر انجام می‌شود).
- همین فلسفه از قبل در پروژه بود: قواعد سیاست در کد (`support.policy`)، تأیید صریح، idempotency، allow-list وظایف پنل، و ممنوعیت تغییر مجوزهای Claude توسط خودش.

### MCP و A2A
- **MCP** ([spec](https://modelcontextprotocol.io/specification)) — نسخهٔ 2026-07-28: هستهٔ stateless، حذف session ها، و منسوخ شدن Roots/Sampling/Logging. یعنی server باید هر درخواست را مستقل پاسخ دهد؛ حالت را در لایهٔ خودت نگه دار.
  سرور پنل این repo روی mcp 1.x (FastMCP) و 2.x (MCPServer) کار می‌کند و ابزارها stateless هستند.
- **A2A** ([a2a-protocol.org](https://a2a-protocol.org/)) — v1.0 (مارس ۲۰۲۶، Linux Foundation): Agent Card امضاشده، task و streaming بین agent ها. **MCP = ابزار/داده برای یک agent؛ A2A = agent با agent.**
- **امنیت MCP:** کمترین دسترسی، allow-list مسیر، رد خواندن اسرار، تأیید برای نوشتن؛ به توضیح ابزارهای شخص ثالث اعتماد نکن (tool poisoning). قالب `mcp` همهٔ این‌ها را با self-test دارد.

### Agent Skills
- پوشه‌ای با `SKILL.md` (frontmatter: `name`، `description` که می‌گوید «کی استفاده شود») + اسکریپت و مرجع. فقط نام و توضیح در context می‌ماند تا وقتی لازم شود (**progressive disclosure**). استاندارد باز ([agentskills.io](https://agentskills.io/)) و پشتیبانی در Claude Code / Agent SDK و ده‌ها پلتفرم دیگر.
- **کجا:** قالب `skills` (سه skill نمونه + اعتبارسنج + تست فعال‌سازی).

### Observability
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) هنوز در وضعیت **Development** هستند: نام attribute ها ممکن است تغییر کنند. لاگ ساختاریافتهٔ خودت (مثل `labkit.ops.Ledger`) را نگه دار و به OTel نگاشت کن، نه برعکس.

---

## ۳. بهینه‌سازی و آموزش

### بهینه‌سازی خودکار prompt
- [GEPA](https://arxiv.org/abs/2507.19457) (ICLR 2026): LLM روی اجراهای ناموفق بازتاب می‌کند و prompt را ویرایش می‌کند؛ نامزدها روی جبههٔ پارتو نگه داشته می‌شوند. در [DSPy](https://dspy.ai/) هم موجود است.
- **هشدار عملی:** overfitting. یک مطالعهٔ موردی: دقت train تا ۹۵٪ بالا رفت، test به ۸۵٪ افتاد و prompt از ~۲٬۴۰۰ به ~۸٬۸۰۰ کاراکتر رسید.
- **کجا:** `src/labkit/optimize.py` انتخاب نهایی را روی **validation** انجام می‌دهد، رشد طول را جریمه می‌کند و کل تاریخچه را برمی‌گرداند. قالب `optimize` test را فقط یک بار در پایان می‌سنجد.

### استدلال در زمان استنتاج
- self-consistency (رأی اکثریت چند نمونه) و best-of-n با امتیازدهنده؛ «agreement» پایین خودش سیگنال عدم اطمینان است → ارجاع به انسان.
- **کجا:** `src/labkit/reasoning.py`.

### RL با پاداش قابل‌بررسی (GRPO / RLVR)
- [GRPO](https://arxiv.org/abs/2402.03300): به جای critic، مزیت نسبی در گروهی از نمونه‌ها برای یک prompt. وقتی پاسخ قابل‌بررسی است (اجرای SQL، تست کد، اعتبار JSON) RL مستقیماً موفقیت را بهینه می‌کند.
- **خطر:** reward hacking و انفجار طول پاسخ. **کجا:** پریست p29 با [TRL GRPOTrainer](https://huggingface.co/docs/trl/main/en/grpo_trainer) و `labkit.sqlguard` برای اجرای امن.

---

## ۴. JEPA و world model ها
خلاصه: در بینایی و ویدیو تثبیت‌شده (I-JEPA، V-JEPA، V-JEPA 2 با کد و وزن باز)؛ LeJEPA/SIGReg روش ساده و اصولی‌تری برای جلوگیری از collapse است؛ world model های نهفته (V-JEPA 2-AC، DINO-WM، TD-MPC2، LeWorldModel) برنامه‌ریزی بدون پاداش را ممکن کرده‌اند. برای عامل‌های متنی مثل پروژهٔ پشتیبانی، JEPA هنوز مزیت عملی اثبات‌شده ندارد.
آموزش کامل، مقایسه با معادل‌ها و نتایج اجراشده: **[docs/jepa.md](jepa.md)**.

---

## ۵. «احتیاط»: ادعاهایی که هنوز برای تصمیم production کافی نیستند
- «RAG مرده است چون context طولانی شده» — نه؛ هزینه و دقت جزئیات (بالا را ببین).
- «یک agent خودمختار همه‌کاره» — در عمل workflow های تعریف‌شده + agent در نقاط محدود پایاترند (pass^k را بسنج).
- «فیلتر prompt injection مشکل را حل کرده» — حملهٔ تطبیقی از فیلتر می‌گذرد؛ دفاع طراحی‌محور لازم است.
- پیش‌چاپ‌های ۲۰۲۶ JEPA برای حوزه‌های خاص (رانندگی، تصمیم‌گیری) — ایده‌های خوب، تا تکرار مستقل صبر کن.
- «بهینه‌سازی prompt همیشه بهتر از دستی است» — فقط با validation/test جدا و گزارش هزینه.

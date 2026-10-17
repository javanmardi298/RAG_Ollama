# پنل کنترل و اتصال به Claude

پنل یک برنامه‌ی محلی روی لپ‌تاپ است که همه‌ی پروژه را از یک جا مدیریت می‌کند: پیش‌نیازها، داده، پارامترها، اجرای هر مرحله با لاگ زنده، نتایج و نمودارها، مقایسه‌ی اجراها، چت با خود agent، و یادآوری‌هایی که با کد از وضعیت پروژه ساخته می‌شوند. Claude از دو راه به همین پنل وصل می‌شود.

```
                 ┌──────────── لپ‌تاپ (ویندوز) ─────────────────────────────────────────┐
 مرورگر ──HTTP──▶ │ python -m support.panel  (FastAPI روی 127.0.0.1:8765)                │
                 │        │                                                              │
 Claude Desktop ─stdio─▶ │ python -m support.panel.mcp_server  (همان ابزارها، از طریق MCP)  │
                 │        │                                                              │
                 │        ▼                                                              │
                 │   panel/service.py  ← یک لایه‌ی ابزار برای هر سه رابط                  │
                 │        │                       │                                      │
                 │   configs/project.yaml     runner → job wrapper → scripts/stageN.py    │
                 │   (پارامترهای معتبرسازی‌شده)        │                                  │
                 │                              results/ + results/panel.db (تاریخچه)     │
                 │   Ollama (localhost:11434) ◀── agent، RAG، مشتری شبیه‌سازی‌شده          │
                 └──────────────────────────────────────────────────────────────────────┘
 چت مستقیم در پنل ──HTTPS──▶ api.anthropic.com  (فقط اگر کلید API در .env باشد)
```

## نصب روی ویندوز (یک بار)

1. **Python 3.11** از python.org (تیک «Add python.exe to PATH»).
2. **Ollama** از ollama.com/download/windows. بعد از نصب، آیکونش در system tray است.
3. در PowerShell، داخل پوشه‌ی پروژه:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\windows\setup.ps1                  # برای نسخه‌ی LangChain هم: .\windows\setup.ps1 -WithLangChain
   ```
   این اسکریپت محیط مجازی `.venv` را می‌سازد، پکیج‌ها را نصب می‌کند، `.env` را می‌سازد، مدل Ollama را pull می‌کند و تست‌ها را اجرا می‌کند.
4. **اجرای پنل:** دوبار کلیک روی `windows\start_panel.bat`. مرورگر روی `http://127.0.0.1:8765` باز می‌شود.

## اتصال Claude

| راه | چه لازم است | چطور |
|---|---|---|
| **Claude Desktop (MCP)** | Claude Desktop نصب باشد؛ کلید API لازم نیست | صفحه‌ی «اتصال‌ها» ← «نصب در Claude Desktop» (یا `windows\install_claude_desktop.bat`)، بعد Claude Desktop را کامل ببند (Quit از system tray) و باز کن. در Settings → Developer باید `support-agent` دیده شود. |
| **چت مستقیم در پنل** | کلید Anthropic API (هزینه جدا از اشتراک) | صفحه‌ی «اتصال‌ها» ← کلید را وارد کن؛ در `.env` ذخیره می‌شود. مدل و effort در تنظیمات بخش `claude`. |

هر دو راه همان ۱۸ ابزار را دارند: `project_status`، `get_stage`، `get_settings`، `update_settings`، `run_task`، `run_status`، `compare_runs`، `get_advice`، `chat_with_agent`، `read_project_file` و بقیه. Claude نمی‌تواند دستور دلخواه shell اجرا کند، `.env` را بخواند، یا اجازه‌های خودش را عوض کند. فقط taskهای فهرست‌شده در `panel/catalog.py` قابل اجرا هستند. در تنظیمات `claude.allow_runs` و `claude.allow_settings_changes` را می‌توانی خاموش کنی.

نمونه‌ی درخواست‌ها (در Claude Desktop یا پنل):
- «وضعیت پروژه را بگو و قدم بعدی چیست؟»
- «چرا اجرای آخر مرحله‌ی ۲ شکست خورد؟»
- «rag.k را ۵ کن، مرحله‌ی ۲ را اجرا کن و با اجرای قبلی مقایسه کن.»
- «منحنی risk-coverage مرحله‌ی ۴ را برایم توضیح بده، با عددهای خودم.»
- «با agent به‌عنوان مشتری حرف بزن و سعی کن سفارش کس دیگری را ببینی.»

## روال کار با پنل

1. **اتصال‌ها و پیش‌نیازها:** همه‌ی موارد قرمز را سبز کن. هر مورد راه‌حلش را نشان می‌دهد.
2. **مرحله‌ی ۰:** «ساخت داده و دیتابیس»، بعد «اجرای همه‌ی تست‌ها».
3. برای هر مرحله: تب **آموزش** (مفهوم، چرایی، قدم‌ها، دام‌ها) ← تب **پارامترها** ← دکمه‌ی **▶ اجرا** ← **لاگ زنده** ← تب **نتایج** ← یک پارامتر را عوض کن و دوباره اجرا کن ← تب **مقایسه‌ی اجراها**.
4. ستون «یادآوری‌ها و پیشنهادها» را جدی بگیر. مثلاً می‌گوید کدام نتیجه بعد از تغییر پارامتر قدیمی شده، یا کدام بند آگهی هنوز مدرک ندارد.
5. **پوشش آگهی / رزومه:** برای هر بند آگهی، عددهای واقعی تو و یک پیش‌نویس خط رزومه.

## ساختار فایل‌ها

```
configs/project.yaml          همه‌ی پارامترهای آزمایش (معتبرسازی: src/support/settings.py)
src/support/runtime.py        ساختن agent، retriever و classifier طبق تنظیمات (مشترک بین اسکریپت‌ها، API و پنل)
src/support/panel/
  catalog.py                  محتوای آموزشی و taskهای هر مرحله (فهرست مجاز دستورها)
  service.py                  ابزارها: یک لایه برای پنل، MCP و چت Claude
  runner.py, job.py           اجرای جدا از پنل، توقف، لاگ
  registry.py                 تاریخچه در results/panel.db
  preflight.py                بررسی پیش‌نیازها (Python، پکیج‌ها، Ollama، داده، دیسک، GPU، git)
  advisor.py                  یادآوری‌ها و پوشش آگهی (با کد)
  results.py                  خواندن نتایج هر مرحله
  mcp_server.py               سرور MCP برای Claude Desktop
  claude_desktop.py           نصب در claude_desktop_config.json (با backup)
  claude_chat.py              چت مستقیم با Claude API (حلقه‌ی tool use)
  web.py, static/             رابط کاربری
windows/                      setup.ps1, start_panel.bat, install_claude_desktop.bat
```

## مشکلات رایج

- **پنل باز نمی‌شود:** پنجره‌ی `start_panel.bat` را ببین؛ اگر نوشته `.venv` نیست، `setup.ps1` را اجرا کن.
- **Ollama قرمز است:** Ollama را از منوی Start باز کن؛ آدرس پیش‌فرض `http://localhost:11434` است (تنظیمات ← `llm.host`).
- **Claude Desktop ابزارها را نمی‌بیند:** Claude Desktop را کامل ببند (نه فقط پنجره). اگر نسخه‌ی Microsoft Store نصب است، پنل در هر دو مسیر config می‌نویسد. لاگ: `%APPDATA%\Claude\logs\mcp-server-support-agent.log`.
- **اجرا «lost» شد:** کامپیوتر خاموش شده یا پروسه کشته شده؛ دوباره اجرا کن.
- **حروف آلمانی/فارسی در لاگ خراب است:** پنل همه‌ی اجراها را با `PYTHONUTF8=1` اجرا می‌کند؛ اگر اسکریپت را دستی اجرا می‌کنی، قبلش `set PYTHONUTF8=1`.

## پروژه‌ها (پریست‌ها) و نقشه‌ی راه

۳۰ پروژه‌ی واقعی در `presets/projects/` از پایه تا پیشرفته. هر پروژه این‌ها را دارد: کاربرد واقعی، مسئله، هدف، پیش‌نیاز، داده با لایسنس، stack، قطعه‌ها، مرحله‌ها (یاد بگیر / بساز / بسنج / دام)، معیار، guardrail، نکته‌های production، سؤال مصاحبه، نسخه‌ی پیشرفته و خط رزومه.

| سطح | پروژه‌ها |
|---|---|
| پایه | ۱ جستجوی FAQ، ۲ جستجوی محصول (WANDS)، ۳ پرسش‌وپاسخ روی اسناد با citation، ۴ طبقه‌بندی تیکت |
| میانی | ۵ استخراج فاکتور + workflow تأیید، ۶ Text-to-SQL، ۷ workflow ایمیل، ۸ همین support agent، ۹ RAG چندزبانه (فارسی) |
| پیشرفته | ۱۰ agent پژوهشی، ۱۱ دستیار کد، ۱۲ multi-agent خسارت بیمه، ۱۳ GraphRAG، ۱۴ پلتفرم LLMOps، ۱۵ fine-tune و distillation، ۱۶ امنیت و red-team |
| JEPA و World Model | ۱۷ مبانی JEPA (پایه)، ۱۸ collapse و SIGReg، ۱۹ world model و برنامه‌ریزی CEM، ۲۰ پایش با surprise، ۲۱ V-JEPA 2 روی ویدیو (پیشرفته) — آموزش: [jepa.md](jepa.md) |
| تکنیک‌های ۲۰۲۶ | ۲۲ Agentic RAG، ۲۳ contextual و RAG چندوجهی، ۲۴ پایایی agent (pass^k)، ۲۵ بهینه‌سازی prompt، ۲۶ MCP و A2A، ۲۷ context engineering، ۲۸ agent امن (CaMeL)، ۲۹ RL با GRPO، ۳۰ Agent Skills — منابع: [research_2026.md](research_2026.md) |

- **سندها در پنل:** منوی کناری «آموزش JEPA و World Model» و «پژوهش ۲۰۲۶» همین فایل‌های markdown را داخل پنل نمایش می‌دهد (`#/doc?path=docs/jepa.md`).
- **پنل:** «پروژه‌ها و پریست‌ها»: فیلتر سطح و مسیر، تیک زدن مرحله‌ها، و «ساخت اسکلت پروژه». این دکمه پوشه‌ی `projects/<id>/` را با README کامل، `config.yaml` و یک `run.py` قابل اجرا روی labkit می‌سازد.
- **قطعه‌ها:** فایل `presets/components.yaml` وضعیت هر قطعه را می‌گوید: **در سیستم** (تست‌شده در repo)، **labkit** (تازه اضافه‌شده در `src/labkit/`) یا **بیرونی** (ابزار شناخته‌شده‌ای که نصب یا وصل می‌کنی، مثل OCR، پایگاه برداری، جستجوی وب، tracing).
- **پریست‌های پارامتر** (`presets/settings/`) برای همین پروژه: تست سریع، لپ‌تاپ بدون GPU، ارزیابی کامل، تمرکز آلمانی، ایمنی سخت‌گیرانه، شبیه production، و Claude فقط مشاور. از صفحه‌ی «همه‌ی پارامترها» اعمال می‌شوند.
- **Claude:** ابزارهای `list_presets`، `get_preset`، `scaffold_preset`، `set_preset_progress`، `list_settings_presets` و `apply_settings_preset`. Claude نمی‌تواند با پریست، اجازه‌های خودش را عوض کند.
- **نسخه‌ی آنلاین (Artifact در claude.ai):** همین نقشه‌ی راه همراه با ثبت پیشرفت خصوصی و پرسش از Claude. برای ساختن دوباره‌اش بعد از تغییر پریست‌ها: `python -m support.panel.presets html out.html`.
- **اعتبارسنجی:** `python -m support.panel.presets check` (در تست‌ها هم اجرا می‌شود).

### labkit: قطعه‌هایی که برای این پروژه‌ها اضافه شد
`loaders` (txt/md/html/pdf/docx و حذف سرصفحه) · `chunking` (fixed، recursive، heading، AST برای کد) · `retrieval` (index عمومی BM25/dense/hybrid، فیلتر metadata، reranker، MMR، multi-query) · `metrics` (recall، MRR، nDCG درجه‌دار، F1 فیلدی) · `structured` (اعتبارسنجی JSON با pydantic و یک دور repair) · `sqlguard` (فقط SELECT، جدول مجاز، LIMIT، اتصال read-only، execution accuracy) · `workflow` (retry، resume، idempotency، تأیید انسانی، audit) · `ops` (کش، ledger هزینه، router مدل ارزان ← قوی، نسخه‌گذاری prompt) · `graph` (گراف دانش، مسیر چندپرشی با منبع) · `memory` (حافظه‌ی گفتگو) · `agentic_rag` (route/grade/rewrite/verify/abstain) · `contextual` (contextual retrieval با کش) · `context` (بودجه‌ی context، prefix پایدار، پاک‌کردن tool result کهنه) · `optimize` (بهینه‌سازی prompt به سبک GEPA با validation و جریمه‌ی طول) · `reasoning` (self-consistency، best-of-n) · `capsec` (provenance و policy ابزار به سبک CaMeL) · `metrics.reliability_report` (pass^k).
`jepa_lab` (نیاز به PyTorch): `ssl` (I-JEPA کوچک)، `sigreg` (LeJEPA و تشخیص collapse)، `world_model` (world model نهفته، CEM-MPC، surprise).

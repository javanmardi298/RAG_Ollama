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

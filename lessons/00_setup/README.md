# راه‌اندازی (یک بار، حدود ۳۰ دقیقه)

این صفحه همه‌چیز را از صفر توضیح می‌دهد: Python، محیط مجازی، نصب پروژه، و **اتصال مدل زبانی** (Ollama، Claude، OpenCode یا هر سرور سازگار با OpenAI). اگر فقط می‌خواهی درس‌ها را امتحان کنی، تا بخش «۳» برو؛ درس‌ها بدون هیچ مدل واقعی هم اجرا می‌شوند (مدل `offline`).

## ۱. نصب Python و گرفتن پروژه

**Windows (PowerShell):**
```powershell
winget install Python.Python.3.12        # یا از python.org (تیک «Add python to PATH» را بزن)
git clone https://github.com/javanmardi298/rag_ollama.git
cd rag_ollama
git checkout ccr-f5e84f2b-jub2kh          # شاخه‌ای که درس‌ها در آن هستند (بعد از merge: main)
python -m venv .venv
.\.venv\Scripts\Activate.ps1              # اگر خطای ExecutionPolicy داد: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install -U pip
pip install -r requirements.txt -r requirements-panel.txt
pip install -e .   # (the .bat files also work without this step)
```
**Linux / macOS:**
```bash
git clone https://github.com/javanmardi298/rag_ollama.git && cd rag_ollama
git checkout ccr-f5e84f2b-jub2kh
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt -r requirements-panel.txt && pip install -e .   # (the .bat files also work without this step)
```
**چرا venv؟** تا نسخه‌ی کتابخانه‌های این پروژه با بقیه‌ی پروژه‌های سیستم قاطی نشود. هر بار ترمینال جدید باز می‌کنی دوباره فعالش کن.

## ۲. بررسی نصب
```bash
python lessons/00_setup/check_env.py
python -m learn list
python -m pytest -q                       # همه‌ی تست‌های پروژه (حدود نیم دقیقه)
```
خروجی `check_env.py` می‌گوید چه چیزی نصب است و برای هر ارائه‌دهنده‌ی مدل چه چیزی کم است. هیچ کلیدی را چاپ نمی‌کند.

## ۳. اولین درس (بدون هیچ مدل)
```bash
python -m learn start p01_faq_search
```
مدل پیش‌فرض درس‌ها `offline` است: یک شبیه‌ساز بدون مدل واقعی که شکل کار را نشان می‌دهد و تست‌ها را قابل‌اجرا می‌کند. **جواب‌های واقعی** با یکی از ارائه‌دهنده‌های زیر می‌آیند.

## ۴. اتصال مدل زبانی

| ارائه‌دهنده | `LEARN_PROVIDER` | چه می‌خواهد | هزینه | حریم داده |
|---|---|---|---|---|
| شبیه‌ساز | `offline` | هیچ | صفر | کامل محلی |
| Ollama | `ollama` | نصب Ollama + دانلود مدل | صفر (سخت‌افزار خودت) | کامل محلی |
| Claude (API) | `anthropic` | کلید API از Console | به‌ازای توکن | داده به سرور Anthropic می‌رود |
| OpenCode | `opencode` | نصب OpenCode + ورود به یک provider | بسته به provider | بسته به provider |
| سرور سازگار با OpenAI | `openai_compatible` | آدرس (LM Studio، vLLM، OpenRouter) | بسته به سرور | بسته به سرور |

انتخاب با متغیر محیطی (برای همه‌ی درس‌ها و اسکریپت‌ها):
```powershell
# PowerShell (فقط همین ترمینال)
$env:LEARN_PROVIDER = "ollama"
$env:LEARN_MODEL    = "qwen2.5:7b"
```
```bash
# bash
export LEARN_PROVIDER=ollama LEARN_MODEL=qwen2.5:7b
```
در Jupyter/Colab: `os.environ["LEARN_PROVIDER"] = "anthropic"` در اولین سلول.

### ۴-الف. Ollama (محلی و رایگان)
1. نصب از [ollama.com](https://ollama.com/download) (Windows: نصب‌کننده‌ی exe).
2. `ollama pull qwen2.5:7b` (حدود ۴.۷ گیگابایت؛ روی لپ‌تاپ بدون GPU کند ولی کار می‌کند. مدل کوچک‌تر: `qwen2.5:3b`).
3. `pip install ollama`، سپس `LEARN_PROVIDER=ollama`.
4. بررسی: `ollama list` و `python lessons/00_setup/check_env.py` (خط «server running» باید ✓ باشد).

### ۴-ب. Claude از طریق API
1. در [console.anthropic.com](https://console.anthropic.com) حساب بساز، اعتبار اضافه کن و یک **API key** بساز.
2. در ریشه‌ی پروژه فایل `.env` بساز (در `.gitignore` هست و commit نمی‌شود):
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. `pip install anthropic`، سپس `LEARN_PROVIDER=anthropic` و `LEARN_MODEL=` نام مدل (مثلاً `claude-sonnet-5-5`؛ نام‌های فعلی در مستندات Anthropic).
4. **سقف هزینه** (توصیه‌ی جدی): قیمت مدل را از صفحه‌ی قیمت‌ها بردار و بگذار:
   ```bash
   export LEARN_BUDGET_USD=1 LEARN_PRICE_IN=<دلار برای هر میلیون توکن ورودی> LEARN_PRICE_OUT=<... خروجی>
   ```
   بعد از رسیدن به تخمین ۱ دلار، فراخوانی‌ها متوقف می‌شوند (`BudgetExceeded`). عدد، تخمین است؛ سقف واقعی را در Console هم بگذار.

> **مهم:** اشتراک Claude.ai (Pro/Max) **کلید API نیست**. با آن در Claude Desktop و Claude Code کار می‌کنی، ولی کد خودت (و ابزارهای شخص ثالث) طبق شرایط Anthropic باید از کلید API استفاده کند ([گزارش The Register](https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access)). شرایط را از منبع رسمی هم چک کن، چون تغییر می‌کند.

### ۴-ج. OpenCode (مدل‌های خودِ OpenCode)
[OpenCode](https://opencode.ai/docs/cli) یک عامل کدنویسی خط فرمان است که به ده‌ها provider وصل می‌شود. درس‌ها می‌توانند از همان مدل‌ها استفاده کنند، بدون اینکه کلیدی در این پروژه بگذاری.
1. نصب طبق [opencode.ai](https://opencode.ai) (مثلاً `npm i -g opencode-ai`؛ دستور فعلی را از سایت بردار).
2. وارد provider شو: `opencode auth login` (یا داخل برنامه `/connect`).
3. بررسی: `opencode models` لیست مدل‌ها را به شکل `provider/model` می‌دهد.
4. `LEARN_PROVIDER=opencode` و `LEARN_MODEL=provider/model`.
هر فراخوانی `opencode run -m provider/model "..."` اجرا می‌کند؛ کند است ولی ساده. محدودیت: در این حالت فقط متن و JSON داریم، نه tool calling.

### ۴-د. سرور سازگار با OpenAI (LM Studio، vLLM، OpenRouter)
```bash
export LEARN_PROVIDER=openai_compatible LEARN_API_BASE=http://localhost:1234/v1 LEARN_MODEL=<نام مدل>
export OPENAI_API_KEY=...   # فقط اگر سرور می‌خواهد
```

### ۴-ه. Claude و OpenCode در نقش «معلم»
جدا از اینکه کدِ درس کدام مدل را صدا بزند، می‌توانی از Claude یا OpenCode بخواهی **راهنمای تو** باشند:
- **Claude Desktop / Claude Code:** MCP server پنل را نصب کن (`windows\install_claude_desktop.bat`). بعد بگو: «درس p01 را با من جلو ببر». ابزارهای `lessons_list`، `lesson_step`، `lesson_check`، `lesson_hint` را می‌بیند. **حالت معلم:** راهنمایی می‌دهد ولی جواب کامل (`solution.py`) را نمی‌تواند بخواند.
- **OpenCode:** در `opencode.json` پروژه:
  ```json
  { "mcp": { "support-panel": { "type": "local", "command": ["python", "-m", "support.panel.mcp_server"], "enabled": true } } }
  ```
  (قالب دقیق را در [مستندات MCP در OpenCode](https://opencode.ai/docs) چک کن.)
- دستور پیشنهادی: «معلم من باش: هر بار یک راهنمایی بده، جواب نده، و بعد از هر راهنمایی بپرس چه فکر می‌کنی.»

## ۵. حریم خصوصی و امنیت
- **داده‌ی واقعی مشتری/شرکت را به مدل ابری نفرست** مگر اجازه داری. درس‌ها فقط داده‌ی ساختگی دارند.
- `.env` را هرگز commit نکن. قبل از push: `git status` و `git diff --cached` را نگاه کن.
- اگر کلیدی را اشتباهاً push کردی: فوراً در Console آن را **باطل (revoke)** کن؛ پاک کردن commit کافی نیست.
- پوشه‌ی `work/` (پاسخ‌های تو) در `.gitignore` است.

## ۶. بدون نصب: Colab و Codespaces
- **Colab:** هر درس یک notebook دارد (`lessons/<درس>/<درس>.ipynb`)؛ دکمه‌ی «Open in Colab» بالای آن است. برای درس‌های JEPA/GPU بهترین مسیر است.
- **GitHub Codespaces:** روی repo «Code ← Codespaces ← Create». محیط خودکار نصب می‌شود. Ollama روی CPU آنجا کند است؛ `anthropic` یا `opencode` مناسب‌تر است.

## ۷. اگر گیر کردی
[رفع اشکال](../troubleshooting.md) و [واژه‌نامه](../glossary.md). خطاهایی که می‌خوری در `work/errors.md` ثبت می‌شود (`python -m learn errors`).

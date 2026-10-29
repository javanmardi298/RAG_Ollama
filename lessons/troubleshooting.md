# رفع اشکال

هر خطایی که می‌خوری در `work/errors.md` ثبت می‌شود (`python -m learn errors`)؛ کنار آن «چه چیزی درستش کرد» را بنویس تا دفعه‌ی بعد سریع‌تر باشی.

| علامت | علت و راه‌حل |
|---|---|
| `No module named learn` | `pip install -e .` را در محیط فعال (venv) اجرا نکرده‌ای |
| `ModuleNotFoundError: torch` | فقط درس‌های JEPA: `pip install -r requirements-jepa.txt` |
| تست‌ها `not implemented yet: TODO` | طبیعی است؛ هنوز کد را ننوشته‌ای (یا فایل پاسخ را ذخیره نکرده‌ای) |
| `python -m learn check` فایل را پیدا نمی‌کند | اول `python -m learn show <درس> <گام>` را بزن تا `work/.../answer.py` ساخته شود |
| تست پاس نمی‌شود ولی کد درست به نظر می‌رسد | خط ✗ را بخوان؛ پیام می‌گوید چه چیزی مورد انتظار بود. بعد `hint` |
| `ConnectionError` به Ollama | Ollama اجرا نیست: `ollama serve` و `ollama list`؛ آدرس `OLLAMA_HOST` |
| `ANTHROPIC_API_KEY is not set` | کلید را در `.env` بگذار (اشتراک Claude.ai کلید API نیست) |
| `BudgetExceeded` | سقف `LEARN_BUDGET_USD` تمام شد؛ درست کار می‌کند. سقف را بالا ببر یا مدل ارزان‌تر |
| `opencode is not on PATH` / `opencode failed` | OpenCode نصب نیست یا وارد provider نشده‌ای (`opencode auth login`) |
| PowerShell اجازه‌ی فعال کردن venv را نمی‌دهد | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| متن فارسی در ترمینال Windows خراب است | `chcp 65001` و `$env:PYTHONUTF8="1"` |
| `UnicodeDecodeError` هنگام خواندن فایل | فایل را با `encoding="utf-8"` باز کن |
| notebook در Colab `ModuleNotFoundError` | اولین سلول (Setup) را اجرا نکرده‌ای |
| JEPA کند است | طبیعی روی CPU؛ `--epochs` را کم کن یا Colab با GPU |

# گام ۱: تنظیم ارائه‌دهنده‌ی مدل از روی محیط (config)

## هدف این گام
تابعی می‌نویسی که متغیرهای محیطی (`LEARN_PROVIDER`، `LEARN_MODEL`، …) را می‌خواند، **اعتبارسنجی** می‌کند و یک تنظیم تمیز برمی‌گرداند. یادگیری اصلی: تنظیمات یک سیستم LLM را در **یک نقطه** جمع کن و خطای تنظیم را زود و واضح بگیر، نه وسط یک اجرای ۲۰ دقیقه‌ای.

## پیش‌نیاز
دیکشنری و استثنا در Python. [00_setup](../../00_setup/README.md) را برای معنی هر ارائه‌دهنده ببین.

## مفهوم
ارائه‌دهنده‌ها فرق دارند ولی رابط ما یکی است (`chat` و `json`). تنها چیزی که عوض می‌شود **تنظیم** است:

| ارائه‌دهنده | `LEARN_MODEL` | شرط | پیش‌فرض مدل |
|---|---|---|---|
| `offline` | ندارد | هیچ | — |
| `ollama` | نام مدل | سرور Ollama | `qwen2.5:7b` |
| `anthropic` | نام مدل Claude | کلید `ANTHROPIC_API_KEY` | `claude-sonnet-5-5` |
| `opencode` | `provider/model` | OpenCode نصب باشد | ندارد (**الزامی**) |
| `openai_compatible` | نام مدل | `LEARN_API_BASE` | ندارد (**الزامی**) |

قواعد `resolve_config(env)`:
1. `provider = env.get("LEARN_PROVIDER", "offline")`؛ ناشناخته ← `ValueError("unknown provider ...")`.
2. `model = env.get("LEARN_MODEL")` یا پیش‌فرض جدول.
3. `opencode` بدون مدل، یا مدل بدون `/` ← `ValueError` (باید `provider/model` باشد).
4. `openai_compatible` بدون `LEARN_API_BASE` ← `ValueError`.
5. `anthropic` بدون کلید (`ANTHROPIC_API_KEY` در `env`) ← `ValueError` (اشتراک Claude.ai کلید نیست).
6. بودجه: `LEARN_BUDGET_USD` (پیش‌فرض ۰ = بدون سقف) به `float`؛ منفی یا غیرعددی ← `ValueError`.
7. خروجی: `{"provider", "model", "api_base", "budget_usd", "cloud": bool}` که `cloud` برای `anthropic` و `openai_compatible` درست است (داده به بیرون می‌رود).

## تمرین کد
فایل پاسخ: `work/m01_compare_models/step01_provider_config/answer.py`

## اجرا کن
```bash
python -m learn check m01_compare_models 1
```

## خروجی مورد انتظار
هفت ✓.

## اگر فرق داشت
| علامت | علت رایج |
|---|---|
| `float("abc")` استثنای دیگری داد | `ValueError` خودت را با پیام واضح بالا بیاور |
| مدل پیش‌فرض ollama خالی است | از جدول پیش‌فرض‌ها استفاده نکرده‌ای |

## دام‌ها
- هرگز **مقدار** کلید را چاپ یا لاگ نکن؛ فقط وجود آن را بررسی کن.
- پیش‌فرض‌های مدل با زمان کهنه می‌شوند؛ نام مدل‌های فعلی را از مستندات هر ارائه‌دهنده بگیر.

## گام بعد
[گام ۲: آزمون](../step02_benchmark/lesson.md)

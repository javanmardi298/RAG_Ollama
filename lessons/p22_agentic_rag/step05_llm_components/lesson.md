# گام ۵: اجزای مبتنی بر مدل زبانی (Ollama / Claude / OpenCode)

## هدف این گام
قاعده‌های گام‌های قبل را با **مدل زبانی** عوض می‌کنی: مسیریاب، grader، بازنویس و verifier. کدهای آماده‌ی `labkit.agentic_rag` را به یک مدل وصل می‌کنی و رفتار دو عامل (قاعده‌ای و مدلی) را روی همان سؤال‌ها مقایسه می‌کنی.

## پیش‌نیاز
گام‌های ۱ تا ۴. برای اجرای واقعی یکی از ارائه‌دهنده‌ها (Ollama، Claude، OpenCode) طبق [00_setup](../../00_setup/README.md). بدون آن، مدل `offline` اجرا می‌شود که فقط شکل کار را نشان می‌دهد.

## مفهوم
قاعده‌های ما سریع و قابل‌تست‌اند ولی معنا را نمی‌فهمند: «bank transfer» و «return transfer» برایشان یکی است. یک **مدل زبانی** می‌تواند بپرسد «آیا این متن به این سؤال کمک می‌کند؟» و جواب ساخت‌یافته بدهد (`{"relevant": true}`). بهای آن: هر تکه یک فراخوانی (هزینه، تأخیر) و احتمال خطای خود مدل.

**اصل مهندسی:** مدل را **پشت یک رابط ثابت** بگذار: `llm.chat(messages)` برای متن و `llm.json(messages, schema)` برای خروجی ساخت‌یافته. بعد Ollama، Claude یا OpenCode فقط یک تنظیم است و **تست‌ها بدون مدل واقعی** (با مدل ساختگی) اجرا می‌شوند. دقیقاً همین کار را در `support/providers.py` کرده‌ایم.

اجزای آماده در `labkit.agentic_rag`:

| تابع | مدل چه می‌گوید | schema |
|---|---|---|
| `llm_router(llm)` | `direct` / `retrieve` / `multi_hop` | `{"route": enum}` |
| `llm_grader(llm)` | آیا تکه مرتبط است | `{"relevant": bool}` |
| `llm_rewriter(llm)` | query های تازه | `{"queries": [str]}` |
| `llm_verifier(llm)` | آیا پاسخ از منابع پشتیبانی می‌شود | `{"supported": bool, ...}` |

کلاس `AgenticRAG` همان حلقه‌ی گام‌های ۱ تا ۴ را با این اجزا اجرا می‌کند.

## تمرین کد
فایل پاسخ: `work/p22_agentic_rag/step05_llm_components/answer.py`

1. `to_chunks(dicts)` : دیکشنری‌های ما (`id`, `doc_id`, `heading`, `text`) را به `labkit.chunking.Chunk(chunk_id, doc_id, text, meta)` تبدیل کن؛ `heading` در `meta["heading"]` می‌رود.
2. `make_answer(llm)` : تابعی `(question, chunks) -> (text, cites)` بساز که prompt را از `Chunk`ها می‌سازد (`[chunk_id] text`)، `llm.chat(...).content` را می‌گیرد و ارجاع‌های `[...]` را که شناسه‌ی واقعی‌اند برمی‌گرداند.
3. `make_agent(search, llm, max_rounds=3)` : یک `AgenticRAG` با `grade`, `rewrite`, `verify`, `route` مبتنی بر `llm`، `answer=make_answer(llm)` و `direct` که با `llm.chat` جواب می‌دهد.

## اجرا کن
```bash
python -m learn check p22_agentic_rag 5
```
مقایسه‌ی واقعی (فایل پاسخ را بعد از قبول شدن اجرا کن):
```powershell
# پیش‌فرض: offline (بدون مدل)
python work\p22_agentic_rag\step05_llm_components\answer.py
# Ollama
$env:LEARN_PROVIDER="ollama"; $env:LEARN_MODEL="qwen2.5:7b"; python work\p22_agentic_rag\step05_llm_components\answer.py
# Claude (کلید API در .env؛ سقف هزینه را بگذار!)
$env:LEARN_PROVIDER="anthropic"; $env:LEARN_MODEL="claude-sonnet-5-5"; $env:LEARN_BUDGET_USD="0.5"
python work\p22_agentic_rag\step05_llm_components\answer.py
# OpenCode
$env:LEARN_PROVIDER="opencode"; $env:LEARN_MODEL="anthropic/claude-sonnet-5-5"; python work\p22_agentic_rag\step05_llm_components\answer.py
```
(Linux/macOS: `export X=y`.)

## خروجی مورد انتظار
تست‌ها شش ✓. اجرای مقایسه دو ردیف گزارش چاپ می‌کند (`rules` و `llm`) با همان پنج شمارنده‌ی گام ۴ و تعداد فراخوانی/تأخیر. با `offline`، مدل «همه‌چیز مرتبط است» می‌گوید و `answered_unanswerable` بالا می‌رود: این **درس اصلی** است؛ خروجی بدون مدل واقعی قابل‌اعتماد نیست و همیشه باید اندازه گرفت.

با مدل واقعی معمولاً: `answered_unanswerable` کمتر یا برابر قاعده‌ها و `abstained_wrongly` کمتر؛ ولی هزینه و زمان چند برابر. اگر مدل کوچک (۷B) از قاعده‌ها بدتر شد، تعجب نکن؛ گزارش کن.

## اگر فرق داشت
| علامت | علت رایج |
|---|---|
| `KeyError: 'relevant'` | مدل JSON با شکل دیگر داد؛ prompt/schema را سخت‌تر کن یا مدل بهتر بگذار |
| `ANTHROPIC_API_KEY is not set` | کلید در `.env` نیست (اشتراک Claude.ai کلید نیست) |
| `BudgetExceeded` | سقف `LEARN_BUDGET_USD` تمام شد؛ این رفتار درست است |
| `opencode failed` | OpenCode نصب نیست یا login نکرده‌ای |
| خیلی کند | هر تکه یک فراخوانی است؛ `k` را کم کن یا مدل کوچک‌تر/سریع‌تر بگذار |

## دام‌ها
- **مدل به‌عنوان قاضی خودش سوگیری دارد.** اگر همان مدل جواب می‌دهد و همان verify می‌کند، خطاها همبسته‌اند. مدل verify را متفاوت یا قوی‌تر بگذار و قبل از اعتماد، با ۳۰ نمونه‌ی برچسب‌دار خودت بسنج (در پروژه‌ی اصلی: kappa).
- هزینه را بشمار: تعداد فراخوانی هر سؤال = `1 (route) + تعداد تکه‌ها (grade) + rewrite + 1 (answer) + 1 (verify)`. با سقف دور محدود می‌ماند.
- داده‌ی حساس را به مدل ابری نفرست.

## جمع‌بندی p22
عاملی داری که مسیر را انتخاب می‌کند، شواهد را نمره می‌دهد، خودش دوباره امتحان می‌کند، پاسخ را چک می‌کند و حق «نمی‌دانم» دارد، به‌علاوه‌ی راه اندازه‌گیری هر تصمیمش. قدم بعد: نسخه‌ی کامل با داده‌ی بزرگ‌تر (`python -m support.panel.presets scaffold p22_agentic_rag`)، ارزیابی با bootstrap CI، و مقایسه‌ی مدل‌ها در [m01_compare_models](../../m01_compare_models/README.md).

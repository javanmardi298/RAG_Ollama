# گام ۵: جواب با ارجاع به منبع و حق «نمی‌دانم»

## هدف این گام
آخرین حلقه‌ی یک سیستم FAQ: تکه‌های پیدا‌شده را به مدل زبانی می‌دهی، جواب با **ارجاع** می‌گیری، ارجاع‌های ساختگی را حذف می‌کنی و وقتی شواهد نیست **امتناع** می‌کنی. بعد همان تابع را با مدل واقعی اجرا می‌کنی: Ollama یا Claude یا مدل‌های OpenCode.

## پیش‌نیاز
گام‌های قبل مفهومی‌اند. این گام فقط یک شیء `llm` با متد `chat(messages)` می‌خواهد؛ در تست یک مدل ساختگی است و در اجرای واقعی `learn.llm.get()`.

## مفهوم
مدل زبانی خوب می‌نویسد ولی دو خطای خطرناک دارد: **ساختن واقعیت** (hallucination) و **جواب دادن وقتی نباید**. دفاع‌ها که در **کد** هستند، نه در prompt:

1. **جواب فقط از شواهد:** prompt می‌گوید فقط از متن‌های داده‌شده استفاده کن و بعد از هر ادعا شناسه‌ی منبع را در کروشه بنویس `[returns#0]`.
2. **ارجاع باید واقعی باشد:** بعد از جواب، شناسه‌های داخل کروشه را با شناسه‌های تکه‌هایی که فرستادیم مقایسه می‌کنیم. شناسه‌ی ساختگی حذف می‌شود.
3. **بی‌شاهد = بی‌جواب:** اگر هیچ تکه‌ای پیدا نشد، مدل را صدا نمی‌زنیم (هم ارزان‌تر، هم امن‌تر). اگر مدل جواب داد ولی هیچ ارجاع معتبری نداشت، جواب را نمی‌پذیریم.

نتیجه یک دیکشنری است: `{"answer": متن یا None, "citations": [...], "abstained": bool}`.

## تمرین کد
فایل پاسخ: `work/p01_faq_search/step05_answer_citations/answer.py`

1. `build_messages(question, chunks)` : لیست پیام‌ها (`system` و `user`). `chunks` لیست دیکشنری‌های گام ۱ است (`id`, `heading`, `text`). متن user باید هر تکه را به شکل `[id] heading: text` و بعد سؤال را داشته باشد.
2. `extract_citations(text, allowed_ids)` : همه‌ی `[...]`ها را پیدا کن، فقط آن‌هایی که در `allowed_ids` هستند، بدون تکرار و به ترتیب ظهور.
3. `answer(question, chunks, llm)` : مراحل بالا. جواب مدل از `llm.chat(messages).content` می‌آید.

## اجرا کن
```bash
python -m learn check p01_faq_search 5
```

### حالا با مدل واقعی (اختیاری ولی مهم)
فایل پاسخ را که درست شد اجرا کن. در پایین فایل یک بخش `__main__` هست که سؤال‌های FAQ را با مدل انتخابی می‌پرسد.

```powershell
# Windows PowerShell — پیش‌فرض: مدل آفلاین (بدون هیچ نصبی؛ جواب فقط شکل کار را نشان می‌دهد)
python work\p01_faq_search\step05_answer_citations\answer.py

# با Ollama (باید Ollama نصب و مدل pull شده باشد)
$env:LEARN_PROVIDER="ollama"; $env:LEARN_MODEL="qwen2.5:7b"
python work\p01_faq_search\step05_answer_citations\answer.py

# با Claude (کلید API در .env یا محیط)
$env:LEARN_PROVIDER="anthropic"; $env:LEARN_MODEL="claude-sonnet-5-5"
python work\p01_faq_search\step05_answer_citations\answer.py

# با OpenCode (مدل از تنظیمات خود OpenCode: provider/model)
$env:LEARN_PROVIDER="opencode"; $env:LEARN_MODEL="anthropic/claude-sonnet-5-5"
python work\p01_faq_search\step05_answer_citations\answer.py
```
در Linux/macOS به‌جای `$env:X="y"` از `export X=y` استفاده کن. راه‌اندازی هر ارائه‌دهنده در [00_setup](../../00_setup/README.md) است.

## خروجی مورد انتظار
تست‌ها شش ✓. با مدل واقعی برای «how long do I have to send back a sofa» باید جوابی مثل «30 days [returns#0]» ببینی؛ با سؤال «can I pay by cheque» باید **امتناع** (`ABSTAINED`) یا جواب بدون ارجاع معتبر رد شود.

## اگر فرق داشت
| علامت | علت رایج |
|---|---|
| ارجاع ساختگی در خروجی ماند | `extract_citations` را با `allowed_ids` فیلتر نکرده‌ای |
| با chunk خالی هم مدل صدا زده شد | شرط `if not chunks` را قبل از `llm.chat` نگذاشته‌ای |
| `opencode failed` | OpenCode نصب نیست یا به یک provider وارد نشده‌ای |
| `ANTHROPIC_API_KEY is not set` | کلید در `.env` نیست (اشتراک Claude.ai کلید API نیست) |

## دام‌ها
- «به مدل بگو اگر نمی‌دانی نگو» کافی نیست؛ بدون بررسی کد، مدل گاهی باز هم جواب می‌دهد. بررسی ارجاع یک دفاع قابل‌تست است.
- ارجاع معتبر ≠ جواب درست. مدل می‌تواند به تکه‌ی درست اشاره کند و چیز دیگری بگوید. راستی‌آزمایی (verify) را در درس p22 می‌بینی.
- داده‌ی واقعی مشتری را به مدل ابری نفرست مگر اجازه داشته باشی (بخش حریم داده در 00_setup).

## جمع‌بندی پروژه‌ی p01
حالا یک FAQ search کامل داری: chunk → BM25 + trigram → RRF → جواب با ارجاع. قدم بعد: [درس p22 Agentic RAG](../../p22_agentic_rag/README.md) که یاد می‌گیرد جست‌وجو را دوباره امتحان کند و بداند کی «نمی‌دانم» بگوید، و بعد جایگزینی با `labkit.retrieval.Index` (BM25 + embedding + reranker واقعی).

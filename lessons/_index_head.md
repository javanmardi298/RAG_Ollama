# درس‌ها: یادگیری قدم‌به‌قدم با کد، تست خودکار و راهنما

هر درس یک پروژه‌ی واقعی را به گام‌های کوچک می‌شکند. هر گام: **متن آموزشی کامل** (مفهوم، چرا، خط‌به‌خط کد، دام‌ها)، **کد ناقص** با TODO که تو کامل می‌کنی، **تست خودکار** که می‌گوید درست نوشتی یا نه و چرا، **راهنمایی سه‌سطحی**، **امتحان کوتاه** و جواب مرجع.

## از کجا شروع کنم؟
1. [راه‌اندازی (۳۰ دقیقه)](00_setup/README.md): Python، نصب، و اتصال مدل: Ollama، Claude، OpenCode.
2. [p01 — جست‌وجوی FAQ](p01_faq_search/README.md) (پایه، بدون هیچ مدل).
3. [p22 — Agentic RAG](p22_agentic_rag/README.md) (میانی).
4. [p17 — مبانی JEPA](p17_jepa_basics/README.md) (PyTorch، CPU).
5. [m01 — مقایسه‌ی مدل‌ها](m01_compare_models/README.md) (Ollama در برابر Claude در برابر OpenCode با عدد).

## چطور کار می‌کند
```bash
python -m learn list                       # درس‌ها و پیشرفت تو
python -m learn start p01_faq_search       # متن گام ۱ + ساخت فایل پاسخ در work/
python -m learn check p01_faq_search       # تست خودکار روی پاسخ تو
python -m learn hint  p01_faq_search       # راهنمایی (هر بار یک سطح بیشتر)
python -m learn quiz  p01_faq_search 1     # امتحان کوتاه
python -m learn solution p01_faq_search    # جواب مرجع (بعد از یک تلاش)
python -m learn review                     # سؤال‌هایی که اشتباه زدی
python -m learn errors                     # دفترچه‌ی خطاهای خودت
```
همین‌ها در **پنل** (منوی «درس‌ها») و به‌صورت **notebook** (Jupyter / Colab / VS Code) هم هست. پاسخ‌های تو در `work/` می‌مانند و commit نمی‌شوند.

## حالت معلم (Claude یا OpenCode راهنمای توست)
از Claude Desktop، Claude Code یا OpenCode بخواه: «درس p01 را با من جلو ببر». ابزارهای `lessons_list`، `lesson_step`، `lesson_check`، `lesson_hint` به آن‌ها داده می‌شود. معلم مفهوم را توضیح می‌دهد، تو کد را می‌نویسی، او نتیجه‌ی تست را با پرسش راهنما برایت باز می‌کند و **جواب کامل نمی‌دهد** (فایل `solution.py` از ابزار پنل خوانده نمی‌شود). برای Claude Code/OpenCode که خودشان فایل می‌خوانند، این قرارداد است نه قفل: در تنظیمات آن‌ها قاعده‌ی deny برای `lessons/**/solution.py` بگذار.

## مدل زبانی هر درس
پیش‌فرض `offline` (بدون نصب؛ شکل کار را نشان می‌دهد). برای جواب واقعی: `LEARN_PROVIDER=ollama | anthropic | opencode | openai_compatible` ([راهنمای کامل](00_setup/README.md)).

## قاعده‌های کار (برای هر درس)
- قبل از «بهتر کردن» اندازه بگیر؛ بعد از هر تغییر دوباره اندازه بگیر.
- نتیجه‌ی یک اجرا یا یک seed را باور نکن.
- کلید API و داده‌ی واقعی مشتری هرگز در git نرود.

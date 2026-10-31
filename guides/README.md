# راهنمای ساخت پروژه‌ها (برای repo خودت در GitHub)

هر راهنما قدم‌به‌قدم می‌گوید یک پروژه را **در repo خودت** چطور بسازی: کدام فایل را در GitHub بسازی (کد آماده‌ی کپی)، چطور روی لپ‌تاپ در VS Code اجرا کنی، سلول‌های notebook یکی‌یکی با «باید ببینی»، تست خودکار با GitHub Actions، README با عددهای خودت و خط رزومه.

همه‌ی کد این راهنماها قبل از انتشار روی یک پوشه‌ی تمیز اجرا و تست می‌شود (`python -m learn.guides verify`) و «باید ببینی»ها خروجی واقعی همان اجراست.

| پروژه | repo تو | راهنما | زمان |
|---|---|---|---|
| p01 — جست‌وجوی FAQ با جواب مستند | `faq_search` | [GUIDE.md](p01_faq_search/GUIDE.md) | ۱ تا ۲ ساعت |
| p22 — Agentic RAG | `agentic_rag` | [GUIDE.md](p22_agentic_rag/GUIDE.md) | ۱ تا ۲ ساعت |
| p17 — Mini I-JEPA | `jepa_digits` | [GUIDE.md](p17_jepa_basics/GUIDE.md) | ۱ تا ۲ ساعت |

**نسخه‌ی تعاملی** (تیک مراحل که در حساب claude.ai تو ذخیره می‌شود، مقایسه‌ی خروجی خودت با خروجی درست، پرسیدن از Claude وقتی به خطا می‌خوری، دانلود notebook آماده، پر کردن خودکار عددهای README): صفحه‌ی «راهنمای ساخت پروژه‌ها» در claude.ai: https://claude.ai/artifact/JtBeo3vZLnwWugaWV5uSc6 (خصوصی؛ فقط تو بازش می‌کنی مگر از منوی Share اجازه بدهی).

ترتیب پیشنهادی: اول درس همان موضوع را در repo آزمایشگاه (`python -m learn start <درس>`) برای فهمیدن، بعد همین راهنما برای ساختن نمونه‌کار خودت.

## برای نگه‌دارنده
```bash
python -m learn.guides verify      # اجرای کامل هر پروژه در پوشه‌ی تمیز + ذخیره‌ی خروجی‌ها در outputs.json
python -m learn.guides build       # GUIDE.md ها
python -m learn.guides html out.html
```

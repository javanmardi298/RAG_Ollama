# Agent Skills: بسته‌بندی دانش و روال کار با SKILL.md
_Agent Skills: packaging know-how and procedures with SKILL.md_ · سطح پایه · 1 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p30_agent_skills` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
روال‌های تکراری تیم (گزارش، بازبینی کد، استخراج فاکتور) به‌صورت skill برای Claude Code / Agent SDK و ده‌ها پلتفرم دیگر.
## مسئله
prompt های بلند برای هر کار context را پر می‌کنند؛ دانش تیم در ذهن افراد می‌ماند.
## هدف
سه skill با SKILL.md (توضیح کوتاه + دستورالعمل + اسکریپت/مرجع) بسازی که با progressive disclosure فقط وقتی لازم است بارگذاری شوند، و اثرشان را روی موفقیت وظیفه و توکن بسنجی.

## داده
- [Agent Skills (مستند)](https://agentskills.io/) · باز · قالب SKILL.md
- روال‌های همین repo · مثلاً اجرای مرحله‌ها و خواندن نتایج

## قطعه‌ها
- `agent_skills` Agent Skills (SKILL.md، progressive disclosure): پوشه‌ی skills/ با SKILL.md (Claude Code، Agent SDK و ~۴۰ پلتفرم)
- `prompt_registry` نسخه‌گذاری prompt: labkit.ops.PromptRegistry
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry

## گام 1: اولین skill
**یاد بگیر**
- frontmatter: name، description (کی استفاده شود)
- progressive disclosure: فقط توضیح در context

**بساز**
- skill «گزارش نتایج پروژه» با اسکریپت

**بسنج:** skill در کار درست فعال می‌شود و در کار نامرتبط نه

**دام:** description مبهم = فعال‌شدن اشتباه.

## گام 2: skill با اسکریپت و مرجع
**یاد بگیر**
- فایل‌های کمکی، اسکریپت قطعی به جای استدلال LLM

**بساز**
- skill استخراج فاکتور با schema و اسکریپت اعتبارسنجی

**بسنج:** موفقیت و توکن با/بدون skill

**دام:** اسکریپت اجرایی skill را مثل کد بازبینی کن (امنیت).

## گام 3: ارزیابی و نگهداری
**یاد بگیر**
- نسخه‌گذاری، تست

**بساز**
- ۱۰ وظیفه‌ی آزمون برای هر skill

**بسنج:** نرخ فعال‌سازی درست و موفقیت

**دام:** skill شخص ثالث را بدون خواندن نصب نکن.

## معیارها
- activation precision/recall
- task success with vs without skill
- tokens per task

## سؤال مصاحبه
- skill چه فرقی با prompt و ابزار MCP دارد؟
- progressive disclosure چیست؟
- skill را چطور ارزیابی کردی؟

## نسخه‌ی پیشرفته
- skill + MCP server با هم
- تولید خودکار skill از trace
- skill برای sub-agent ها

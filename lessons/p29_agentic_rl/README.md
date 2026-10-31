# RL با پاداش قابل‌بررسی (GRPO) برای مدل کوچک ابزارمحور
_RL with verifiable rewards (GRPO) for a small tool-using model_ · سطح پیشرفته · 2–3 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p29_agentic_rl` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
آموزش مدل کوچک ارزان برای Text-to-SQL، استخراج یا فراخوانی ابزار با پاداش قابل‌بررسی (اجرای SQL، اعتبارسنجی JSON) — روش رایج ۲۰۲۵–۲۰۲۶.
## مسئله
SFT فقط تقلید می‌کند؛ وقتی جواب قابل‌بررسی است، RL می‌تواند مستقیماً موفقیت را بهینه کند.
## هدف
یک مدل 0.5B–1.5B را با GRPO و پاداش قابل‌بررسی (اجرای SQL یا صحت JSON) آموزش بدهی و با SFT و مدل پایه مقایسه کنی؛ reward hacking را پایش کنی.

## پیش‌نیاز
- [p15_finetune_distill](../p15_finetune_distill/README.md)
- [p06_text_to_sql](../p06_text_to_sql/README.md)

## داده
- [Spider / BIRD](https://bird-bench.github.io/) · CC BY-SA 4.0 · Text-to-SQL با اجرای قابل‌بررسی
- [TRL GRPOTrainer](https://huggingface.co/docs/trl/main/en/grpo_trainer) · Apache 2.0 · پیاده‌سازی مرجع

## قطعه‌ها
- `grpo_trl` RL با پاداش قابل‌بررسی (GRPO / RLVR): Hugging Face TRL GRPOTrainer / Unsloth
- `lora` fine-tune با LoRA: scripts/stage9_lora_colab.py
- `sql_guard` محافظ Text-to-SQL: labkit.sqlguard
- `sql_exec_accuracy` execution accuracy برای SQL: labkit.sqlguard.execution_match
- `bootstrap_ci` فاصله‌ی اطمینان bootstrap: support.evaluation
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry

## گام 1: پاداش
**یاد بگیر**
- پاداش قابل‌بررسی، شکل‌دهی (فرمت + صحت)
- reward hacking

**بساز**
- تابع پاداش با اجرای SQL در sandbox فقط‌خواندنی

**بسنج:** پاداش روی جواب‌های gold = 1

**دام:** پاداش قابل دور زدن (مثلاً SELECT همه‌چیز) را تست کن.

## گام 2: GRPO
**یاد بگیر**
- گروه نمونه، advantage نسبی، KL

**بساز**
- TRL GRPOTrainer + LoRA روی Colab

**بسنج:** منحنی پاداش و طول پاسخ

**دام:** طول پاسخ منفجر می‌شود یا فرمت می‌شکند؛ پایش کن.

## گام 3: مقایسه
**یاد بگیر**
- SFT در برابر GRPO در برابر پایه

**بساز**
- execution accuracy روی dev جدا

**بسنج:** accuracy با CI، هزینه‌ی آموزش

**دام:** ارزیابی روی همان پایگاه داده‌ی آموزش = نشت.

## معیارها
- execution accuracy
- reward curve
- response length
- training GPU hours

## سؤال مصاحبه
- GRPO چه فرقی با PPO و DPO دارد؟
- reward hacking دیدی؟
- کی RL بهتر از SFT است؟

## نسخه‌ی پیشرفته
- RL چندمرحله‌ای با ابزار (agentic RL)
- curriculum سختی
- تقطیر از مدل بزرگ + RL

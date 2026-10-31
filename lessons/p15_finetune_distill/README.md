# fine-tune و distillation مدل کوچک (LoRA، DPO)
_Fine-tuning and distillation of small models (LoRA, DPO)_ · سطح پیشرفته · 3 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p15_finetune_distill` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
وقتی LLM بزرگ برای یک کار تکراری (طبقه‌بندی، استخراج، لحن برند) گران یا کند است: مدل کوچکِ آموزش‌دیده جایگزین می‌شود.
## مسئله
داده‌ی برچسب‌دار کم است، fine-tune بد مدل را بدتر می‌کند (فراموشی)، و مقایسه باید منصفانه و با هزینه باشد.
## هدف
با برچسب‌های LLM بزرگ (distillation) مدل کوچک را با LoRA آموزش دهی، با DPO لحن را تنظیم کنی، و دقت/هزینه/تأخیر را با baseline مقایسه کنی.

## پیش‌نیاز
- [p04_ticket_triage](../p04_ticket_triage/README.md)
- [p08_support_agent](../p08_support_agent/README.md)

## داده
- splitهای Bitext مرحله‌ی ۰ (`data/processed/`) · برای SFT طبقه‌بندی
- جفت‌های ترجیح از ویرایش اپراتور یا judge · (prompt، جواب بهتر، جواب بدتر) برای DPO

## قطعه‌ها
- `lora` fine-tune با LoRA: scripts/stage9_lora_colab.py
- `dpo` preference tuning (DPO): Hugging Face TRL
- `distillation` distillation از LLM به مدل کوچک: برچسب‌زنی با LLM + LoRA (همین repo)
- `structured_output` خروجی ساختاریافته + اعتبارسنجی + repair: labkit.structured
- `extraction_metrics` F1 هر فیلد، exact match: labkit.metrics
- `bootstrap_ci` فاصله‌ی اطمینان bootstrap: support.evaluation
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry
- `leakage_free_split` تقسیم بدون نشت (group split): support.data

## گام 1: baseline و بودجه
**یاد بگیر**
- آیا fine-tune لازم است؟ اول prompt و few-shot را بسنج

**بساز**
- baseline: TF-IDF مرحله‌ی ۱ و LLM با few-shot

**بسنج:** دقت، تأخیر، هزینه به ازای ۱۰۰۰ پیام

**دام:** fine-tune بدون baseline قوی، بهبود خیالی نشان می‌دهد.

## گام 2: SFT با LoRA
**یاد بگیر**
- LoRA: rank، alpha، ماژول‌های هدف
- overfitting و early stopping روی dev

**بساز**
- بسته‌ی Colab از پنل (مرحله‌ی ۹ support-agent)
- rank 8/16/32 را مقایسه کن

**بسنج:** macro-F1 روی dev و یک بار test

**دام:** learning rate بالا با LoRA مدل را خراب می‌کند؛ منحنی loss را ببین.

## گام 3: distillation
**یاد بگیر**
- برچسب نرم/سخت از مدل بزرگ
- کیفیت برچسب معلم را بسنج

**بساز**
- LLM بزرگ روی داده‌ی بی‌برچسب برچسب بزند؛ مدل کوچک روی آن آموزش ببیند
- مقایسه با آموزش روی برچسب انسانی

**بسنج:** دقت شاگرد در برابر معلم، هزینه‌ی برچسب‌زنی

**دام:** شاگرد خطاهای معلم را یاد می‌گیرد؛ نمونه‌ی برچسب معلم را دستی چک کن.

## گام 4: DPO برای لحن و قالب
**یاد بگیر**
- preference optimization بدون reward model
- جفت‌های ترجیح از ویرایش اپراتور

**بساز**
- TRL DPOTrainer روی مدل کوچک instruct با LoRA

**بسنج:** win rate با judge اعتبارسنجی‌شده، و حفظ دقت فکت

**دام:** DPO می‌تواند مدل را پرحرف کند (length bias)؛ طول را کنترل کن.

## معیارها
- macro-F1 / field F1
- win rate (validated judge)
- latency
- cost per 1k requests
- teacher-student gap

## سؤال مصاحبه
- کی fine-tune و کی prompt؟
- LoRA چطور کار می‌کند؟
- distillation را چطور ارزیابی کردی؟

## نسخه‌ی پیشرفته
- QLoRA برای مدل‌های ۷B روی GPU کوچک
- تبدیل به GGUF و quantization
- continual learning بدون فراموشی

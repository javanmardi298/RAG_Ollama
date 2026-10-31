# طبقه‌بندی و مسیریابی تیکت پشتیبانی
_Support ticket triage and routing_ · سطح پایه · 1–2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p04_ticket_triage` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
هر helpdesk: تیکت ورودی باید به تیم درست برود، اولویتش مشخص شود و پیام‌های نامربوط کنار بروند.
## مسئله
intentهای زیاد، پیام‌های نویزی و پیام‌های خارج از حوزه؛ و اینکه مدل بداند کی مطمئن نیست.
## هدف
سه روش (TF-IDF، embedding، LLM) را منصفانه مقایسه کنی، calibration انجام دهی و برای هر تیم آستانه‌ی جدا بگذاری.

## داده
- [Bitext customer support](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset) · CDLA-Sharing-1.0 · ۲۷ intent، flag برای غلط تایپی و محاوره
- [CLINC150 (oos)](https://github.com/clinc/oos-eval) · CC BY 3.0 · پیام‌های خارج از حوزه

## قطعه‌ها
- `leakage_free_split` تقسیم بدون نشت (group split): support.data
- `intent_classifier` طبقه‌بند intent (TF-IDF / embedding / LLM): support.intents
- `calibration` calibration (temperature scaling، ECE): support.intents
- `selective_decision` آستانه‌ی ریسک و ارجاع به انسان: support.decision
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry
- `ci_eval` ارزیابی در CI: .github/workflows/tests.yml

## گام 1: تقسیم بدون نشت
**یاد بگیر**
- near-duplicate و StratifiedGroupKFold

**بساز**
- مرحله‌ی ۰ پروژه‌ی support-agent در پنل

**بسنج:** اختلاف سهم intent بین بخش‌ها

**دام:** تقسیم تصادفی روی داده‌ی template-محور نمره را باد می‌کند.

## گام 2: سه مدل، یک معیار
**یاد بگیر**
- macro-F1
- سرعت به‌عنوان بخشی از مقایسه

**بساز**
- مرحله‌ی ۱ پروژه‌ی support-agent

**بسنج:** macro-F1، ms/پیام، دقت به تفکیک flag

**دام:** LLM روی نمونه ارزیابی می‌شود؛ حجم نمونه را گزارش کن.

## گام 3: calibration و آستانه
**یاد بگیر**
- ECE، temperature scaling
- risk-coverage

**بساز**
- مرحله‌ی ۴ پروژه‌ی support-agent

**بسنج:** ECE قبل/بعد، coverage در بودجه‌ی خطا

**دام:** آستانه روی test انتخاب نشود.

## گام 4: اولویت و چندبرچسبی (فراتر از support-agent)
**یاد بگیر**
- multi-label (یک پیام، دو درخواست)
- اولویت ترتیبی (ordinal)

**بساز**
- برچسب اولویت قاعده‌محور بساز (کلمه‌های خشم، مبلغ، تهدید حقوقی) و مدل را با آن آموزش بده

**بسنج:** F1 هر برچسب، recall اولویت بالا

**دام:** recall تیکت‌های فوری مهم‌تر از دقت کلی است؛ معیار را با هزینه‌ی واقعی انتخاب کن.

## معیارها
- macro-F1
- ECE
- oos recall
- coverage at error budget

## سؤال مصاحبه
- چرا calibration برای مسیریابی مهم است؟
- out-of-scope را چطور مدیریت کردی؟
- کی LLM و کی مدل کلاسیک؟

## نسخه‌ی پیشرفته
- SetFit با داده‌ی کم
- conformal prediction
- active learning: کدام تیکت را برای برچسب‌زنی بفرستیم

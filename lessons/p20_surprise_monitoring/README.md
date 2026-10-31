# پایش با «غافلگیری»: کشف ناهنجاری با خطای پیش‌بینی world model
_Surprise-based monitoring: anomaly detection from world-model prediction error_ · سطح میانی · 1 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p20_surprise_monitoring` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
پایش خط تولید، ربات و سنسورها: هشدار وقتی یک عمل اثر همیشگی‌اش را نداشت (شیر باز شد ولی فشار تغییر نکرد).
## مسئله
ناهنجاری‌ها نادر و متنوع‌اند و برچسب ندارند؛ قاعده‌های دستی همه را پوشش نمی‌دهند.
## هدف
خطای پیش‌بینی world model را به نمره‌ی ناهنجاری تبدیل کنی، AUC بگیری و آستانه را با نرخ هشدار کاذب قابل‌تحمل روی validation انتخاب کنی.

## پیش‌نیاز
- [p19_world_model_planning](../p19_world_model_planning/README.md)

## داده
- DotWorld با teleport · پرش‌های ناممکن به‌عنوان ناهنجاری
- [NAB (Numenta Anomaly Benchmark)](https://github.com/numenta/NAB) · AGPL · سری زمانی واقعی برای قدم بعد

## قطعه‌ها
- `latent_world_model` world model نهفته‌ی شرطی به عمل: jepa_lab.world_model.train_world_model
- `surprise_detection` surprise = خطای پیش‌بینی (کشف ناهنجاری): jepa_lab.world_model.surprise_auc
- `selective_decision` آستانه‌ی ریسک و ارجاع به انسان: support.decision
- `drift` drift با PSI: support.monitoring

## گام 1: نمره‌ی surprise
**یاد بگیر**
- violation of expectation
- ROC AUC

**بساز**
- python run.py --stage surprise

**بسنج:** AUC و میانگین خطا برای عادی/ناهنجار

**دام:** AUC بالا روی داده‌ی آموزش معنا ندارد؛ episode های تازه.

## گام 2: آستانه و هزینه
**یاد بگیر**
- false-alarm rate، precision در آستانه
- همان منطق مرحله‌ی ۴ پروژه‌ی اصلی

**بساز**
- آستانه را روی validation با FPR=1% انتخاب کن

**بسنج:** recall در FPR ثابت

**دام:** آستانه روی تست = نشت.

## گام 3: مقاومت
**یاد بگیر**
- نویز سنسور، drift

**بساز**
- --noise 0.05، تغییر نرخ teleport

**بسنج:** افت AUC با نویز

**دام:** نویز عادی را با ناهنجاری اشتباه نگیر؛ آستانه را دوباره کالیبره کن.

## معیارها
- ROC AUC
- recall at fixed false-alarm rate
- alert latency

## سؤال مصاحبه
- چرا خطای پیش‌بینی نمره‌ی ناهنجاری خوبی است؟
- آستانه را چطور انتخاب کردی؟
- اگر نویز سنسور زیاد شود چه می‌کنی؟

## نسخه‌ی پیشرفته
- V-JEPA 2 روی ویدیوی واقعی (p21)
- سری زمانی صنعتی (NAB)
- ترکیب با قواعد دامنه

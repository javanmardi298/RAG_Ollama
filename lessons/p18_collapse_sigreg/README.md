# فروپاشی نمایش (collapse) و درمان‌ها: EMA در برابر SIGReg
_Representation collapse and its cures: EMA teacher vs SIGReg (LeJEPA)_ · سطح میانی · 1 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p18_collapse_sigreg` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
هر سیستم self-supervised یا embedding (جست‌وجو، توصیه‌گر، world model) ممکن است بی‌صدا collapse کند: loss عالی، خروجی بی‌فایده.
## مسئله
loss به صفر می‌رسد ولی embedding ها به ورودی وابسته نیستند؛ معیارهای پایین‌دستی گاهی این را پنهان می‌کنند.
## هدف
collapse را عمداً بسازی، با mean_std و effective_rank تشخیص بدهی، و دو درمان (EMA teacher و SIGReg) را با هم مقایسه کنی.

## پیش‌نیاز
- [p17_jepa_basics](../p17_jepa_basics/README.md)

## داده
- [sklearn digits](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_digits.html) · BSD · همان داده‌ی p17
- [LeJEPA (مقاله)](https://arxiv.org/abs/2511.08544) · arXiv · SIGReg و توجیه نظری

## قطعه‌ها
- `jepa_ssl` JEPA: پیش‌بینی embedding بخش پنهان (I-JEPA کوچک): jepa_lab.ssl.train
- `sigreg` SIGReg و تشخیص collapse (LeJEPA): jepa_lab.sigreg.sigreg
- `linear_probe` linear probe روی encoder منجمد: jepa_lab.ssl.linear_probe
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry

## گام 1: ساختن collapse
**یاد بگیر**
- چرا loss صفر مشکوک است
- mean_std و effective_rank

**بساز**
- variant=naive را اجرا کن و منحنی‌ها را ببین

**بسنج:** loss≈0 و mean_std≈0 را نشان بده

**دام:** probe با StandardScaler ممکن است collapse را پنهان کند.

## گام 2: درمان‌ها
**یاد بگیر**
- EMA + stop-gradient (BYOL، I-JEPA)
- SIGReg: Epps–Pulley روی projection های تصادفی

**بساز**
- ema و sigreg را با همان بودجه اجرا کن
- sigreg_weight را 0.05→0.9 جاروب کن

**بسنج:** rank، std و probe برای هر وزن

**دام:** وزن زیاد SIGReg پیش‌بینی را خفه می‌کند؛ وزن کم collapse را برنمی‌گرداند.

## گام 3: انتقال به world model
**یاد بگیر**
- collapse در world model یعنی تصمیم‌گیری تصادفی

**بساز**
- world model را با sigreg_weight=0 آموزش بده (p19)

**بسنج:** موفقیت planning با و بدون SIGReg

**دام:** rank پایین همیشه collapse نیست: دنیای دوبعدی rank≈2 دارد.

## معیارها
- mean_std
- effective_rank
- loss
- probe accuracy

## سؤال مصاحبه
- collapse چیست و چطور تشخیصش می‌دهی؟
- EMA teacher چرا کار می‌کند و ایرادش چیست؟
- SIGReg چه چیزی را جریمه می‌کند؟

## نسخه‌ی پیشرفته
- VICReg و Barlow Twins را اضافه کن
- SIGReg روی ImageNet-100 با ViT-S
- اثر اندازه‌ی batch روی SIGReg

# V-JEPA 2 واقعی: embedding ویدیو، جست‌وجو، رخداد غیرعادی و تشخیص عمل
_Pretrained V-JEPA 2: video embeddings, search, unusual events and action recognition_ · سطح پیشرفته · 2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p21_vjepa2_video` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
تحلیل ویدیوی ورزشی، فروشگاه، ایمنی کارگاه، رباتیک؛ encoder ویدیویی منجمد + probe کوچک با برچسب کم.
## مسئله
مدل‌های ویدیویی آموزش از صفر گران‌اند؛ باید با encoder آماده و داده‌ی برچسب‌دار کم به نتیجه رسید.
## هدف
با V-JEPA 2 از پیش آموزش‌دیده embedding کلیپ بگیری، جست‌وجوی نزدیک‌ترین همسایه و surprise زمانی بسازی، و با DINOv2 فریم‌به‌فریم مقایسه کنی.

## پیش‌نیاز
- [p20_surprise_monitoring](../p20_surprise_monitoring/README.md)

## داده
- [V-JEPA 2 (Hugging Face)](https://huggingface.co/facebook/vjepa2-vitl-fpc64-256) · کارت مدل را ببین · ViT-L، ~۱.۳GB
- [UCF101](https://www.crcv.ucf.edu/data/UCF101.php) · پژوهشی · ۱۰۱ کلاس عمل
- ویدیوهای خودت · ۱۰–۵۰ کلیپ کوتاه

## قطعه‌ها
- `vjepa2` V-JEPA 2 از پیش آموزش‌دیده (ویدیو): transformers: facebook/vjepa2-* (scripts/jepa5_vjepa2_colab.py)
- `pretrained_vision` backbone بینایی آماده برای مقایسه: DINOv2/v3، SigLIP (transformers / timm)
- `linear_probe` linear probe روی encoder منجمد: jepa_lab.ssl.linear_probe
- `surprise_detection` surprise = خطای پیش‌بینی (کشف ناهنجاری): jepa_lab.world_model.surprise_auc
- `vector_db` پایگاه برداری: FAISS (محلی) / Qdrant / pgvector

## گام 1: راه‌اندازی و embedding
**یاد بگیر**
- پردازشگر ویدیو، فریم در هر پنجره
- mean-pool توکن‌ها

**بساز**
- scripts/jepa5_vjepa2_colab.py روی چند کلیپ

**بسنج:** زمان هر کلیپ روی T4

**دام:** نسخه‌ی transformers و نام مدل را با کارت مدل چک کن.

## گام 2: جست‌وجو و probe
**یاد بگیر**
- kNN، probe خطی با برچسب کم

**بساز**
- ۵ کلاس از UCF101 با ۱۰ نمونه برای هر کلاس

**بسنج:** دقت probe در برابر DINOv2 فریم‌به‌فریم

**دام:** نشت: کلیپ‌های یک ویدیو نباید در train و test باشند (group split).

## گام 3: رخداد غیرعادی
**یاد بگیر**
- پرش embedding بین پنجره‌های متوالی

**بساز**
- چند ویدیو با رخداد ناگهانی، نمره بده

**بسنج:** آیا لحظه‌ی رخداد بالاترین نمره را دارد؟

**دام:** برش دوربین (cut) هم پرش می‌سازد؛ آن را جدا کن.

## معیارها
- probe accuracy (few labels)
- retrieval recall@5
- seconds per clip
- event localisation hit rate

## سؤال مصاحبه
- چرا encoder منجمد + probe؟
- V-JEPA 2 با DINOv2 چه فرقی دارد؟
- group split را در ویدیو چطور انجام دادی؟

## نسخه‌ی پیشرفته
- fine-tune attentive probe
- V-JEPA 2-AC روی داده‌ی ربات (کد رسمی)
- VL-JEPA برای پرسش متنی از ویدیو

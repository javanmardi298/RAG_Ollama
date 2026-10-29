# p17 — مبانی JEPA: پیش‌بینی در فضای embedding

**سطح:** پایه‌ی یادگیری ماشین · **زمان:** ۴ تا ۶ ساعت · **نیاز:** numpy برای گام‌های ۱، ۳ و ۴؛ PyTorch برای گام ۲ و اجرای آزمایش (`pip install -r requirements-jepa.txt`، فقط CPU کافی است)

## ایده در سه جمله
مدل‌های مولد پیکسل یا توکن را بازسازی می‌کنند. **JEPA** (Joint-Embedding Predictive Architecture) به‌جای پیکسل، **embedding بخش پنهان** تصویر را از روی بخش دیده‌شده پیش‌بینی می‌کند؛ پس ظرفیت مدل صرف جزئیات غیرقابل‌پیش‌بینی (نویز) نمی‌شود. خطر اصلی **فروپاشی نمایش** (collapse) است: encoder همه‌چیز را به یک نقطه ببرد تا loss صفر شود.

توضیح کامل‌تر، خانواده‌ی JEPA و جدول معادل‌ها: [docs/jepa.md](../../docs/jepa.md).

## گام‌ها
| گام | موضوع | چه می‌نویسی |
|---|---|---|
| [۱](step01_patches_masks/lesson.md) | patch و ماسک | `patchify`، `block_mask` (numpy) |
| [۲](step02_latent_loss_ema/lesson.md) | هدف آموزش | `masked_latent_loss`، `ema_update` (PyTorch) |
| [۳](step03_collapse/lesson.md) | تشخیص collapse | `collapse_stats`، `is_collapsed` (numpy) |
| [۴](step04_probe_and_verdict/lesson.md) | ارزیابی صادقانه | `summarize`، `verdict` و اجرای آزمایش واقعی |

بعد از این درس: آزمایش‌های کامل `scripts/jepa1…4`، پروژه‌های p18 تا p21 و آموزش `docs/jepa.md`.

## چطور کار کنیم
```bash
pip install -r requirements-jepa.txt
python -m learn start p17_jepa_basics
python -m learn check p17_jepa_basics
```

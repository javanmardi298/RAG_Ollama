# world model نهفته و تصمیم‌گیری با برنامه‌ریزی (CEM + MPC)
_Latent world model and decision-making by planning (CEM + MPC)_ · سطح میانی · 1–2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p19_world_model_planning` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
ربات‌هایی که قبل از حرکت نتیجه را «تصور» می‌کنند (V-JEPA 2-AC، DINO-WM، TD-MPC2)؛ برنامه‌ریزی مسیر و کنترل فرایند.
## مسئله
یادگیری سیاست با RL داده و پاداش زیاد می‌خواهد؛ اغلب فقط داده‌ی تعامل بدون پاداش و یک تصویر هدف داریم.
## هدف
از تعامل تصادفی (بدون پاداش) یک world model نهفته یاد بگیری، با CEM در فضای نهفته به سمت تصویر هدف برنامه بریزی، و با planner تصادفی (کف) و oracle (سقف) مقایسه کنی.

## پیش‌نیاز
- [p18_collapse_sigreg](../p18_collapse_sigreg/README.md)

## داده
- DotWorld (داخل jepa_lab) · نقطه در تصویر ۱۲×۱۲، داده‌ی تعامل تصادفی
- [V-JEPA 2 (مقاله)](https://arxiv.org/abs/2506.09985) · arXiv · V-JEPA 2-AC و برنامه‌ریزی با انرژی L1
- [LeWorldModel](https://arxiv.org/abs/2603.19312) · arXiv · JEPA انتها-به-انتها از پیکسل با SIGReg

## قطعه‌ها
- `latent_world_model` world model نهفته‌ی شرطی به عمل: jepa_lab.world_model.train_world_model
- `sigreg` SIGReg و تشخیص collapse (LeJEPA): jepa_lab.sigreg.sigreg
- `cem_mpc` برنامه‌ریزی CEM + MPC در فضای نهفته: jepa_lab.world_model.cem_plan
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry

## گام 1: آموزش بدون پاداش
**یاد بگیر**
- z' ≈ z + predictor(z, a)
- loss در فضای نهفته + SIGReg

**بساز**
- python run.py --stage train
- probe موقعیت (R²)

**بسنج:** R² موقعیت و effective_rank

**دام:** بدون SIGReg z ثابت می‌شود و loss صفر — collapse.

## گام 2: برنامه‌ریزی
**یاد بگیر**
- CEM: نمونه، rollout نهفته، elite، به‌روزرسانی
- MPC: فقط اولین عمل، دوباره برنامه

**بساز**
- planner های cem/random/oracle
- horizon و samples را جاروب کن

**بسنج:** نرخ موفقیت، گام تا هدف، زمان هر تصمیم

**دام:** فقط موفقیت را گزارش نکن؛ زمان تصمیم هم مهم است.

## گام 3: سخت‌تر کردن دنیا
**یاد بگیر**
- عدم قطعیت مدل، موانع، عمل گسسته

**بساز**
- یک مانع به DotWorld اضافه کن
- noise دوربین

**بسنج:** افت موفقیت با سختی

**دام:** مدلی که روی داده‌ی تصادفی آموزش دیده ممکن است حالت‌های نادیده را بد پیش‌بینی کند.

## معیارها
- planning success rate (cem vs random vs oracle)
- mean steps to goal
- seconds per decision
- position probe R²

## سؤال مصاحبه
- world model چه فرقی با سیاست (policy) دارد؟
- CEM و MPC را توضیح بده
- بدون پاداش چطور هدف را مشخص کردی؟

## نسخه‌ی پیشرفته
- DINO-WM روی PushT
- TD-MPC2 با پاداش
- گرادیان در فضای نهفته به جای CEM

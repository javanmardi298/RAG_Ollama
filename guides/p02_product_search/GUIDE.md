# ساختن جست‌وجوی محصول با ارزیابی درجه‌دار، از صفر در GitHub

جست‌وجوی محصول برای یک فروشگاه مبلمان می‌سازی و با برچسب‌های درجه‌دار (Exact / Partial) می‌سنجی: آیا متن غنی‌تر محصول کمک می‌کند؟ ترکیب دو جست‌وجو چطور؟ و آیا تفاوت واقعی است یا شانس؟ بدون GPU و بدون مدل، روی یک کاتالوگ کوچک ساختگی. نسخه‌ی کامل با داده‌ی واقعی WANDS (۴۳ هزار محصول، Colab + Ollama) در صفحه‌ی Build Log خودت است.

> نسخه‌ی تعاملی (تیک مراحل، مقایسه‌ی خروجی، پرسیدن از Claude، دانلود notebook): صفحه‌ی «راهنمای ساخت پروژه‌ها» (claude.ai artifact).

**برای فهمیدن بهتر:** پروژه در نقشه‌ی راه (نقشه‌ی راه، پروژه‌ی `p02_product_search`) · [مفاهیم BM25 و RRF: درس p01](../../lessons/p01_faq_search/README.md)

## مراحل
1. ساختن repo در GitHub
2. فایل .gitignore
3. فایل requirements.txt
4. فایل داده: data/products.json
5. فایل اصلی: product_search.py
6. فایل check_setup.py
7. تست‌ها: tests/test_product_search.py
8. تست خودکار در GitHub (Actions)
9. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
10. ساختن و اجرای notebook
11. commit و push از VS Code
12. README نهایی
13. صیقل نهایی repo

## 1. ساختن repo در GitHub
_GitHub · حدود 3 دقیقه_

**چرا:** repo خودت نمونه‌کار توست: هر فایلی که اینجا می‌سازی، کارفرما می‌بیند. اسم و توضیح کوتاه و دقیق، اولین چیزی است که دیده می‌شود.

1. در github.com بالا سمت راست **+** → **New repository**.
2. **Repository name:** `product_search`
3. **Description:** `Product search for a furniture shop: basic vs rich product text, BM25, typo-tolerant trigrams and hybrid RRF, evaluated with nDCG@10 / recall@10 / MRR and bootstrap tests`
4. **Public** را انتخاب کن (برای نمونه‌کار و Actions رایگان).
5. تیک **Add a README file**، **Add .gitignore:** None (خودمان می‌سازیم)، **Choose a license:** MIT License → **Create repository**.

> **باید ببینی:** repo دو فایل دارد: `README.md` و `LICENSE`. در LICENSE اگر نام تو در خط Copyright نیست، با آیکون مداد اصلاحش کن.

## 2. فایل .gitignore
_GitHub · حدود 2 دقیقه_

**چرا:** به git می‌گوید چه چیزهایی هرگز وارد repo نشوند: محیط مجازی، فایل‌های موقت، و `.env` که کلید API در آن است. **قبل از** هر فایل دیگری بساز.

1. **Add file** → **Create new file**، نام `.gitignore`، متن زیر را paste کن. commit: `Add .gitignore`.

`.gitignore`

````
# Python and editors
.venv/
__pycache__/
.ipynb_checkpoints/
.pytest_cache/
.DS_Store

# secrets: API keys live here, never in git
.env
````

## 3. فایل requirements.txt
_GitHub · حدود 2 دقیقه_

**چرا:** numpy برای محاسبه‌ی سریع امتیازها و bootstrap. بقیه‌ی پروژه با کتابخانه‌ی استاندارد پایتون است. `sentence-transformers` اختیاری است (جست‌وجوی embedding)؛ فعلاً با `#` غیرفعال است.

1. **Add file → Create new file**، نام `requirements.txt`. commit: `Add requirements`.

`requirements.txt`

````
numpy>=1.24
pytest>=8.0
ipykernel>=6.29
# optional: dense search with embeddings (downloads a small model, about 90 MB)
# sentence-transformers>=3.0
````

## 4. فایل داده: data/products.json
_GitHub · حدود 3 دقیقه_

**چرا:** ۸۴ محصول (مبل، صندلی، میز، تخت، چراغ، فرش، ...) با نام، دسته، ویژگی‌های ساخت‌یافته (رنگ، جنس، سبک) و توضیح؛ ۲۴ جست‌وجوی خریدار و برچسب‌های درجه‌دار مثل WANDS: Exact (۲) و Partial (۱). داده ساختگی است و مجوزی لازم ندارد.

1. **Add file → Create new file**، در کادر نام بنویس `data/products.json` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add synthetic catalogue with graded labels`.

`data/products.json`

````json
{
 "products": [
  {
   "product_id": 1,
   "product_name": "Elio Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:white|material:velvet|style:modern|seats:4",
   "description": "A settee made of velvet. Solid build for daily use. Seats 4."
  },
  {
   "product_id": 2,
   "product_name": "Juno Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:white|material:velvet|style:industrial|seats:2",
   "description": "A settee for your home. Easy to assemble. Seats 2."
  },
  {
   "product_id": 3,
   "product_name": "Juno Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:grey|material:velvet|style:mid-century|seats:4",
   "description": "A settee made of velvet. Solid build for daily use. Seats 4."
  },
  {
   "product_id": 4,
   "product_name": "Dane Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:white|material:leather|style:industrial|seats:3",
   "description": "A settee for your home. Fits small spaces. Seats 3."
  },
  {
   "product_id": 5,
   "product_name": "Gus Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:brown|material:velvet|style:mid-century|seats:4",
   "description": "A settee for your home. Solid build for daily use. Seats 4."
  },
  {
   "product_id": 6,
   "product_name": "Gus Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:blue|material:linen|style:modern|seats:2",
   "description": "A settee made of linen. Fits small spaces. Seats 2."
  },
  {
   "product_id": 7,
   "product_name": "Hale Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:black|material:linen|style:modern|seats:4",
   "description": "A settee for your home. Comes with a 2-year warranty. Seats 4."
  },
  {
   "product_id": 8,
   "product_name": "Juno Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:grey|material:leather|style:rustic|seats:4",
   "description": "A settee for your home. Fits small spaces. Seats 4."
  },
  {
   "product_id": 9,
   "product_name": "Alma Armchair",
   "product_class": "armchair",
   "category": "Living Room Furniture",
   "features": "color:black|material:velvet|style:modern",
   "description": "A accent chair for your home. Fits small spaces."
  },
  {
   "product_id": 10,
   "product_name": "Gus Armchair",
   "product_class": "armchair",
   "category": "Living Room Furniture",
   "features": "color:grey|material:velvet|style:modern",
   "description": "A accent chair made of velvet. Fits small spaces."
  },
  {
   "product_id": 11,
   "product_name": "Dane Armchair",
   "product_class": "armchair",
   "category": "Living Room Furniture",
   "features": "color:blue|material:linen|style:rustic",
   "description": "A accent chair for your home. Easy to assemble."
  },
  {
   "product_id": 12,
   "product_name": "Iris Armchair",
   "product_class": "armchair",
   "category": "Living Room Furniture",
   "features": "color:black|material:leather|style:mid-century",
   "description": "A accent chair for your home. Solid build for daily use."
  },
  {
   "product_id": 13,
   "product_name": "Iris Armchair",
   "product_class": "armchair",
   "category": "Living Room Furniture",
   "features": "color:beige|material:linen|style:rustic",
   "description": "A accent chair made of linen. Fits small spaces."
  },
  {
   "product_id": 14,
   "product_name": "Alma Armchair",
   "product_class": "armchair",
   "category": "Living Room Furniture",
   "features": "color:brown|material:velvet|style:mid-century",
   "description": "A accent chair for your home. Comes with a 2-year warranty."
  },
  {
   "product_id": 15,
   "product_name": "Juno Armchair",
   "product_class": "armchair",
   "category": "Living Room Furniture",
   "features": "color:green|material:velvet|style:mid-century",
   "description": "A accent chair for your home. Fits small spaces."
  },
  {
   "product_id": 16,
   "product_name": "Gus Armchair",
   "product_class": "armchair",
   "category": "Living Room Furniture",
   "features": "color:blue|material:leather|style:scandinavian",
   "description": "A accent chair for your home. Comes with a 2-year warranty."
  },
  {
   "product_id": 17,
   "product_name": "Dane Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:blue|material:metal|style:mid-century",
   "description": "A side chair for your home. Fits small spaces."
  },
  {
   "product_id": 18,
   "product_name": "Juno Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:white|material:plastic|style:scandinavian",
   "description": "A side chair for your home. Solid build for daily use."
  },
  {
   "product_id": 19,
   "product_name": "Brook Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:blue|material:plastic|style:scandinavian",
   "description": "A side chair for your home. Easy to assemble."
  },
  {
   "product_id": 20,
   "product_name": "Gus Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:blue|material:plastic|style:mid-century",
   "description": "A side chair for your home. Comes with a 2-year warranty."
  },
  {
   "product_id": 21,
   "product_name": "Iris Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:beige|material:plastic|style:scandinavian",
   "description": "A side chair made of plastic. Easy to assemble."
  },
  {
   "product_id": 22,
   "product_name": "Iris Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:white|material:plastic|style:modern",
   "description": "A side chair for your home. Fits small spaces."
  },
  {
   "product_id": 23,
   "product_name": "Cora Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:grey|material:metal|style:scandinavian",
   "description": "A side chair for your home. Fits small spaces."
  },
  {
   "product_id": 24,
   "product_name": "Brook Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:black|material:oak|style:industrial",
   "description": "A side chair for your home. Fits small spaces."
  },
  {
   "product_id": 25,
   "product_name": "Juno Coffee Table",
   "product_class": "coffee table",
   "category": "Living Room Furniture",
   "features": "color:brown|material:glass|style:industrial",
   "description": "A coffee table made of glass. Fits small spaces."
  },
  {
   "product_id": 26,
   "product_name": "Iris Coffee Table",
   "product_class": "coffee table",
   "category": "Living Room Furniture",
   "features": "color:brown|material:oak|style:industrial",
   "description": "A coffee table for your home. Fits small spaces."
  },
  {
   "product_id": 27,
   "product_name": "Faye Coffee Table",
   "product_class": "coffee table",
   "category": "Living Room Furniture",
   "features": "color:beige|material:oak|style:modern",
   "description": "A coffee table for your home. Fits small spaces."
  },
  {
   "product_id": 28,
   "product_name": "Juno Coffee Table",
   "product_class": "coffee table",
   "category": "Living Room Furniture",
   "features": "color:blue|material:oak|style:mid-century",
   "description": "A coffee table for your home. Easy to assemble."
  },
  {
   "product_id": 29,
   "product_name": "Iris Coffee Table",
   "product_class": "coffee table",
   "category": "Living Room Furniture",
   "features": "color:white|material:marble|style:modern",
   "description": "A coffee table for your home. Solid build for daily use."
  },
  {
   "product_id": 30,
   "product_name": "Cora Coffee Table",
   "product_class": "coffee table",
   "category": "Living Room Furniture",
   "features": "color:white|material:marble|style:industrial",
   "description": "A coffee table made of marble. Comes with a 2-year warranty."
  },
  {
   "product_id": 31,
   "product_name": "Elio Coffee Table",
   "product_class": "coffee table",
   "category": "Living Room Furniture",
   "features": "color:blue|material:glass|style:mid-century",
   "description": "A coffee table for your home. Fits small spaces."
  },
  {
   "product_id": 32,
   "product_name": "Brook Coffee Table",
   "product_class": "coffee table",
   "category": "Living Room Furniture",
   "features": "color:beige|material:glass|style:scandinavian",
   "description": "A coffee table made of glass. Easy to assemble."
  },
  {
   "product_id": 33,
   "product_name": "Iris Dining Table",
   "product_class": "dining table",
   "category": "Kitchen & Dining",
   "features": "color:green|material:oak|style:industrial",
   "description": "A kitchen table made of oak. Solid build for daily use."
  },
  {
   "product_id": 34,
   "product_name": "Dane Dining Table",
   "product_class": "dining table",
   "category": "Kitchen & Dining",
   "features": "color:grey|material:oak|style:modern",
   "description": "A kitchen table made of oak. Easy to assemble."
  },
  {
   "product_id": 35,
   "product_name": "Iris Dining Table",
   "product_class": "dining table",
   "category": "Kitchen & Dining",
   "features": "color:brown|material:walnut|style:modern",
   "description": "A kitchen table made of walnut. Comes with a 2-year warranty."
  },
  {
   "product_id": 36,
   "product_name": "Juno Dining Table",
   "product_class": "dining table",
   "category": "Kitchen & Dining",
   "features": "color:blue|material:glass|style:mid-century",
   "description": "A kitchen table for your home. Solid build for daily use."
  },
  {
   "product_id": 37,
   "product_name": "Dane Dining Table",
   "product_class": "dining table",
   "category": "Kitchen & Dining",
   "features": "color:brown|material:walnut|style:scandinavian",
   "description": "A kitchen table made of walnut. Comes with a 2-year warranty."
  },
  {
   "product_id": 38,
   "product_name": "Hale Dining Table",
   "product_class": "dining table",
   "category": "Kitchen & Dining",
   "features": "color:green|material:walnut|style:scandinavian",
   "description": "A kitchen table for your home. Easy to assemble."
  },
  {
   "product_id": 39,
   "product_name": "Alma Dining Table",
   "product_class": "dining table",
   "category": "Kitchen & Dining",
   "features": "color:white|material:glass|style:modern",
   "description": "A kitchen table for your home. Fits small spaces."
  },
  {
   "product_id": 40,
   "product_name": "Dane Dining Table",
   "product_class": "dining table",
   "category": "Kitchen & Dining",
   "features": "color:brown|material:oak|style:mid-century",
   "description": "A kitchen table made of oak. Comes with a 2-year warranty."
  },
  {
   "product_id": 41,
   "product_name": "Elio Bed Frame",
   "product_class": "bed frame",
   "category": "Bedroom Furniture",
   "features": "color:blue|material:metal|style:mid-century",
   "description": "A platform bed for your home. Easy to assemble."
  },
  {
   "product_id": 42,
   "product_name": "Alma Bed Frame",
   "product_class": "bed frame",
   "category": "Bedroom Furniture",
   "features": "color:beige|material:upholstered|style:modern",
   "description": "A platform bed for your home. Easy to assemble."
  },
  {
   "product_id": 43,
   "product_name": "Gus Bed Frame",
   "product_class": "bed frame",
   "category": "Bedroom Furniture",
   "features": "color:grey|material:oak|style:mid-century",
   "description": "A platform bed for your home. Solid build for daily use."
  },
  {
   "product_id": 44,
   "product_name": "Cora Bed Frame",
   "product_class": "bed frame",
   "category": "Bedroom Furniture",
   "features": "color:brown|material:metal|style:modern",
   "description": "A platform bed for your home. Comes with a 2-year warranty."
  },
  {
   "product_id": 45,
   "product_name": "Gus Bed Frame",
   "product_class": "bed frame",
   "category": "Bedroom Furniture",
   "features": "color:green|material:metal|style:rustic",
   "description": "A platform bed for your home. Comes with a 2-year warranty."
  },
  {
   "product_id": 46,
   "product_name": "Dane Bed Frame",
   "product_class": "bed frame",
   "category": "Bedroom Furniture",
   "features": "color:blue|material:oak|style:rustic",
   "description": "A platform bed for your home. Easy to assemble."
  },
  {
   "product_id": 47,
   "product_name": "Alma Bed Frame",
   "product_class": "bed frame",
   "category": "Bedroom Furniture",
   "features": "color:white|material:metal|style:modern",
   "description": "A platform bed for your home. Solid build for daily use."
  },
  {
   "product_id": 48,
   "product_name": "Cora Bed Frame",
   "product_class": "bed frame",
   "category": "Bedroom Furniture",
   "features": "color:grey|material:upholstered|style:modern",
   "description": "A platform bed made of upholstered. Easy to assemble."
  },
  {
   "product_id": 49,
   "product_name": "Brook Floor Lamp",
   "product_class": "floor lamp",
   "category": "Lighting",
   "features": "color:white|material:metal|style:scandinavian",
   "description": "A floor lamp for your home. Solid build for daily use."
  },
  {
   "product_id": 50,
   "product_name": "Juno Floor Lamp",
   "product_class": "floor lamp",
   "category": "Lighting",
   "features": "color:black|material:wood|style:modern",
   "description": "A floor lamp made of wood. Fits small spaces."
  },
  {
   "product_id": 51,
   "product_name": "Dane Floor Lamp",
   "product_class": "floor lamp",
   "category": "Lighting",
   "features": "color:green|material:metal|style:rustic",
   "description": "A floor lamp made of metal. Solid build for daily use."
  },
  {
   "product_id": 52,
   "product_name": "Hale Floor Lamp",
   "product_class": "floor lamp",
   "category": "Lighting",
   "features": "color:white|material:wood|style:rustic",
   "description": "A floor lamp for your home. Easy to assemble."
  },
  {
   "product_id": 53,
   "product_name": "Juno Floor Lamp",
   "product_class": "floor lamp",
   "category": "Lighting",
   "features": "color:grey|material:brass|style:industrial",
   "description": "A floor lamp for your home. Easy to assemble."
  },
  {
   "product_id": 54,
   "product_name": "Elio Floor Lamp",
   "product_class": "floor lamp",
   "category": "Lighting",
   "features": "color:black|material:metal|style:industrial",
   "description": "A floor lamp made of metal. Fits small spaces."
  },
  {
   "product_id": 55,
   "product_name": "Elio Floor Lamp",
   "product_class": "floor lamp",
   "category": "Lighting",
   "features": "color:grey|material:metal|style:rustic",
   "description": "A floor lamp made of metal. Fits small spaces."
  },
  {
   "product_id": 56,
   "product_name": "Alma Floor Lamp",
   "product_class": "floor lamp",
   "category": "Lighting",
   "features": "color:black|material:wood|style:industrial",
   "description": "A floor lamp for your home. Fits small spaces."
  },
  {
   "product_id": 57,
   "product_name": "Elio Area Rug",
   "product_class": "area rug",
   "category": "Rugs",
   "features": "color:white|material:wool|style:mid-century",
   "description": "A carpet made of wool. Easy to assemble."
  },
  {
   "product_id": 58,
   "product_name": "Elio Area Rug",
   "product_class": "area rug",
   "category": "Rugs",
   "features": "color:white|material:cotton|style:mid-century",
   "description": "A carpet made of cotton. Solid build for daily use."
  },
  {
   "product_id": 59,
   "product_name": "Elio Area Rug",
   "product_class": "area rug",
   "category": "Rugs",
   "features": "color:white|material:jute|style:mid-century",
   "description": "A carpet for your home. Fits small spaces."
  },
  {
   "product_id": 60,
   "product_name": "Gus Area Rug",
   "product_class": "area rug",
   "category": "Rugs",
   "features": "color:brown|material:wool|style:modern",
   "description": "A carpet for your home. Easy to assemble."
  },
  {
   "product_id": 61,
   "product_name": "Elio Area Rug",
   "product_class": "area rug",
   "category": "Rugs",
   "features": "color:grey|material:jute|style:mid-century",
   "description": "A carpet made of jute. Comes with a 2-year warranty."
  },
  {
   "product_id": 62,
   "product_name": "Iris Area Rug",
   "product_class": "area rug",
   "category": "Rugs",
   "features": "color:black|material:cotton|style:scandinavian",
   "description": "A carpet made of cotton. Easy to assemble."
  },
  {
   "product_id": 63,
   "product_name": "Alma Area Rug",
   "product_class": "area rug",
   "category": "Rugs",
   "features": "color:white|material:wool|style:industrial",
   "description": "A carpet for your home. Solid build for daily use."
  },
  {
   "product_id": 64,
   "product_name": "Elio Area Rug",
   "product_class": "area rug",
   "category": "Rugs",
   "features": "color:beige|material:wool|style:modern",
   "description": "A carpet for your home. Easy to assemble."
  },
  {
   "product_id": 65,
   "product_name": "Brook Desk",
   "product_class": "desk",
   "category": "Office Furniture",
   "features": "color:green|material:oak|style:mid-century",
   "description": "A writing desk for your home. Comes with a 2-year warranty."
  },
  {
   "product_id": 66,
   "product_name": "Dane Desk",
   "product_class": "desk",
   "category": "Office Furniture",
   "features": "color:black|material:metal|style:mid-century",
   "description": "A writing desk for your home. Solid build for daily use."
  },
  {
   "product_id": 67,
   "product_name": "Faye Desk",
   "product_class": "desk",
   "category": "Office Furniture",
   "features": "color:beige|material:oak|style:mid-century",
   "description": "A writing desk for your home. Comes with a 2-year warranty."
  },
  {
   "product_id": 68,
   "product_name": "Elio Desk",
   "product_class": "desk",
   "category": "Office Furniture",
   "features": "color:brown|material:metal|style:mid-century",
   "description": "A writing desk made of metal. Easy to assemble."
  },
  {
   "product_id": 69,
   "product_name": "Dane Desk",
   "product_class": "desk",
   "category": "Office Furniture",
   "features": "color:beige|material:oak|style:scandinavian",
   "description": "A writing desk made of oak. Comes with a 2-year warranty."
  },
  {
   "product_id": 70,
   "product_name": "Dane Desk",
   "product_class": "desk",
   "category": "Office Furniture",
   "features": "color:green|material:walnut|style:mid-century",
   "description": "A writing desk made of walnut. Solid build for daily use."
  },
  {
   "product_id": 71,
   "product_name": "Brook Desk",
   "product_class": "desk",
   "category": "Office Furniture",
   "features": "color:beige|material:walnut|style:rustic",
   "description": "A writing desk for your home. Fits small spaces."
  },
  {
   "product_id": 72,
   "product_name": "Gus Desk",
   "product_class": "desk",
   "category": "Office Furniture",
   "features": "color:green|material:metal|style:industrial",
   "description": "A writing desk for your home. Fits small spaces."
  },
  {
   "product_id": 73,
   "product_name": "Cora Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:grey|material:oak|style:rustic",
   "description": "A bookshelf for your home. Fits small spaces."
  },
  {
   "product_id": 74,
   "product_name": "Gus Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:grey|material:oak|style:industrial",
   "description": "A bookshelf for your home. Fits small spaces."
  },
  {
   "product_id": 75,
   "product_name": "Brook Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:beige|material:metal|style:industrial",
   "description": "A bookshelf for your home. Solid build for daily use."
  },
  {
   "product_id": 76,
   "product_name": "Alma Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:green|material:oak|style:scandinavian",
   "description": "A bookshelf for your home. Solid build for daily use."
  },
  {
   "product_id": 77,
   "product_name": "Faye Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:green|material:pine|style:modern",
   "description": "A bookshelf for your home. Easy to assemble."
  },
  {
   "product_id": 78,
   "product_name": "Elio Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:white|material:pine|style:industrial",
   "description": "A bookshelf for your home. Fits small spaces."
  },
  {
   "product_id": 79,
   "product_name": "Iris Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:beige|material:metal|style:rustic",
   "description": "A bookshelf made of metal. Comes with a 2-year warranty."
  },
  {
   "product_id": 80,
   "product_name": "Juno Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:white|material:pine|style:mid-century",
   "description": "A bookshelf for your home. Comes with a 2-year warranty."
  },
  {
   "product_id": 81,
   "product_name": "Kai Dining Chair",
   "product_class": "dining chair",
   "category": "Kitchen & Dining",
   "features": "color:black|material:oak|style:rustic",
   "description": "A side chair for your home."
  },
  {
   "product_id": 82,
   "product_name": "Kai Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:green|material:linen|style:rustic",
   "description": "A settee for your home."
  },
  {
   "product_id": 83,
   "product_name": "Kai Sofa",
   "product_class": "sofa",
   "category": "Living Room Furniture",
   "features": "color:beige|material:velvet|style:modern",
   "description": "A settee for your home."
  },
  {
   "product_id": 84,
   "product_name": "Kai Bookcase",
   "product_class": "bookcase",
   "category": "Storage",
   "features": "color:black|material:metal|style:scandinavian",
   "description": "A bookshelf for your home."
  }
 ],
 "queries": [
  {
   "query_id": 1,
   "query": "grey velvet sofa"
  },
  {
   "query_id": 2,
   "query": "leather couch"
  },
  {
   "query_id": 3,
   "query": "3 seat sofa"
  },
  {
   "query_id": 4,
   "query": "oak dining table"
  },
  {
   "query_id": 5,
   "query": "kitchen table glass"
  },
  {
   "query_id": 6,
   "query": "mid-century armchair"
  },
  {
   "query_id": 7,
   "query": "accent chair blue"
  },
  {
   "query_id": 8,
   "query": "metal desk"
  },
  {
   "query_id": 9,
   "query": "writing desk walnut"
  },
  {
   "query_id": 10,
   "query": "wool rug"
  },
  {
   "query_id": 11,
   "query": "jute carpet"
  },
  {
   "query_id": 12,
   "query": "brass floor lamp"
  },
  {
   "query_id": 13,
   "query": "industrial lamp"
  },
  {
   "query_id": 14,
   "query": "platform bed oak"
  },
  {
   "query_id": 15,
   "query": "upholstered bed"
  },
  {
   "query_id": 16,
   "query": "scandinavian bookshelf"
  },
  {
   "query_id": 17,
   "query": "pine bookcase"
  },
  {
   "query_id": 18,
   "query": "marble coffee table"
  },
  {
   "query_id": 19,
   "query": "white dining chair"
  },
  {
   "query_id": 20,
   "query": "rustic side chair"
  },
  {
   "query_id": 21,
   "query": "green settee"
  },
  {
   "query_id": 22,
   "query": "modern beige sofa"
  },
  {
   "query_id": 23,
   "query": "black metal bookcase"
  },
  {
   "query_id": 24,
   "query": "cotton area rug"
  }
 ],
 "labels": [
  {
   "query_id": 1,
   "product_id": 1,
   "label": "Partial"
  },
  {
   "query_id": 1,
   "product_id": 2,
   "label": "Partial"
  },
  {
   "query_id": 1,
   "product_id": 3,
   "label": "Exact"
  },
  {
   "query_id": 1,
   "product_id": 4,
   "label": "Partial"
  },
  {
   "query_id": 1,
   "product_id": 5,
   "label": "Partial"
  },
  {
   "query_id": 1,
   "product_id": 6,
   "label": "Partial"
  },
  {
   "query_id": 1,
   "product_id": 7,
   "label": "Partial"
  },
  {
   "query_id": 1,
   "product_id": 8,
   "label": "Partial"
  },
  {
   "query_id": 1,
   "product_id": 82,
   "label": "Partial"
  },
  {
   "query_id": 1,
   "product_id": 83,
   "label": "Partial"
  },
  {
   "query_id": 2,
   "product_id": 1,
   "label": "Partial"
  },
  {
   "query_id": 2,
   "product_id": 2,
   "label": "Partial"
  },
  {
   "query_id": 2,
   "product_id": 3,
   "label": "Partial"
  },
  {
   "query_id": 2,
   "product_id": 4,
   "label": "Exact"
  },
  {
   "query_id": 2,
   "product_id": 5,
   "label": "Partial"
  },
  {
   "query_id": 2,
   "product_id": 6,
   "label": "Partial"
  },
  {
   "query_id": 2,
   "product_id": 7,
   "label": "Partial"
  },
  {
   "query_id": 2,
   "product_id": 8,
   "label": "Exact"
  },
  {
   "query_id": 2,
   "product_id": 82,
   "label": "Partial"
  },
  {
   "query_id": 2,
   "product_id": 83,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 1,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 2,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 3,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 4,
   "label": "Exact"
  },
  {
   "query_id": 3,
   "product_id": 5,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 6,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 7,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 8,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 82,
   "label": "Partial"
  },
  {
   "query_id": 3,
   "product_id": 83,
   "label": "Partial"
  },
  {
   "query_id": 4,
   "product_id": 33,
   "label": "Exact"
  },
  {
   "query_id": 4,
   "product_id": 34,
   "label": "Exact"
  },
  {
   "query_id": 4,
   "product_id": 35,
   "label": "Partial"
  },
  {
   "query_id": 4,
   "product_id": 36,
   "label": "Partial"
  },
  {
   "query_id": 4,
   "product_id": 37,
   "label": "Partial"
  },
  {
   "query_id": 4,
   "product_id": 38,
   "label": "Partial"
  },
  {
   "query_id": 4,
   "product_id": 39,
   "label": "Partial"
  },
  {
   "query_id": 4,
   "product_id": 40,
   "label": "Exact"
  },
  {
   "query_id": 5,
   "product_id": 33,
   "label": "Partial"
  },
  {
   "query_id": 5,
   "product_id": 34,
   "label": "Partial"
  },
  {
   "query_id": 5,
   "product_id": 35,
   "label": "Partial"
  },
  {
   "query_id": 5,
   "product_id": 36,
   "label": "Exact"
  },
  {
   "query_id": 5,
   "product_id": 37,
   "label": "Partial"
  },
  {
   "query_id": 5,
   "product_id": 38,
   "label": "Partial"
  },
  {
   "query_id": 5,
   "product_id": 39,
   "label": "Exact"
  },
  {
   "query_id": 5,
   "product_id": 40,
   "label": "Partial"
  },
  {
   "query_id": 6,
   "product_id": 9,
   "label": "Partial"
  },
  {
   "query_id": 6,
   "product_id": 10,
   "label": "Partial"
  },
  {
   "query_id": 6,
   "product_id": 11,
   "label": "Partial"
  },
  {
   "query_id": 6,
   "product_id": 12,
   "label": "Exact"
  },
  {
   "query_id": 6,
   "product_id": 13,
   "label": "Partial"
  },
  {
   "query_id": 6,
   "product_id": 14,
   "label": "Exact"
  },
  {
   "query_id": 6,
   "product_id": 15,
   "label": "Exact"
  },
  {
   "query_id": 6,
   "product_id": 16,
   "label": "Partial"
  },
  {
   "query_id": 7,
   "product_id": 9,
   "label": "Partial"
  },
  {
   "query_id": 7,
   "product_id": 10,
   "label": "Partial"
  },
  {
   "query_id": 7,
   "product_id": 11,
   "label": "Exact"
  },
  {
   "query_id": 7,
   "product_id": 12,
   "label": "Partial"
  },
  {
   "query_id": 7,
   "product_id": 13,
   "label": "Partial"
  },
  {
   "query_id": 7,
   "product_id": 14,
   "label": "Partial"
  },
  {
   "query_id": 7,
   "product_id": 15,
   "label": "Partial"
  },
  {
   "query_id": 7,
   "product_id": 16,
   "label": "Exact"
  },
  {
   "query_id": 8,
   "product_id": 65,
   "label": "Partial"
  },
  {
   "query_id": 8,
   "product_id": 66,
   "label": "Exact"
  },
  {
   "query_id": 8,
   "product_id": 67,
   "label": "Partial"
  },
  {
   "query_id": 8,
   "product_id": 68,
   "label": "Exact"
  },
  {
   "query_id": 8,
   "product_id": 69,
   "label": "Partial"
  },
  {
   "query_id": 8,
   "product_id": 70,
   "label": "Partial"
  },
  {
   "query_id": 8,
   "product_id": 71,
   "label": "Partial"
  },
  {
   "query_id": 8,
   "product_id": 72,
   "label": "Exact"
  },
  {
   "query_id": 9,
   "product_id": 65,
   "label": "Partial"
  },
  {
   "query_id": 9,
   "product_id": 66,
   "label": "Partial"
  },
  {
   "query_id": 9,
   "product_id": 67,
   "label": "Partial"
  },
  {
   "query_id": 9,
   "product_id": 68,
   "label": "Partial"
  },
  {
   "query_id": 9,
   "product_id": 69,
   "label": "Partial"
  },
  {
   "query_id": 9,
   "product_id": 70,
   "label": "Exact"
  },
  {
   "query_id": 9,
   "product_id": 71,
   "label": "Exact"
  },
  {
   "query_id": 9,
   "product_id": 72,
   "label": "Partial"
  },
  {
   "query_id": 10,
   "product_id": 57,
   "label": "Exact"
  },
  {
   "query_id": 10,
   "product_id": 58,
   "label": "Partial"
  },
  {
   "query_id": 10,
   "product_id": 59,
   "label": "Partial"
  },
  {
   "query_id": 10,
   "product_id": 60,
   "label": "Exact"
  },
  {
   "query_id": 10,
   "product_id": 61,
   "label": "Partial"
  },
  {
   "query_id": 10,
   "product_id": 62,
   "label": "Partial"
  },
  {
   "query_id": 10,
   "product_id": 63,
   "label": "Exact"
  },
  {
   "query_id": 10,
   "product_id": 64,
   "label": "Exact"
  },
  {
   "query_id": 11,
   "product_id": 57,
   "label": "Partial"
  },
  {
   "query_id": 11,
   "product_id": 58,
   "label": "Partial"
  },
  {
   "query_id": 11,
   "product_id": 59,
   "label": "Exact"
  },
  {
   "query_id": 11,
   "product_id": 60,
   "label": "Partial"
  },
  {
   "query_id": 11,
   "product_id": 61,
   "label": "Exact"
  },
  {
   "query_id": 11,
   "product_id": 62,
   "label": "Partial"
  },
  {
   "query_id": 11,
   "product_id": 63,
   "label": "Partial"
  },
  {
   "query_id": 11,
   "product_id": 64,
   "label": "Partial"
  },
  {
   "query_id": 12,
   "product_id": 49,
   "label": "Partial"
  },
  {
   "query_id": 12,
   "product_id": 50,
   "label": "Partial"
  },
  {
   "query_id": 12,
   "product_id": 51,
   "label": "Partial"
  },
  {
   "query_id": 12,
   "product_id": 52,
   "label": "Partial"
  },
  {
   "query_id": 12,
   "product_id": 53,
   "label": "Exact"
  },
  {
   "query_id": 12,
   "product_id": 54,
   "label": "Partial"
  },
  {
   "query_id": 12,
   "product_id": 55,
   "label": "Partial"
  },
  {
   "query_id": 12,
   "product_id": 56,
   "label": "Partial"
  },
  {
   "query_id": 13,
   "product_id": 49,
   "label": "Partial"
  },
  {
   "query_id": 13,
   "product_id": 50,
   "label": "Partial"
  },
  {
   "query_id": 13,
   "product_id": 51,
   "label": "Partial"
  },
  {
   "query_id": 13,
   "product_id": 52,
   "label": "Partial"
  },
  {
   "query_id": 13,
   "product_id": 53,
   "label": "Exact"
  },
  {
   "query_id": 13,
   "product_id": 54,
   "label": "Exact"
  },
  {
   "query_id": 13,
   "product_id": 55,
   "label": "Partial"
  },
  {
   "query_id": 13,
   "product_id": 56,
   "label": "Exact"
  },
  {
   "query_id": 14,
   "product_id": 41,
   "label": "Partial"
  },
  {
   "query_id": 14,
   "product_id": 42,
   "label": "Partial"
  },
  {
   "query_id": 14,
   "product_id": 43,
   "label": "Exact"
  },
  {
   "query_id": 14,
   "product_id": 44,
   "label": "Partial"
  },
  {
   "query_id": 14,
   "product_id": 45,
   "label": "Partial"
  },
  {
   "query_id": 14,
   "product_id": 46,
   "label": "Exact"
  },
  {
   "query_id": 14,
   "product_id": 47,
   "label": "Partial"
  },
  {
   "query_id": 14,
   "product_id": 48,
   "label": "Partial"
  },
  {
   "query_id": 15,
   "product_id": 41,
   "label": "Partial"
  },
  {
   "query_id": 15,
   "product_id": 42,
   "label": "Exact"
  },
  {
   "query_id": 15,
   "product_id": 43,
   "label": "Partial"
  },
  {
   "query_id": 15,
   "product_id": 44,
   "label": "Partial"
  },
  {
   "query_id": 15,
   "product_id": 45,
   "label": "Partial"
  },
  {
   "query_id": 15,
   "product_id": 46,
   "label": "Partial"
  },
  {
   "query_id": 15,
   "product_id": 47,
   "label": "Partial"
  },
  {
   "query_id": 15,
   "product_id": 48,
   "label": "Exact"
  },
  {
   "query_id": 16,
   "product_id": 73,
   "label": "Partial"
  },
  {
   "query_id": 16,
   "product_id": 74,
   "label": "Partial"
  },
  {
   "query_id": 16,
   "product_id": 75,
   "label": "Partial"
  },
  {
   "query_id": 16,
   "product_id": 76,
   "label": "Exact"
  },
  {
   "query_id": 16,
   "product_id": 77,
   "label": "Partial"
  },
  {
   "query_id": 16,
   "product_id": 78,
   "label": "Partial"
  },
  {
   "query_id": 16,
   "product_id": 79,
   "label": "Partial"
  },
  {
   "query_id": 16,
   "product_id": 80,
   "label": "Partial"
  },
  {
   "query_id": 16,
   "product_id": 84,
   "label": "Exact"
  },
  {
   "query_id": 17,
   "product_id": 73,
   "label": "Partial"
  },
  {
   "query_id": 17,
   "product_id": 74,
   "label": "Partial"
  },
  {
   "query_id": 17,
   "product_id": 75,
   "label": "Partial"
  },
  {
   "query_id": 17,
   "product_id": 76,
   "label": "Partial"
  },
  {
   "query_id": 17,
   "product_id": 77,
   "label": "Exact"
  },
  {
   "query_id": 17,
   "product_id": 78,
   "label": "Exact"
  },
  {
   "query_id": 17,
   "product_id": 79,
   "label": "Partial"
  },
  {
   "query_id": 17,
   "product_id": 80,
   "label": "Exact"
  },
  {
   "query_id": 17,
   "product_id": 84,
   "label": "Partial"
  },
  {
   "query_id": 18,
   "product_id": 25,
   "label": "Partial"
  },
  {
   "query_id": 18,
   "product_id": 26,
   "label": "Partial"
  },
  {
   "query_id": 18,
   "product_id": 27,
   "label": "Partial"
  },
  {
   "query_id": 18,
   "product_id": 28,
   "label": "Partial"
  },
  {
   "query_id": 18,
   "product_id": 29,
   "label": "Exact"
  },
  {
   "query_id": 18,
   "product_id": 30,
   "label": "Exact"
  },
  {
   "query_id": 18,
   "product_id": 31,
   "label": "Partial"
  },
  {
   "query_id": 18,
   "product_id": 32,
   "label": "Partial"
  },
  {
   "query_id": 19,
   "product_id": 17,
   "label": "Partial"
  },
  {
   "query_id": 19,
   "product_id": 18,
   "label": "Exact"
  },
  {
   "query_id": 19,
   "product_id": 19,
   "label": "Partial"
  },
  {
   "query_id": 19,
   "product_id": 20,
   "label": "Partial"
  },
  {
   "query_id": 19,
   "product_id": 21,
   "label": "Partial"
  },
  {
   "query_id": 19,
   "product_id": 22,
   "label": "Exact"
  },
  {
   "query_id": 19,
   "product_id": 23,
   "label": "Partial"
  },
  {
   "query_id": 19,
   "product_id": 24,
   "label": "Partial"
  },
  {
   "query_id": 19,
   "product_id": 81,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 17,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 18,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 19,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 20,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 21,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 22,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 23,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 24,
   "label": "Partial"
  },
  {
   "query_id": 20,
   "product_id": 81,
   "label": "Exact"
  },
  {
   "query_id": 21,
   "product_id": 1,
   "label": "Partial"
  },
  {
   "query_id": 21,
   "product_id": 2,
   "label": "Partial"
  },
  {
   "query_id": 21,
   "product_id": 3,
   "label": "Partial"
  },
  {
   "query_id": 21,
   "product_id": 4,
   "label": "Partial"
  },
  {
   "query_id": 21,
   "product_id": 5,
   "label": "Partial"
  },
  {
   "query_id": 21,
   "product_id": 6,
   "label": "Partial"
  },
  {
   "query_id": 21,
   "product_id": 7,
   "label": "Partial"
  },
  {
   "query_id": 21,
   "product_id": 8,
   "label": "Partial"
  },
  {
   "query_id": 21,
   "product_id": 82,
   "label": "Exact"
  },
  {
   "query_id": 21,
   "product_id": 83,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 1,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 2,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 3,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 4,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 5,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 6,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 7,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 8,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 82,
   "label": "Partial"
  },
  {
   "query_id": 22,
   "product_id": 83,
   "label": "Exact"
  },
  {
   "query_id": 23,
   "product_id": 73,
   "label": "Partial"
  },
  {
   "query_id": 23,
   "product_id": 74,
   "label": "Partial"
  },
  {
   "query_id": 23,
   "product_id": 75,
   "label": "Partial"
  },
  {
   "query_id": 23,
   "product_id": 76,
   "label": "Partial"
  },
  {
   "query_id": 23,
   "product_id": 77,
   "label": "Partial"
  },
  {
   "query_id": 23,
   "product_id": 78,
   "label": "Partial"
  },
  {
   "query_id": 23,
   "product_id": 79,
   "label": "Partial"
  },
  {
   "query_id": 23,
   "product_id": 80,
   "label": "Partial"
  },
  {
   "query_id": 23,
   "product_id": 84,
   "label": "Exact"
  },
  {
   "query_id": 24,
   "product_id": 57,
   "label": "Partial"
  },
  {
   "query_id": 24,
   "product_id": 58,
   "label": "Exact"
  },
  {
   "query_id": 24,
   "product_id": 59,
   "label": "Partial"
  },
  {
   "query_id": 24,
   "product_id": 60,
   "label": "Partial"
  },
  {
   "query_id": 24,
   "product_id": 61,
   "label": "Partial"
  },
  {
   "query_id": 24,
   "product_id": 62,
   "label": "Exact"
  },
  {
   "query_id": 24,
   "product_id": 63,
   "label": "Partial"
  },
  {
   "query_id": 24,
   "product_id": 64,
   "label": "Partial"
  }
 ]
}
````

## 5. فایل اصلی: product_search.py
_GitHub · حدود 5 دقیقه_

**چرا:** همه‌ی منطق در یک فایل: ساختن متن محصول (basic و rich)، BM25، جست‌وجوی سه‌حرفی، embedding اختیاری، ترکیب RRF، معیارهای درجه‌دار nDCG@10، recall@10 و MRR، و bootstrap برای اینکه بفهمی تفاوت واقعی است یا نه.

1. **Add file → Create new file**، در کادر نام بنویس `product_search.py`. commit: `Add product search: product text, BM25, trigrams, RRF, graded metrics, bootstrap`.

`product_search.py`

````python
"""Product search for an online furniture shop: product text (basic vs rich), BM25, character-trigram search,
optional dense embeddings, hybrid fusion with RRF, and graded evaluation (nDCG@10, recall@10, MRR) with a bootstrap test."""
import json
import math
import re
from collections import Counter

import numpy as np

STOP = {"a", "an", "the", "and", "or", "for", "of", "to", "in", "on", "with", "by", "is", "it", "this"}
GRADE = {"Exact": 2, "Partial": 1, "Irrelevant": 0}


# ---------- data ----------

def load_data(path="data/products.json"):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    qrels = {}
    for lab in d["labels"]:
        qrels.setdefault(lab["query_id"], {})[lab["product_id"]] = GRADE[lab["label"]]
    return d["products"], {q["query_id"]: q["query"] for q in d["queries"]}, qrels


def features_to_text(raw):
    return "; ".join(f"{k}: {v}" for k, v in (p.split(":", 1) for p in raw.split("|") if ":" in p))


def product_text(p, rich=True):
    """basic = name + description; rich adds the class, the category and the structured features."""
    if not rich:
        return p["product_name"] + ". " + p["description"]
    return (f"{p['product_name']}\nCategory: {p['product_class']} ({p['category']})\n"
            f"Features: {features_to_text(p['features'])}\nDescription: {p['description']}")


# ---------- search ----------

def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class BM25:
    def __init__(self, texts, k1=1.5, b=0.75):
        toks = [tokenize(t) for t in texts]
        self.k1, self.b, self.n = k1, b, len(texts)
        self.tf = [Counter(t) for t in toks]
        self.len = [len(t) for t in toks]
        self.avg = sum(self.len) / self.n
        self.df = Counter(w for t in toks for w in set(t))

    def scores(self, query):
        s = np.zeros(self.n)
        for w in tokenize(query):
            df = self.df.get(w, 0)
            if not df:
                continue
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            for i in range(self.n):
                tf = self.tf[i].get(w, 0)
                if tf:
                    s[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        return s


def trigram_scores(query, texts):
    def grams(t):
        out = set()
        for w in re.findall(r"[a-z0-9]+", t.lower()):
            w = f" {w} "
            out |= {w[i:i + 3] for i in range(len(w) - 2)}
        return out
    q = grams(query)
    return np.array([len(q & g) / len(q | g) if q | g else 0.0 for g in map(grams, texts)])


def top_k(scores, ids, k=10):
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    return [ids[i] for i in order if scores[i] > 0][:k]


def rrf(lists, k=60):
    score = {}
    for lst in lists:
        for rank, pid in enumerate(lst, start=1):
            score[pid] = score.get(pid, 0.0) + 1 / (k + rank)
    return sorted(score, key=lambda p: (-score[p], p))


class Dense:
    """Embedding search with sentence-transformers (optional; only if the package is installed)."""

    def __init__(self, texts, model="sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)
        self.emb = self.model.encode(texts, normalize_embeddings=True)

    def scores(self, query):
        return self.emb @ self.model.encode(query, normalize_embeddings=True)


# ---------- evaluation ----------

def dcg(gains):
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg(ranked, rel, k=10):
    best = dcg(sorted(rel.values(), reverse=True)[:k])
    return dcg([rel.get(p, 0) for p in ranked[:k]]) / best if best else float("nan")


def recall(ranked, rel, k=10):
    exact = {p for p, g in rel.items() if g == 2}
    return len(exact & set(ranked[:k])) / len(exact) if exact else float("nan")


def mrr(ranked, rel):
    return next((1 / (i + 1) for i, p in enumerate(ranked) if rel.get(p) == 2), 0.0)


def evaluate(run, qrels):
    """run: query_id -> ranked product ids. Returns per-query metrics (for the bootstrap) and their means."""
    per_query = {q: {"ndcg@10": ndcg(r, qrels[q]), "recall@10": recall(r, qrels[q]), "mrr": mrr(r, qrels[q])} for q, r in run.items()}
    means = {m: round(float(np.nanmean([v[m] for v in per_query.values()])), 3) for m in ["ndcg@10", "recall@10", "mrr"]}
    return per_query, means


def bootstrap(a, b, n=10000, seed=42):
    """Is b better than a on the same queries? Mean difference, 95% interval and the share of resamples where b <= a."""
    diff = np.array([b[q] - a[q] for q in a])
    rng = np.random.default_rng(seed)
    means = diff[rng.integers(0, len(diff), size=(n, len(diff)))].mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    return {"diff": round(float(diff.mean()), 3), "low": round(float(low), 3), "high": round(float(high), 3),
            "p": round(float((means <= 0).mean()), 4)}
````

<details><summary><b>درک کد: تابع به تابع</b></summary>

- **`load_data و product_text`**: برچسب‌های Exact/Partial به ۲/۱ تبدیل می‌شوند. متن rich دسته و ویژگی‌های ساخت‌یافته را هم دارد؛ رنگ و جنس اغلب فقط آنجا هستند.
- **`BM25 و trigram_scores`**: همان BM25 و سه‌حرفی‌های p01، این بار با numpy و روی محصولات. ([درس](../../lessons/p01_faq_search/step02_bm25/lesson.md))
- **`top_k و rrf`**: مرتب‌سازی قطعی با شکستن تساوی با اندیس؛ RRF دو فهرست را با رتبه ترکیب می‌کند. ([درس](../../lessons/p01_faq_search/step04_hybrid_rrf/lesson.md))
- **`Dense`**: اختیاری: embedding با sentence-transformers؛ شباهت کسینوسی با ضرب داخلی بردارهای نرمال‌شده.
- **`dcg، ndcg، recall، mrr، evaluate`**: nDCG برچسب درجه‌دار را می‌فهمد: Exact در رتبه‌ی ۱ از Partial در رتبه‌ی ۱ بهتر است. recall فقط Exact را می‌شمارد. evaluate امتیاز هر query را هم برمی‌گرداند. ([درس](../../lessons/p01_faq_search/step03_metrics/lesson.md))
- **`bootstrap`**: ۱۰٬۰۰۰ بار نمونه‌برداری دوباره از اختلاف‌های هر query؛ اگر حد پایین بازه‌ی ۹۵٪ بیشتر از صفر باشد، بهبود واقعی است.

</details>

## 6. فایل check_setup.py
_GitHub · حدود 2 دقیقه_

**چرا:** یک بررسی کوچک که بعد از نصب روی لپ‌تاپ اجرا می‌کنی تا مطمئن شوی پایتون، داده و توابع اصلی کار می‌کنند، قبل از notebook.

1. **Add file → Create new file**، نام `check_setup.py`. commit: `Add setup check`.

`check_setup.py`

````python
"""Run once after installing: checks Python, the data and the metrics."""
import sys

from product_search import load_data, ndcg, product_text, recall

print("Python", sys.version.split()[0])
products, queries, qrels = load_data()
print(len(products), "products,", len(queries), "queries,", sum(len(v) for v in qrels.values()), "labels")
print(product_text(products[0]))
rel = {10: 2, 11: 1, 12: 0}
print(ndcg([10, 11, 12], rel), round(ndcg([12, 11, 10], rel), 3), recall([10], rel))
print("setup ok")
````

## 7. تست‌ها: tests/test_product_search.py
_GitHub · حدود 3 دقیقه_

**چرا:** تست‌ها معیارها را با مثال کوچکی که جوابش را می‌دانیم چک می‌کنند و مطمئن می‌شوند متن rich روی این داده از basic بهتر است. هیچ مدلی لازم نیست.

1. **Add file → Create new file**، نام `tests/test_product_search.py`. commit: `Add tests`.

`tests/test_product_search.py`

````python
from product_search import BM25, bootstrap, evaluate, load_data, mrr, ndcg, product_text, recall, rrf, top_k, trigram_scores


def test_metrics():
    rel = {10: 2, 11: 1, 12: 0}
    assert ndcg([10, 11, 12], rel) == 1.0 and ndcg([12, 11, 10], rel) < 1
    assert recall([10], rel) == 1.0 and mrr([12, 10], rel) == 0.5


def test_rich_text_contains_structured_features():
    p = load_data()[0][0]
    assert "|" not in product_text(p) and "color: " in product_text(p) and "Category" not in product_text(p, rich=False)


def test_search_and_fusion():
    texts = ["grey velvet sofa", "oak dining table", "brass floor lamp"]
    assert top_k(BM25(texts).scores("velvet sofa"), [1, 2, 3])[0] == 1
    assert top_k(trigram_scores("dinning tabel", texts), [1, 2, 3])[0] == 2
    assert rrf([[3, 1], [3, 2]])[0] == 3


def test_rich_text_beats_basic_on_the_sample():
    products, queries, qrels = load_data()
    ids = [p["product_id"] for p in products]
    res = {}
    for rich in (False, True):
        bm = BM25([product_text(p, rich) for p in products])
        res[rich] = evaluate({q: top_k(bm.scores(t), ids, 10) for q, t in queries.items()}, qrels)
    assert res[True][1]["ndcg@10"] > res[False][1]["ndcg@10"]
    sig = bootstrap({q: v["ndcg@10"] for q, v in res[False][0].items()}, {q: v["ndcg@10"] for q, v in res[True][0].items()})
    assert sig["diff"] > 0 and sig["low"] <= sig["diff"] <= sig["high"]
````

## 8. تست خودکار در GitHub (Actions)
_GitHub · حدود 3 دقیقه_

**چرا:** با هر push، GitHub تست‌ها را روی یک ماشین تمیز اجرا می‌کند. تیک سبز یعنی پروژه روی هر سیستمی کار می‌کند، نه فقط لپ‌تاپ تو.

1. **Add file → Create new file**، نام `.github/workflows/tests.yml`. commit: `Add CI`.
2. به تب **Actions** برو و چند ثانیه صبر کن.

`.github/workflows/tests.yml`

````
name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python check_setup.py
      - run: pytest -q
````

> **باید ببینی:** در تب Actions یک اجرای `tests` با تیک سبز. اگر قرمز شد، رویش کلیک کن: خطا دقیقاً می‌گوید کدام فایل یا خط.

## 9. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
_VS Code · حدود 8 دقیقه_

**چرا:** محیط مجازی (venv) یک پایتون جدا فقط برای این پروژه است تا بسته‌هایش با پروژه‌های دیگر قاطی نشوند.

پیش‌نیاز: Git (از git-scm.com) و Python 3.10 یا جدیدتر، و در VS Code افزونه‌های **Python** و **Jupyter** از Microsoft.

1. VS Code: `Ctrl+Shift+P` → **Git: Clone** → آدرس `https://github.com/<نام-کاربری-تو>/product_search.git` → یک پوشه انتخاب کن → **Open**.
2. ترمینال را باز کن: ``Ctrl+` ``

_ترمینال VS Code · Windows PowerShell_

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

_ترمینال VS Code_

```
python check_setup.py
python -m pytest -q
```

**باید ببینی:**

```
Python 3.x.y
84 products, 24 queries, 207 labels
Elio Sofa
Category: sofa (Living Room Furniture)
Features: color: white; material: velvet; style: modern; seats: 4
Description: A settee made of velvet. Solid build for daily use. Seats 4.
1.0 0.587 1.0
setup ok

....                                                                     [100%]
4 passed
```

> **حواست باشد:** اگر PowerShell گفت running scripts is disabled: یک بار `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` و دوباره فعال کن. روی Mac/Linux به‌جای خط دوم: `source .venv/bin/activate`.

## 10. ساختن و اجرای notebook
_VS Code · حدود 15 دقیقه_

**چرا:** notebook داستان پروژه است: دو شکل متن محصول، سه روش جست‌وجو، اثر غلط املایی، و آزمون bootstrap که می‌گوید کدام بهبود واقعی است.

1. VS Code: `Ctrl+Shift+P` → **Create: New Jupyter Notebook** → `Ctrl+S` با نام `01_product_search.ipynb` در پوشه‌ی repo.
2. بالا سمت راست **Select Kernel → Python Environments → .venv**.
3. سلول‌ها را به ترتیب زیر بساز (متن: **+ Markdown**، کد: **+ Code**) و هر سلول کد را با `Shift+Enter` اجرا کن. خروجی را با «باید ببینی» زیرش مقایسه کن.

_سلول متنی (Markdown):_

````markdown
# Product search for a furniture shop

84 products, 24 shopper queries and graded labels (Exact = 2, Partial = 1). Questions: does richer product text help
(category + structured features), do typo-tolerant trigrams and hybrid fusion help, and is the difference real?
Metrics: nDCG@10 (graded), recall@10 (Exact only), MRR.
````

_سلول کد 1:_

```python
from product_search import BM25, bootstrap, evaluate, load_data, product_text, rrf, top_k, trigram_scores

products, queries, qrels = load_data()
ids = [p["product_id"] for p in products]
print(len(products), "products,", len(queries), "queries")
print(product_text(products[0], rich=False))
print("---")
print(product_text(products[0], rich=True))
```

داده و دو شکل متن محصول: basic (نام + توضیح) و rich (به‌علاوه‌ی دسته و ویژگی‌های ساخت‌یافته مثل رنگ و جنس).

**باید ببینی:**

```
84 products, 24 queries
Elio Sofa. A settee made of velvet. Solid build for daily use. Seats 4.
---
Elio Sofa
Category: sofa (Living Room Furniture)
Features: color: white; material: velvet; style: modern; seats: 4
Description: A settee made of velvet. Solid build for daily use. Seats 4.
```

_سلول متنی (Markdown):_

````markdown
## Basic vs rich product text (BM25)
````

_سلول کد 2:_

```python
runs, scores = {}, {}
for name, rich in [("bm25 basic", False), ("bm25 rich", True)]:
    bm = BM25([product_text(p, rich) for p in products])
    runs[name] = {q: top_k(bm.scores(t), ids, 10) for q, t in queries.items()}
    per_query, means = evaluate(runs[name], qrels)
    scores[name] = per_query
    print(f"{name:14s}", means)
```

متن rich بهتر است چون رنگ و جنس محصول اغلب فقط در ویژگی‌های ساخت‌یافته هست، نه در نام یا توضیح.

**باید ببینی:**

```
bm25 basic     {'ndcg@10': 0.841, 'recall@10': 0.958, 'mrr': 0.699}
bm25 rich      {'ndcg@10': 0.941, 'recall@10': 1.0, 'mrr': 0.972}
```

_سلول متنی (Markdown):_

````markdown
## Typos and hybrid search
Character trigrams survive typos ("velvt sofa"); RRF fuses BM25 and trigram rankings by rank only.
````

_سلول کد 3:_

```python
rich_texts = [product_text(p) for p in products]
bm_rich = BM25(rich_texts)
runs["trigram rich"] = {q: top_k(trigram_scores(t, rich_texts), ids, 10) for q, t in queries.items()}
runs["hybrid rrf"] = {q: rrf([top_k(bm_rich.scores(t), ids, 50), top_k(trigram_scores(t, rich_texts), ids, 50)])[:10]
                        for q, t in queries.items()}
for name in ["trigram rich", "hybrid rrf"]:
    scores[name], means = evaluate(runs[name], qrels)
    print(f"{name:14s}", means)
print()
by_id = {p["product_id"]: p for p in products}
show = lambda pids: [by_id[p]["product_class"] for p in pids]
for q in ["grey velvt sofaa", "oak dinning tabel"]:
    print(f"{q:18s} bm25: {show(top_k(bm_rich.scores(q), ids, 3))}")
    print(f"{'':18s} hybrid: {show(rrf([top_k(bm_rich.scores(q), ids, 50), top_k(trigram_scores(q, rich_texts), ids, 50)])[:3])}")
```

روی این داده، hybrid اولین نتیجه‌ی درست را بالاتر می‌آورد (MRR بیشتر) ولی nDCG کمی کمتر از BM25 روی متن rich دارد: ترکیب همیشه در همه‌ی معیارها برنده نیست. در دو query غلط‌دار پایین ببین BM25 چه دسته‌ای برمی‌گرداند و hybrid چه.

**باید ببینی:**

```
trigram rich   {'ndcg@10': 0.915, 'recall@10': 1.0, 'mrr': 1.0}
hybrid rrf     {'ndcg@10': 0.926, 'recall@10': 1.0, 'mrr': 1.0}

grey velvt sofaa   bm25: ['bookcase', 'bookcase', 'floor lamp']
                   hybrid: ['armchair', 'sofa', 'sofa']
oak dinning tabel  bm25: ['dining table', 'desk', 'dining table']
                   hybrid: ['dining table', 'dining table', 'dining table']
```

_سلول متنی (Markdown):_

````markdown
## Is the difference real? (bootstrap over the 24 queries)
````

_سلول کد 4:_

```python
import json, os

base = {q: v["ndcg@10"] for q, v in scores["bm25 basic"].items()}
sig = {name: bootstrap(base, {q: v["ndcg@10"] for q, v in scores[name].items()}) for name in scores if name != "bm25 basic"}
for name, s in sig.items():
    print(f"{name:14s}", s)
table = {name: evaluate(runs[name], qrels)[1] for name in runs}
os.makedirs("results", exist_ok=True)
with open("results/results.json", "w") as f:
    json.dump({"table": table, "vs_basic": sig}, f, indent=2)
```

برای هر روش در برابر bm25/basic: `diff` اختلاف میانگین nDCG، و `low`..`high` بازه‌ی ۹۵٪. اگر `low` بزرگ‌تر از صفر باشد، بهبود واقعی است (نه شانس ۲۴ سؤال).

**باید ببینی:**

```
bm25 rich      {'diff': 0.1, 'low': 0.045, 'high': 0.154, 'p': 0.0}
trigram rich   {'diff': 0.073, 'low': -0.001, 'high': 0.156, 'p': 0.028}
hybrid rrf     {'diff': 0.085, 'low': 0.019, 'high': 0.158, 'p': 0.0044}
```

_سلول متنی (Markdown):_

````markdown
## Dense embeddings (optional)
Needs `pip install sentence-transformers` (downloads a small model). Skipped otherwise.
````

_سلول کد 5:_

```python
try:
    from product_search import Dense
    dense = Dense(rich_texts)
    runs["dense rich"] = {q: top_k(dense.scores(t), ids, 10) for q, t in queries.items()}
    print("dense rich  ", evaluate(runs["dense rich"], qrels)[1])
except ImportError:
    print("sentence-transformers is not installed: dense search skipped")
```

اختیاری. بدون sentence-transformers فقط پیام رد شدن چاپ می‌شود. با آن، می‌بینی embedding روی هم‌معنی‌ها (couch/sofa) چه می‌کند.

**باید ببینی:**

```
sentence-transformers is not installed: dense search skipped
```

_سلول متنی (Markdown):_

````markdown
## Limitations
- Synthetic catalogue (84 products) with rule-based labels: good for learning the method, not for claims.
  The same pipeline on the real WANDS dataset (43k products, 233k human labels) is the next step.
- 24 queries: use the bootstrap interval, not the point estimate.
````

> **نکته:** اگر نمی‌خواهی سلول‌ها را یکی‌یکی بسازی: دکمه‌ی **دانلود notebook** بالای سلول‌ها فایل آماده را می‌دهد؛ در پوشه‌ی repo بگذار و Run All. ولی یک بار دستی ساختن، کد را بهتر در ذهنت می‌نشاند.

## 11. commit و push از VS Code
_VS Code · GitHub · حدود 3 دقیقه_

**چرا:** notebook با خروجی‌هایش و فایل نتایج باید در GitHub باشند تا بدون اجرا دیده شوند.

1. پنل Source Control: `Ctrl+Shift+G`. فایل‌های `01_product_search.ipynb` و `results/results.json` را می‌بینی.
2. پیام: `Add notebook: product text, hybrid search and bootstrap` → **Commit** → **Sync Changes**.

> **باید ببینی:** در GitHub، `01_product_search.ipynb` را باز کن: جدول‌ها و خروجی‌ها بدون اجرا دیده می‌شوند. تب Actions دوباره سبز است.

> **حواست باشد:** قانون ساده: قبل از هر کار در VS Code اول **Pull** بزن، و یک فایل را هم‌زمان در GitHub و VS Code ویرایش نکن.

## 12. README نهایی
_GitHub · حدود 10 دقیقه_

**چرا:** README صفحه‌ی اول پروژه است: در ۳۰ ثانیه بگوید چه مسئله‌ای، چه روشی، چه عددی و چه محدودیتی. عددها را از `results/results.json` خودت بردار، نه از این صفحه.

1. در GitHub روی `README.md` → آیکون مداد → متن زیر را جایگزین کن و عددهای `{...}` را پر کن (یا results.json را پایین paste کن). commit: `Write README`.
2. نام کاربری‌ات را در خط badge جایگزین کن.

````markdown
# Product search for a furniture shop

![tests](https://github.com/<your-user>/product_search/actions/workflows/tests.yml/badge.svg)

Search over a furniture catalogue, measured with graded relevance labels. Compares basic vs rich product text (structured
features), BM25, typo-tolerant character trigrams and hybrid fusion (RRF), with a bootstrap test for every difference.

## Results (`results/results.json`, 24 queries)
| method | nDCG@10 | recall@10 | MRR |
|---|---|---|---|
| BM25, basic text | {basic_ndcg} | {basic_recall} | {basic_mrr} |
| BM25, rich text | {rich_ndcg} | {rich_recall} | {rich_mrr} |
| trigram, rich text | {tri_ndcg} | {tri_recall} | {tri_mrr} |
| hybrid (RRF) | {hyb_ndcg} | {hyb_recall} | {hyb_mrr} |

Rich text vs basic: nDCG difference {rich_diff} (95% bootstrap interval {rich_low} to {rich_high}).

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_product_search.ipynb` and run all cells. Optional dense search: `pip install sentence-transformers`.

## Limitations
- Synthetic catalogue with rule-based labels; the next step is the real WANDS dataset (Wayfair, MIT licence).
- 24 queries: read the bootstrap interval, not only the mean.

## Licence
MIT
````

## 13. صیقل نهایی repo
_GitHub · حدود 5 دقیقه_

**چرا:** جزئیات کوچکی که repo را حرفه‌ای نشان می‌دهد.

1. صفحه‌ی repo → چرخ‌دنده‌ی **About** → Topics: `information-retrieval`, `search`, `bm25`, `evaluation`, `python`.
2. در پروفایل GitHub: **Customize your pins** → این repo را pin کن.
3. خط رزومه‌ی پایین را با عددهای خودت بردار.

**خط رزومه:** Built a product search engine (BM25 over structured product text, typo-tolerant trigrams, hybrid RRF) evaluated with graded relevance: nDCG@10 {base} → {ndcg} from enriching product text, with bootstrap confidence intervals; tested with pytest and GitHub Actions.

## اگر به خطا خوردی
- **`No module named product_search` در notebook**: notebook باید در همان پوشه‌ی `product_search.py` باشد و kernel روی `.venv` باشد.
- **`FileNotFoundError: data/products.json`**: فایل داده را با مسیر دقیق `data/products.json` ساخته‌ای؟ notebook را از پوشه‌ی repo اجرا کن.
- **`python` شناخته نمی‌شود**: Python را با تیک «Add to PATH» نصب کن، یا به‌جای `python` بنویس `py`.
- **تب Actions قرمز است**: روی اجرای قرمز کلیک کن؛ معمولاً یک فایل با نام یا مسیر اشتباه ساخته شده (مثلاً `test/` به‌جای `tests/`).

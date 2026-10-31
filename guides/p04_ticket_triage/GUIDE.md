# ساختن طبقه‌بندی و مسیریابی تیکت با ارجاع به انسان، از صفر در GitHub

تیکت‌های پشتیبانی را به ۶ دسته تقسیم می‌کنی و فقط وقتی مدل به اندازه‌ی کافی مطمئن است تیکت را خودکار مسیریابی می‌کنی؛ بقیه به انسان می‌روند. سه درس مهم با عدد: نشت داده (leakage) با تقسیم تصادفی، کالیبراسیون اطمینان، و اینکه مدل گاهی روی اشتباهش مطمئن است. بدون GPU؛ مدل زبانی اختیاری برای مقایسه.

> نسخه‌ی تعاملی (تیک مراحل، مقایسه‌ی خروجی، پرسیدن از Claude، دانلود notebook): صفحه‌ی «راهنمای ساخت پروژه‌ها» (claude.ai artifact).

**برای فهمیدن بهتر:** پروژه در نقشه‌ی راه (نقشه‌ی راه، پروژه‌ی `p04_ticket_triage`) · [مقایسه‌ی مدل‌ها با عدد: درس m01](../../lessons/m01_compare_models/README.md)

## مراحل
1. ساختن repo در GitHub
2. فایل .gitignore
3. فایل requirements.txt
4. فایل داده: data/tickets.json
5. فایل اصلی: triage.py
6. فایل check_setup.py
7. تست‌ها: tests/test_triage.py
8. تست خودکار در GitHub (Actions)
9. آوردن repo به لپ‌تاپ و ساختن محیط پایتون
10. ساختن و اجرای notebook
11. مقایسه با مدل زبانی (اختیاری)
12. commit و push از VS Code
13. README نهایی
14. صیقل نهایی repo

## 1. ساختن repo در GitHub
_GitHub · حدود 3 دقیقه_

**چرا:** repo خودت نمونه‌کار توست: هر فایلی که اینجا می‌سازی، کارفرما می‌بیند. اسم و توضیح کوتاه و دقیق، اولین چیزی است که دیده می‌شود.

1. در github.com بالا سمت راست **+** → **New repository**.
2. **Repository name:** `ticket_triage`
3. **Description:** `Support-ticket triage: TF-IDF + logistic regression with a leakage-free split, temperature calibration and a confidence threshold that sends uncertain tickets to a human`
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

**چرا:** numpy و scikit-learn (TF-IDF، logistic regression، تقسیم گروهی). بسته‌های مدل زبانی اختیاری‌اند.

1. **Add file → Create new file**، نام `requirements.txt`. commit: `Add requirements`.

`requirements.txt`

````
numpy>=1.24
scikit-learn>=1.3
pytest>=8.0
ipykernel>=6.29
# optional model providers (zero-shot comparison)
# ollama>=0.4
# anthropic>=0.40
````

## 4. فایل داده: data/tickets.json
_GitHub · حدود 3 دقیقه_

**چرا:** ۲۴۰ تیکت ساختگی در ۶ دسته. هر تیکت از یکی از ۶۰ «قالب جمله» ساخته شده (ستون `template`)، با کمی غلط تایپی. ستون template برای تقسیم درست لازم است: همان جمله‌بندی نباید هم در آموزش باشد و هم در آزمون.

1. **Add file → Create new file**، در کادر نام بنویس `data/tickets.json` (با تایپ `/` خود GitHub پوشه را می‌سازد). commit: `Add synthetic support tickets`.

`data/tickets.json`

````json
{
"tickets": [
{
"text": "how do i cancel an order that is processing",
"label": "cancel_order",
"template": "cancel_order-3"
},
{
"text": "the desk came damaged, order #47988",
"label": "damaged_item",
"template": "damaged_item-0"
},
{
"text": "password reset email never arrives",
"label": "account_access",
"template": "account_access-5"
},
{
"text": "how do i cancel an order that is processing",
"label": "cancel_order",
"template": "cancel_order-3"
},
{
"text": "one leg of the lamp is cracked",
"label": "damaged_item",
"template": "damaged_item-6"
},
{
"text": "can you reimburse me for the mirror",
"label": "refund",
"template": "refund-8"
},
{
"text": "the bookcase is damaged and unusable",
"label": "damaged_item",
"template": "damaged_item-2"
},
{
"text": "still waiting for my refund, returned the mirror 19 days ago",
"label": "refund",
"template": "refund-7"
},
{
"text": "how do i cancel an orderthat is processing",
"label": "cancel_order",
"template": "cancel_order-3"
},
{
"text": "you charged me twice for #84868, i want a refund",
"label": "refund",
"template": "refund-1"
},
{
"text": "can i get the invoice in my company's name",
"label": "invoice",
"template": "invoice-9"
},
{
"text": "I want my money back for order #55482",
"label": "refund",
"template": "refund-4"
},
{
"text": "still waiting or my refund, returned the mirror 14 days ago",
"label": "refund",
"template": "refund-7"
},
{
"text": "account access problem, cannotsign in",
"label": "account_access",
"template": "account_access-3"
},
{
"text": "order #79366: the rug is scratched",
"label": "damaged_item",
"template": "damaged_item-5"
},
{
"text": "I need an invoice for order #66439",
"label": "invoice",
"template": "invoice-4"
},
{
"text": "i changed my mind, cancel the order",
"label": "cancel_order",
"template": "cancel_order-2"
},
{
"text": "I cannot log in to my account",
"label": "account_access",
"template": "account_access-4"
},
{
"text": "order #12858: the lamp is scratched",
"label": "damaged_item",
"template": "damaged_item-5"
},
{
"text": "how do I change the email on my account",
"label": "account_access",
"template": "account_access-7"
},
{
"text": "please refund order #46493, the bookcase was not what I expected",
"label": "refund",
"template": "refund-5"
},
{
"text": "where is my order #77732? it is 1 days late",
"label": "shipping_delay",
"template": "shipping_delay-4"
},
{
"text": "the sofa delivery is delayed again",
"label": "shipping_delay",
"template": "shipping_delay-1"
},
{
"text": "the rug arrived broken",
"label": "damaged_item",
"template": "damaged_item-4"
},
{
"text": "delivery was promised last week, order #65217",
"label": "shipping_delay",
"template": "shipping_delay-7"
},
{
"text": "please correct the invoice for #18794",
"label": "invoice",
"template": "invoice-1"
},
{
"text": "can I still cancel #23751 before it ships?",
"label": "cancel_order",
"template": "cancel_order-6"
},
{
"text": "I need a copy of the invoice",
"label": "invoice",
"template": "invoice-2"
},
{
"text": "the invoice for #77040 has the wrong address",
"label": "invoice",
"template": "invoice-5"
},
{
"text": "the box was crushed and the mirror is damaged",
"label": "damaged_item",
"template": "damaged_item-7"
},
{
"text": "invoice amount for #48138 is wrong",
"label": "invoice",
"template": "invoice-8"
},
{
"text": "when will the bed frame be delivered?",
"label": "shipping_delay",
"template": "shipping_delay-8"
},
{
"text": "login fails with my email",
"label": "account_access",
"template": "account_access-2"
},
{
"text": "courier says the sofa is not shipped yet",
"label": "shipping_delay",
"template": "shipping_delay-3"
},
{
"text": "I need a copy of the invoice",
"label": "invoice",
"template": "invoice-2"
},
{
"text": "no update on my delivery for 16 days",
"label": "shipping_delay",
"template": "shipping_delay-2"
},
{
"text": "returned the rug, when do I get my money",
"label": "refund",
"template": "refund-2"
},
{
"text": "the box was crushed and the bookcase is damaged",
"label": "damaged_item",
"template": "damaged_item-7"
},
{
"text": "order #77847 is late, where is it",
"label": "shipping_delay",
"template": "shipping_delay-0"
},
{
"text": "please cancel order #15461",
"label": "cancel_order",
"template": "cancel_order-4"
},
{
"text": "i ordered the bookcase by mistake, cancel it",
"label": "cancel_order",
"template": "cancel_order-5"
},
{
"text": "tracking for #44025 has not mved in 16 days",
"label": "shipping_delay",
"template": "shipping_delay-6"
},
{
"text": "can you reimburse me fr the mirror",
"label": "refund",
"template": "refund-8"
},
{
"text": "stop my order #4024, I found it cheaper",
"label": "cancel_order",
"template": "cancel_order-7"
},
{
"text": "my account is locked after 11 attempts",
"label": "account_access",
"template": "account_access-6"
},
{
"text": "please refund order #82016, the desk was not what I expected",
"label": "refund",
"template": "refund-5"
},
{
"text": "tracking for #72657 has not moved in 18 days",
"label": "shipping_delay",
"template": "shipping_delay-6"
},
{
"text": "where can i download my invoice",
"label": "invoice",
"template": "invoice-7"
},
{
"text": "how long until I get the refund for #51761?",
"label": "refund",
"template": "refund-6"
},
{
"text": "courier says he chair is not shipped yet",
"label": "shipping_delay",
"template": "shipping_delay-3"
},
{
"text": "broken chair in the parcel",
"label": "damaged_item",
"template": "damaged_item-1"
},
{
"text": "i need a copy of the invoice",
"label": "invoice",
"template": "invoice-2"
},
{
"text": "how do I change the email on my account",
"label": "account_access",
"template": "account_access-7"
},
{
"text": "the invoice for #95556 has the wrong address",
"label": "invoice",
"template": "invoice-5"
},
{
"text": "refund status for #75889 please",
"label": "refund",
"template": "refund-9"
},
{
"text": "password reset email never arrives",
"label": "account_access",
"template": "account_access-5"
},
{
"text": "delivery was promised last week, order #39322",
"label": "shipping_delay",
"template": "shipping_delay-7"
},
{
"text": "sill waiting for my refund, returned the lamp 5 days ago",
"label": "refund",
"template": "refund-7"
},
{
"text": "one lg of the mirror is cracked",
"label": "damaged_item",
"template": "damaged_item-6"
},
{
"text": "can i get the invoice in my company's name",
"label": "invoice",
"template": "invoice-9"
},
{
"text": "I changed my mind, cancel the order",
"label": "cancel_order",
"template": "cancel_order-2"
},
{
"text": "ivoice needed for my expense report",
"label": "invoice",
"template": "invoice-3"
},
{
"text": "where is my order #29634? it is 6 days late",
"label": "shipping_delay",
"template": "shipping_delay-4"
},
{
"text": "invoice missing for order #10770",
"label": "invoice",
"template": "invoice-0"
},
{
"text": "the desk is damaged and unusable",
"label": "damaged_item",
"template": "damaged_item-2"
},
{
"text": "cancel the desk from my last order",
"label": "cancel_order",
"template": "cancel_order-8"
},
{
"text": "can you reimburseme for the chair",
"label": "refund",
"template": "refund-8"
},
{
"text": "cancel the desk from my last order",
"label": "cancel_order",
"template": "cancel_order-8"
},
{
"text": "please send a VAT invoice",
"label": "invoice",
"template": "invoice-6"
},
{
"text": "can you reimburse me for the bed frame",
"label": "refund",
"template": "refund-8"
},
{
"text": "broken rug in the parcel",
"label": "damaged_item",
"template": "damaged_item-1"
},
{
"text": "one leg of the chair is cracked",
"label": "damaged_item",
"template": "damaged_item-6"
},
{
"text": "invoice needed for my expense report",
"label": "invoice",
"template": "invoice-3"
},
{
"text": "invoice amount for #29162 is wrong",
"label": "invoice",
"template": "invoice-8"
},
{
"text": "please cancel #34832 immeditely",
"label": "cancel_order",
"template": "cancel_order-1"
},
{
"text": "parcel#84789 seems lost",
"label": "shipping_delay",
"template": "shipping_delay-9"
},
{
"text": "i cannot log in to my account",
"label": "account_access",
"template": "account_access-4"
},
{
"text": "account access problem, cannot sgn in",
"label": "account_access",
"template": "account_access-3"
},
{
"text": "please corrct the invoice for #58607",
"label": "invoice",
"template": "invoice-1"
},
{
"text": "two-factor code does not work",
"label": "account_access",
"template": "account_access-8"
},
{
"text": "cancel my order for the sofa",
"label": "cancel_order",
"template": "cancel_order-0"
},
{
"text": "please send a VAT invoice",
"label": "invoice",
"template": "invoice-6"
},
{
"text": "inoice missing for order #63243",
"label": "invoice",
"template": "invoice-0"
},
{
"text": "account access problem, cannot sign in",
"label": "account_access",
"template": "account_access-3"
},
{
"text": "i need to cancel, order #46643",
"label": "cancel_order",
"template": "cancel_order-9"
},
{
"text": "the bed frame came damged, order #59296",
"label": "damaged_item",
"template": "damaged_item-0"
},
{
"text": "please cancel #95210 immediately",
"label": "cancel_order",
"template": "cancel_order-1"
},
{
"text": "invoice amount for #33167 is wrong",
"label": "invoice",
"template": "invoice-8"
},
{
"text": "the bookcase as a big dent",
"label": "damaged_item",
"template": "damaged_item-9"
},
{
"text": "I forgot my password and cannot reset it",
"label": "account_access",
"template": "account_access-1"
},
{
"text": "the desk arrived roken",
"label": "damaged_item",
"template": "damaged_item-4"
},
{
"text": "glass on the bookcase was shattered on arrival",
"label": "damaged_item",
"template": "damaged_item-3"
},
{
"text": "the chai has a big dent",
"label": "damaged_item",
"template": "damaged_item-9"
},
{
"text": "how do I change the email on my account",
"label": "account_access",
"template": "account_access-7"
},
{
"text": "how long until I ge the refund for #40583?",
"label": "refund",
"template": "refund-6"
},
{
"text": "the chair delivery is delayed again",
"label": "shipping_delay",
"template": "shipping_delay-1"
},
{
"text": "the box was crushed and the desk is damaged",
"label": "damaged_item",
"template": "damaged_item-7"
},
{
"text": "I ordered the lamp by mistake, cancel it",
"label": "cancel_order",
"template": "cancel_order-5"
},
{
"text": "please send a VAT invoice",
"label": "invoice",
"template": "invoice-6"
},
{
"text": "how do i cancel an order that is processing",
"label": "cancel_order",
"template": "cancel_order-3"
},
{
"text": "returned the sofa, when do i get my money",
"label": "refund",
"template": "refund-2"
},
{
"text": "stopmy order #95397, I found it cheaper",
"label": "cancel_order",
"template": "cancel_order-7"
},
{
"text": "can i still cancel #43055 before it ships?",
"label": "cancel_order",
"template": "cancel_order-6"
},
{
"text": "cancel my order for the lamp",
"label": "cancel_order",
"template": "cancel_order-0"
},
{
"text": "cancel my order for the lamp",
"label": "cancel_order",
"template": "cancel_order-0"
},
{
"text": "I changed my mind, cancel the order",
"label": "cancel_order",
"template": "cancel_order-2"
},
{
"text": "I want my money back for order #97051",
"label": "refund",
"template": "refund-4"
},
{
"text": "you charged me twice for #16105, I want a refund",
"label": "refund",
"template": "refund-1"
},
{
"text": "stop my order #16127, I found it cheaper",
"label": "cancel_order",
"template": "cancel_order-7"
},
{
"text": "I need to cancel, order #44315",
"label": "cancel_order",
"template": "cancel_order-9"
},
{
"text": "I need an invoice fororder #96126",
"label": "invoice",
"template": "invoice-4"
},
{
"text": "login fails with my email",
"label": "account_access",
"template": "account_access-2"
},
{
"text": "my account is loked after 8 attempts",
"label": "account_access",
"template": "account_access-6"
},
{
"text": "two-factor code does not work",
"label": "account_access",
"template": "account_access-8"
},
{
"text": "broken desk in the parcel",
"label": "damaged_item",
"template": "damaged_item-1"
},
{
"text": "password reset email never arrives",
"label": "account_access",
"template": "account_access-5"
},
{
"text": "someone else may have accessed my account",
"label": "account_access",
"template": "account_access-9"
},
{
"text": "one leg of the lamp is racked",
"label": "damaged_item",
"template": "damaged_item-6"
},
{
"text": "you charged me wice for #92657, I want a refund",
"label": "refund",
"template": "refund-1"
},
{
"text": "I want my money back for order #85752",
"label": "refund",
"template": "refund-4"
},
{
"text": "i need an invoice for order #91119",
"label": "invoice",
"template": "invoice-4"
},
{
"text": "i need to cancel, order #37618",
"label": "cancel_order",
"template": "cancel_order-9"
},
{
"text": "when will the bed frame be delivered?",
"label": "shipping_delay",
"template": "shipping_delay-8"
},
{
"text": "I cannot log in to my account",
"label": "account_access",
"template": "account_access-4"
},
{
"text": "when willthe chair be delivered?",
"label": "shipping_delay",
"template": "shipping_delay-8"
},
{
"text": "I cannot log in to my account",
"label": "account_access",
"template": "account_access-4"
},
{
"text": "two-facor code does not work",
"label": "account_access",
"template": "account_access-8"
},
{
"text": "courier says the bed frame is not shipped yet",
"label": "shipping_delay",
"template": "shipping_delay-3"
},
{
"text": "parcel #65747 seems lost",
"label": "shipping_delay",
"template": "shipping_delay-9"
},
{
"text": "locked out of my account",
"label": "account_access",
"template": "account_access-0"
},
{
"text": "received a damaged bookcase in order #98403",
"label": "damaged_item",
"template": "damaged_item-8"
},
{
"text": "please correct the invoice for #82292",
"label": "invoice",
"template": "invoice-1"
},
{
"text": "account access problem, cannot sign in",
"label": "account_access",
"template": "account_access-3"
},
{
"text": "glass on the mirror was shattered on arrival",
"label": "damaged_item",
"template": "damaged_item-3"
},
{
"text": "the mirror came damaged order #99337",
"label": "damaged_item",
"template": "damaged_item-0"
},
{
"text": "please cancel order#10648",
"label": "cancel_order",
"template": "cancel_order-4"
},
{
"text": "my mirror has not arrived yet",
"label": "shipping_delay",
"template": "shipping_delay-5"
},
{
"text": "please cacel #75547 immediately",
"label": "cancel_order",
"template": "cancel_order-1"
},
{
"text": "please cancel order #21073",
"label": "cancel_order",
"template": "cancel_order-4"
},
{
"text": "no update on my delivery for 6 days",
"label": "shipping_delay",
"template": "shipping_delay-2"
},
{
"text": "cancel my order for the desk",
"label": "cancel_order",
"template": "cancel_order-0"
},
{
"text": "where can I download my invoice",
"label": "invoice",
"template": "invoice-7"
},
{
"text": "how do I change the email on my account",
"label": "account_access",
"template": "account_access-7"
},
{
"text": "invoice missing for order #57681",
"label": "invoice",
"template": "invoice-0"
},
{
"text": "locked out of my account",
"label": "account_access",
"template": "account_access-0"
},
{
"text": "order #55125 is late, where is it",
"label": "shipping_delay",
"template": "shipping_delay-0"
},
{
"text": "someone else may have accessed my account",
"label": "account_access",
"template": "account_access-9"
},
{
"text": "my account is loced after 20 attempts",
"label": "account_access",
"template": "account_access-6"
},
{
"text": "please refund order #62153, the bookcase was not what i expected",
"label": "refund",
"template": "refund-5"
},
{
"text": "courier says the bed frame is not shipped yet",
"label": "shipping_delay",
"template": "shipping_delay-3"
},
{
"text": "when will the ofa be delivered?",
"label": "shipping_delay",
"template": "shipping_delay-8"
},
{
"text": "the rug has a big dent",
"label": "damaged_item",
"template": "damaged_item-9"
},
{
"text": "glass on the bokcase was shattered on arrival",
"label": "damaged_item",
"template": "damaged_item-3"
},
{
"text": "where can I download my invoice",
"label": "invoice",
"template": "invoice-7"
},
{
"text": "two-factorcode does not work",
"label": "account_access",
"template": "account_access-8"
},
{
"text": "delivery was promised last week, order #57996",
"label": "shipping_delay",
"template": "shipping_delay-7"
},
{
"text": "I was promised a refund 6 days ago",
"label": "refund",
"template": "refund-3"
},
{
"text": "please send a VAT invoice",
"label": "invoice",
"template": "invoice-6"
},
{
"text": "please cancel #14843 immediately",
"label": "cancel_order",
"template": "cancel_order-1"
},
{
"text": "still waiting for my refund, returned the lamp 19 days ago",
"label": "refund",
"template": "refund-7"
},
{
"text": "returned the bed frame, when do I get my money",
"label": "refund",
"template": "refund-2"
},
{
"text": "where is my order #82938? it is 12 days late",
"label": "shipping_delay",
"template": "shipping_delay-4"
},
{
"text": "tracking for #51416 has not moved in 9 days",
"label": "shipping_delay",
"template": "shipping_delay-6"
},
{
"text": "someone else may have accessed my account",
"label": "account_access",
"template": "account_access-9"
},
{
"text": "where is my order #12451? it is 7 days late",
"label": "shipping_delay",
"template": "shipping_delay-4"
},
{
"text": "can I get the invoice inmy company's name",
"label": "invoice",
"template": "invoice-9"
},
{
"text": "can  get the invoice in my company's name",
"label": "invoice",
"template": "invoice-9"
},
{
"text": "I forgot my password and cannot reset it",
"label": "account_access",
"template": "account_access-1"
},
{
"text": "please refund orer #74709, the sofa was not what I expected",
"label": "refund",
"template": "refund-5"
},
{
"text": "i need to cancel, order #73719",
"label": "cancel_order",
"template": "cancel_order-9"
},
{
"text": "stop my order #73674, I found it cheaper",
"label": "cancel_order",
"template": "cancel_order-7"
},
{
"text": "please cancel order #72212",
"label": "cancel_order",
"template": "cancel_order-4"
},
{
"text": "refund for the bed frame please, order #22337",
"label": "refund",
"template": "refund-0"
},
{
"text": "the rug arrived broken",
"label": "damaged_item",
"template": "damaged_item-4"
},
{
"text": "the chair came damaged, order #62200",
"label": "damaged_item",
"template": "damaged_item-0"
},
{
"text": "I was promised a refund 21 ays ago",
"label": "refund",
"template": "refund-3"
},
{
"text": "loked out of my account",
"label": "account_access",
"template": "account_access-0"
},
{
"text": "parcel #98601 seems lost",
"label": "shipping_delay",
"template": "shipping_delay-9"
},
{
"text": "invoice amount for #93786 is wrong",
"label": "invoice",
"template": "invoice-8"
},
{
"text": "parcl #44151 seems lost",
"label": "shipping_delay",
"template": "shipping_delay-9"
},
{
"text": "the sofa is damaged and unusable",
"label": "damaged_item",
"template": "damaged_item-2"
},
{
"text": "the chair delivery is delayed again",
"label": "shipping_delay",
"template": "shipping_delay-1"
},
{
"text": "someone else may have accessed my account",
"label": "account_access",
"template": "account_access-9"
},
{
"text": "can i still cancel #19189 before it ships?",
"label": "cancel_order",
"template": "cancel_order-6"
},
{
"text": "invoice needed for my expense report",
"label": "invoice",
"template": "invoice-3"
},
{
"text": "I need an invoice for oder #70068",
"label": "invoice",
"template": "invoice-4"
},
{
"text": "the bookcase is damged and unusable",
"label": "damaged_item",
"template": "damaged_item-2"
},
{
"text": "i forgot my passwod and cannot reset it",
"label": "account_access",
"template": "account_access-1"
},
{
"text": "received a damaged bed frame in order #65123",
"label": "damaged_item",
"template": "damaged_item-8"
},
{
"text": "invoice needed for my expense report",
"label": "invoice",
"template": "invoice-3"
},
{
"text": "n update on my delivery for 6 days",
"label": "shipping_delay",
"template": "shipping_delay-2"
},
{
"text": "can i still cancel #92080 before it ships?",
"label": "cancel_order",
"template": "cancel_order-6"
},
{
"text": "refund status for #79239 please",
"label": "refund",
"template": "refund-9"
},
{
"text": "no update on my delivery for 21 days",
"label": "shipping_delay",
"template": "shipping_delay-2"
},
{
"text": "login fails with my email",
"label": "account_access",
"template": "account_access-2"
},
{
"text": "order #62396: the mirror is scratched",
"label": "damaged_item",
"template": "damaged_item-5"
},
{
"text": "the chair has a big dent",
"label": "damaged_item",
"template": "damaged_item-9"
},
{
"text": "refund for the ookcase please, order #82226",
"label": "refund",
"template": "refund-0"
},
{
"text": "how long until I get the refund for #10536?",
"label": "refund",
"template": "refund-6"
},
{
"text": "where can I download my invoice",
"label": "invoice",
"template": "invoice-7"
},
{
"text": "order #35578 is late, where is it",
"label": "shipping_delay",
"template": "shipping_delay-0"
},
{
"text": "mychair has not arrived yet",
"label": "shipping_delay",
"template": "shipping_delay-5"
},
{
"text": "the mirror delivery is delayed again",
"label": "shipping_delay",
"template": "shipping_delay-1"
},
{
"text": "i ordered the rug by misake, cancel it",
"label": "cancel_order",
"template": "cancel_order-5"
},
{
"text": "you charged me twice for #84830, I wan a refund",
"label": "refund",
"template": "refund-1"
},
{
"text": "the bed frame arrived broken",
"label": "damaged_item",
"template": "damaged_item-4"
},
{
"text": "I was promised a refund 13 days ago",
"label": "refund",
"template": "refund-3"
},
{
"text": "returned the desk, when do I get my money",
"label": "refund",
"template": "refund-2"
},
{
"text": "refund for the lamp please, order #2445",
"label": "refund",
"template": "refund-0"
},
{
"text": "order #46623 is late, where is it",
"label": "shipping_delay",
"template": "shipping_delay-0"
},
{
"text": "my rug has not arrived yet",
"label": "shipping_delay",
"template": "shipping_delay-5"
},
{
"text": "broken lamp in the parcel",
"label": "damaged_item",
"template": "damaged_item-1"
},
{
"text": "my account is locked after 5 attempts",
"label": "account_access",
"template": "account_access-6"
},
{
"text": "glass on the desk was shattered on arrival",
"label": "damaged_item",
"template": "damaged_item-3"
},
{
"text": "received a damaged rug in order #58525",
"label": "damaged_item",
"template": "damaged_item-8"
},
{
"text": "cancel the rug from my last order",
"label": "cancel_order",
"template": "cancel_order-8"
},
{
"text": "the box was crushed and the chair is damaged",
"label": "damaged_item",
"template": "damaged_item-7"
},
{
"text": "the invoice for #24363 has the wrong address",
"label": "invoice",
"template": "invoice-5"
},
{
"text": "received a damaged desk in order #63976",
"label": "damaged_item",
"template": "damaged_item-8"
},
{
"text": "I changed my mind, cancel the order",
"label": "cancel_order",
"template": "cancel_order-2"
},
{
"text": "order #72032: the mirror is scratched",
"label": "damaged_item",
"template": "damaged_item-5"
},
{
"text": "I need a copy of he invoice",
"label": "invoice",
"template": "invoice-2"
},
{
"text": "I forgot my pasword and cannot reset it",
"label": "account_access",
"template": "account_access-1"
},
{
"text": "I was promised a refund 19 days ago",
"label": "refund",
"template": "refund-3"
},
{
"text": "refund for the chair please, order #14914",
"label": "refund",
"template": "refund-0"
},
{
"text": "tracking for #49685 has not moved in 6 days",
"label": "shipping_delay",
"template": "shipping_delay-6"
},
{
"text": "please correct the invoice for 35865",
"label": "invoice",
"template": "invoice-1"
},
{
"text": "I ordered the sofa by mistake, cancel it",
"label": "cancel_order",
"template": "cancel_order-5"
},
{
"text": "delivery was promised last week, order #3871",
"label": "shipping_delay",
"template": "shipping_delay-7"
},
{
"text": "invoice missing for order #84254",
"label": "invoice",
"template": "invoice-0"
},
{
"text": "login fails with my email",
"label": "account_access",
"template": "account_access-2"
},
{
"text": "the invoice for #31641 has the wrong address",
"label": "invoice",
"template": "invoice-5"
},
{
"text": "refund status for #79220 please",
"label": "refund",
"template": "refund-9"
},
{
"text": "locked out of my account",
"label": "account_access",
"template": "account_access-0"
},
{
"text": "I want my money back for order #69795",
"label": "refund",
"template": "refund-4"
},
{
"text": "how long until i get the refund for #40245?",
"label": "refund",
"template": "refund-6"
},
{
"text": "cancel the desk from my last order",
"label": "cancel_order",
"template": "cancel_order-8"
},
{
"text": "refund status for #58064 please",
"label": "refund",
"template": "refund-9"
},
{
"text": "password reset email never arrivs",
"label": "account_access",
"template": "account_access-5"
},
{
"text": "my mirror has not arrived yet",
"label": "shipping_delay",
"template": "shipping_delay-5"
}
]
}
````

## 5. فایل اصلی: triage.py
_GitHub · حدود 5 دقیقه_

**چرا:** همه‌ی منطق در یک فایل: تقسیم بر اساس قالب (و تقسیم تصادفی برای مقایسه)، مدل TF-IDF کلمه‌ای و حرفی + logistic regression، اطمینان با temperature، ECE، انتخاب آستانه روی dev برای دقت هدف، coverage و دقت تیکت‌های خودکار، و طبقه‌بند مدل زبانی اختیاری.

1. **Add file → Create new file**، در کادر نام بنویس `triage.py`. commit: `Add triage: leakage-free split, TF-IDF classifier, calibration, human fallback`.

`triage.py`

````python
"""Support-ticket triage: TF-IDF + logistic regression, a leakage-free split by template, calibration (ECE), and a
selective decision: route automatically only when the model is confident enough, otherwise send to a human."""
import json
import os
import re
import shutil
import subprocess

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline, make_union


def load_tickets(path="data/tickets.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["tickets"]


def split(tickets, seed=42):
    """train / dev / test by TEMPLATE: the same wording never appears on both sides (that would be leakage)."""
    groups = [t["template"] for t in tickets]
    idx = np.arange(len(tickets))
    rest, test = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(idx, groups=groups))
    tr, dev = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(rest, groups=[groups[i] for i in rest]))
    pick = lambda ids: [tickets[i] for i in ids]  # noqa: E731
    return pick(rest[tr]), pick(rest[dev]), pick(test)


def random_split(tickets, seed=42):
    """The naive split for comparison: rows shuffled, so near-identical tickets land in train and test."""
    rng = np.random.default_rng(seed)
    ids = rng.permutation(len(tickets))
    n = len(ids)
    return [tickets[i] for i in ids[: n // 2]], [tickets[i] for i in ids[n // 2: 3 * n // 4]], [tickets[i] for i in ids[3 * n // 4:]]


def train(tickets, C=4.0):
    """Word and character n-grams (typos!) into a logistic regression."""
    features = make_union(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                          TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True))
    model = make_pipeline(features, LogisticRegression(C=C, max_iter=2000))
    return model.fit([t["text"] for t in tickets], [t["label"] for t in tickets])


def predict(model, tickets, temperature=1.0):
    """Labels and calibrated confidences (temperature > 1 softens over-confident probabilities)."""
    logits = model.decision_function([t["text"] for t in tickets]) / temperature
    p = np.exp(logits - logits.max(axis=1, keepdims=True))
    p /= p.sum(axis=1, keepdims=True)
    return model.classes_[p.argmax(axis=1)], p.max(axis=1)


def scores(tickets, labels):
    y = [t["label"] for t in tickets]
    return {"accuracy": round(accuracy_score(y, labels), 3), "macro_f1": round(f1_score(y, labels, average="macro"), 3)}


def ece(correct, confidence, bins=10):
    """Expected calibration error: how far the confidence is from the real accuracy, averaged over confidence bins."""
    correct, confidence = np.asarray(correct, float), np.asarray(confidence)
    edges, total = np.linspace(0, 1, bins + 1), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (confidence > lo) & (confidence <= hi)
        if m.any():
            total += m.mean() * abs(correct[m].mean() - confidence[m].mean())
    return round(float(total), 4)


def fit_temperature(model, dev):
    """The temperature that minimises the negative log-likelihood on dev (simple grid search)."""
    y = [t["label"] for t in dev]
    logits = model.decision_function([t["text"] for t in dev])
    cls = list(model.classes_)
    best = (1e9, 1.0)
    for T in np.linspace(0.3, 5, 48):
        z = logits / T
        logp = z - np.log(np.exp(z - z.max(1, keepdims=True)).sum(1, keepdims=True)) - z.max(1, keepdims=True)
        nll = -np.mean([logp[i, cls.index(lab)] for i, lab in enumerate(y)])
        best = min(best, (nll, float(T)))
    return round(best[1], 2)


def choose_threshold(correct, confidence, target_accuracy=0.9, min_auto=5):
    """Sort tickets by confidence, most confident first; return the lowest threshold whose automated set still reaches the
    target accuracy on dev (largest coverage), with at least `min_auto` automated tickets. Nothing safe -> 1.01 (all human)."""
    correct, confidence = np.asarray(correct, float), np.asarray(confidence)
    order = np.argsort(-confidence)
    running = np.cumsum(correct[order]) / np.arange(1, len(order) + 1)
    ok = [i for i in range(min_auto - 1, len(order)) if running[i] >= target_accuracy]
    return float(confidence[order][max(ok)]) if ok else 1.01


def selective(correct, confidence, threshold):
    """Coverage = share routed automatically; error among those is what customers feel."""
    correct, confidence = np.asarray(correct, float), np.asarray(confidence)
    auto = confidence >= threshold
    return {"threshold": round(threshold, 3), "coverage": round(float(auto.mean()), 3),
            "accuracy_automated": round(float(correct[auto].mean()), 3) if auto.any() else None,
            "to_human": int((~auto).sum())}


def confusion(tickets, labels, classes):
    return confusion_matrix([t["label"] for t in tickets], labels, labels=classes)


# ---------- optional: zero-shot LLM classifier for comparison ----------

def llm_classifier(classes, provider=None, model=None):
    """ticket text -> label, asked to Ollama, Claude or OpenCode (TRIAGE_PROVIDER)."""
    provider = provider or os.environ.get("TRIAGE_PROVIDER", "")

    def prompt(text):
        return f"Classify this support ticket into exactly one of: {', '.join(classes)}. Answer with the label only.\nTicket: {text}"
    if provider == "ollama":
        import ollama
        model = model or "qwen2.5:7b"
        ask = lambda text: ollama.chat(model=model, messages=[{"role": "user", "content": prompt(text)}], options={"temperature": 0})["message"]["content"]  # noqa: E731
    elif provider == "anthropic":
        import anthropic
        client, model = anthropic.Anthropic(), model or "claude-sonnet-5-5"
        ask = lambda text: "".join(b.text for b in client.messages.create(model=model, max_tokens=20, messages=[{"role": "user", "content": prompt(text)}]).content if b.type == "text")  # noqa: E731
    elif provider == "opencode":
        if not shutil.which("opencode"):
            raise RuntimeError("opencode is not installed (https://opencode.ai)")
        model = model or "anthropic/claude-sonnet-5-5"
        ask = lambda text: subprocess.run(["opencode", "run", "-m", model, prompt(text)], capture_output=True, text=True, encoding="utf-8", timeout=300).stdout  # noqa: E731
    else:
        raise ValueError("set TRIAGE_PROVIDER to ollama, anthropic or opencode")

    def classify(text):
        out = ask(text).lower()
        return next((c for c in classes if re.search(rf"\b{c}\b", out)), "unknown")
    return classify
````

مدل زبانی برای مقایسه با `TRIAGE_PROVIDER` انتخاب می‌شود: `ollama`، `anthropic` یا `opencode`.

<details><summary><b>درک کد: تابع به تابع</b></summary>

- **`split و random_split`**: تقسیم بر اساس قالب جمله (GroupShuffleSplit) تا همان جمله‌بندی در دو طرف نباشد؛ random_split نسخه‌ی نشت‌دار برای مقایسه است.
- **`train`**: TF-IDF کلمه‌ای (۱ و ۲ کلمه) + حرفی (۲ تا ۴ حرف، برای غلط تایپی) و logistic regression. حرفی‌ها همان چیزی‌اند که delayed را شبیه damaged می‌کنند.
- **`predict، ece، fit_temperature`**: softmax روی امتیازها تقسیم بر temperature. ECE فاصله‌ی اطمینان با دقت واقعی است. temperature روی dev انتخاب می‌شود.
- **`choose_threshold و selective`**: تیکت‌ها از مطمئن‌ترین مرتب می‌شوند؛ پایین‌ترین آستانه‌ای که دقت تیکت‌های خودکار هنوز به هدف می‌رسد. coverage = سهم خودکار؛ بقیه به انسان.
- **`llm_classifier`**: اختیاری: همان کار بدون آموزش با Ollama، Claude یا OpenCode، برای مقایسه.

</details>

## 6. فایل check_setup.py
_GitHub · حدود 2 دقیقه_

**چرا:** یک بررسی کوچک که بعد از نصب روی لپ‌تاپ اجرا می‌کنی تا مطمئن شوی پایتون، داده و توابع اصلی کار می‌کنند، قبل از notebook.

1. **Add file → Create new file**، نام `check_setup.py`. commit: `Add setup check`.

`check_setup.py`

````python
"""Run once after installing: checks Python, scikit-learn, the data and one training run."""
import sys

import sklearn

from triage import load_tickets, predict, scores, split, train

print("Python", sys.version.split()[0], "| scikit-learn", sklearn.__version__)
tickets = load_tickets()
tr, dev, test = split(tickets)
print(len(tickets), "tickets:", len(tr), "train /", len(dev), "dev /", len(test), "test")
model = train(tr)
print("dev", scores(dev, predict(model, dev)[0]))
print("setup ok")
````

## 7. تست‌ها: tests/test_triage.py
_GitHub · حدود 3 دقیقه_

**چرا:** تست‌ها چک می‌کنند هیچ قالبی دو جا نباشد، تقسیم تصادفی نتیجه‌ی بهتری (گول‌زننده) نشان دهد، ECE و انتخاب آستانه درست حساب شوند، و مدل یاد بگیرد.

1. **Add file → Create new file**، نام `tests/test_triage.py`. commit: `Add tests`.

`tests/test_triage.py`

````python
import numpy as np

from triage import choose_threshold, ece, load_tickets, predict, random_split, scores, selective, split, train


def test_split_has_no_template_in_two_places():
    tr, dev, test = split(load_tickets())
    sets = [{t["template"] for t in part} for part in (tr, dev, test)]
    assert not (sets[0] & sets[1]) and not (sets[0] & sets[2]) and not (sets[1] & sets[2])


def test_random_split_looks_better_than_it_is():
    tickets = load_tickets()
    honest = split(tickets)
    leaky = random_split(tickets)
    acc = lambda parts: scores(parts[2], predict(train(parts[0]), parts[2])[0])["accuracy"]  # noqa: E731
    assert acc(leaky) >= acc(honest)


def test_ece_and_selective_decision():
    assert ece([1, 1, 0, 0], [0.9, 0.9, 0.1, 0.1]) < ece([1, 1, 0, 0], [0.9, 0.9, 0.9, 0.9])
    correct, conf = np.array([1, 1, 1, 0]), np.array([0.95, 0.9, 0.8, 0.5])
    th = choose_threshold(correct, conf, 0.95, min_auto=1)
    assert th == 0.8 and selective(correct, conf, th) == {"threshold": 0.8, "coverage": 0.75, "accuracy_automated": 1.0, "to_human": 1}
    assert choose_threshold(np.array([0, 0]), np.array([0.9, 0.8]), min_auto=1) > 1


def test_model_learns():
    tr, dev, _ = split(load_tickets())
    assert scores(dev, predict(train(tr), dev)[0])["accuracy"] > 0.6
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

1. VS Code: `Ctrl+Shift+P` → **Git: Clone** → آدرس `https://github.com/<نام-کاربری-تو>/ticket_triage.git` → یک پوشه انتخاب کن → **Open**.
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
Python 3.x.y | scikit-learn 1.9.1
240 tickets: 132 train / 48 dev / 60 test
dev {'accuracy': 0.792, 'macro_f1': 0.778}
setup ok

....                                                                     [100%]
4 passed
```

> **حواست باشد:** اگر PowerShell گفت running scripts is disabled: یک بار `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` و دوباره فعال کن. روی Mac/Linux به‌جای خط دوم: `source .venv/bin/activate`.

## 10. ساختن و اجرای notebook
_VS Code · حدود 15 دقیقه_

**چرا:** notebook داستان پروژه است: نشت داده با عدد، ماتریس اشتباه، کالیبراسیون، مطمئن‌ترین اشتباه‌ها و مسیریابی با ارجاع به انسان.

1. VS Code: `Ctrl+Shift+P` → **Create: New Jupyter Notebook** → `Ctrl+S` با نام `01_ticket_triage.ipynb` در پوشه‌ی repo.
2. بالا سمت راست **Select Kernel → Python Environments → .venv**.
3. سلول‌ها را به ترتیب زیر بساز (متن: **+ Markdown**، کد: **+ Code**) و هر سلول کد را با `Shift+Enter` اجرا کن. خروجی را با «باید ببینی» زیرش مقایسه کن.

_سلول متنی (Markdown):_

````markdown
# Support-ticket triage with a human fallback

240 synthetic tickets, 6 intents (refund, shipping delay, cancellation, damaged item, account access, invoice), each
written from one of 60 wording templates. The model routes a ticket automatically only when it is confident enough;
everything else goes to a human. Questions: how good is it really (no leakage), are its confidences honest
(calibration), and how many tickets can be automated at a given accuracy?
````

_سلول کد 1:_

```python
import numpy as np
from triage import (choose_threshold, confusion, ece, fit_temperature, load_tickets, predict, random_split, scores,
                    selective, split, train)

tickets = load_tickets()
tr, dev, test = split(tickets)
print(len(tickets), "tickets:", len(tr), "train /", len(dev), "dev /", len(test), "test")
overlap = {t["template"] for t in tr} & {t["template"] for t in test}
print("templates shared by train and test:", len(overlap))
```

تقسیم بر اساس قالب جمله: هیچ قالبی هم در train و هم در test نیست. یعنی آزمون واقعاً روی جمله‌بندی‌های تازه است، مثل مشتری‌های واقعی.

**باید ببینی:**

```
240 tickets: 132 train / 48 dev / 60 test
templates shared by train and test: 0
```

_سلول متنی (Markdown):_

````markdown
## Leakage: the same model with a naive random split
````

_سلول کد 2:_

```python
leaky = random_split(tickets)
print("random split (leaky):", scores(leaky[2], predict(train(leaky[0]), leaky[2])[0]))
model = train(tr)
print("split by template:   ", scores(test, predict(model, test)[0]))
```

تقسیم تصادفی نتیجه را ۱.۰ نشان می‌دهد، چون جمله‌های تقریباً یکسان در هر دو طرف هستند. تقسیم درست، دقت واقعی را نشان می‌دهد. این یکی از رایج‌ترین اشتباه‌ها در پروژه‌های طبقه‌بندی است.

**باید ببینی:**

```
random split (leaky): {'accuracy': 1.0, 'macro_f1': 1.0}
split by template:    {'accuracy': 0.733, 'macro_f1': 0.661}
```

_سلول متنی (Markdown):_

````markdown
## Where does it go wrong? (test confusion matrix)
````

_سلول کد 3:_

```python
classes = list(model.classes_)
labels, _ = predict(model, test)
cm = confusion(test, labels, classes)
print(" " * 15 + " ".join(f"{c[:7]:>7s}" for c in classes))
for c, row in zip(classes, cm):
    print(f"{c:15s}" + " ".join(f"{v:7d}" for v in row))
```

سطرها برچسب واقعی، ستون‌ها پیش‌بینی. عددهای خارج قطر اشتباه‌ها هستند.

**باید ببینی:**

```
               account cancel_ damaged invoice  refund shippin
account_access      12       0       0       0       0       0
cancel_order         0       8       0       0       0       0
damaged_item         0       0       0       0       0       0
invoice              0       0       0      12       0       0
refund               0       0       1       0      11       0
shipping_delay       0       0      12       0       3       1
```

_سلول متنی (Markdown):_

````markdown
## Are the confidences honest? (calibration)
Temperature scaling: one number fitted on dev that makes probabilities match reality better.
````

_سلول کد 4:_

```python
T = fit_temperature(model, dev)
y_dev = np.array([t["label"] for t in dev])
for temp in (1.0, T):
    lab, conf = predict(model, dev, temp)
    print(f"temperature {temp:.2f}: ECE {ece(lab == y_dev, conf):.3f}, mean confidence {conf.mean():.2f}, accuracy {np.mean(lab == y_dev):.2f}")
```

ECE فاصله‌ی اطمینان مدل با دقت واقعی است؛ کمتر بهتر. temperature روی dev پیدا می‌شود، هرگز روی test.

**باید ببینی:**

```
temperature 1.00: ECE 0.249, mean confidence 0.57, accuracy 0.79
temperature 0.70: ECE 0.202, mean confidence 0.70, accuracy 0.79
```

_سلول متنی (Markdown):_

````markdown
## The most confident mistakes
````

_سلول کد 5:_

```python
lab, conf = predict(model, dev, T)
wrong = [i for i in np.argsort(-conf) if lab[i] != y_dev[i]][:4]
for i in wrong:
    print(f"{conf[i]:.2f}  predicted {lab[i]:15s} true {y_dev[i]:15s} | {dev[i]['text']}")
```

مهم‌ترین درس این پروژه: مدل با اطمینان ۰.۹۶ «delivery is delayed» را damaged_item می‌داند! n-gram های حرفی «delayed» و «damaged» را شبیه می‌بینند. آستانه‌ی اطمینان به‌تنهایی جلوی این را نمی‌گیرد؛ داده‌ی متنوع‌تر یا مدل بهتر لازم است.

**باید ببینی:**

```
0.96  predicted damaged_item    true shipping_delay  | the mirror delivery is delayed again
0.93  predicted damaged_item    true shipping_delay  | the chair delivery is delayed again
0.93  predicted damaged_item    true shipping_delay  | the chair delivery is delayed again
0.82  predicted damaged_item    true shipping_delay  | the sofa delivery is delayed again
```

_سلول متنی (Markdown):_

````markdown
## Human fallback: coverage at a target accuracy
The threshold is chosen on dev for each target accuracy, then applied unchanged to test.
````

_سلول کد 6:_

```python
import json, os

lab_d, conf_d = predict(model, dev, T)
lab_t, conf_t = predict(model, test, T)
y_test = np.array([t["label"] for t in test])
rows = {}
for target in (0.8, 0.9):
    th = choose_threshold(lab_d == y_dev, conf_d, target)
    rows[str(target)] = {"dev": selective(lab_d == y_dev, conf_d, th), "test": selective(lab_t == y_test, conf_t, th)}
    print(f"target {target}: dev {rows[str(target)]['dev']}\n             test {rows[str(target)]['test']}")
os.makedirs("results", exist_ok=True)
with open("results/results.json", "w") as f:
    json.dump({"test": scores(test, lab_t), "leaky_random_split": scores(leaky[2], predict(train(leaky[0]), leaky[2])[0]),
               "temperature": T, "routing": rows}, f, indent=2)
```

با هدف ۰.۸، تقریباً همه‌ی تیکت‌ها خودکار می‌روند. با هدف ۰.۹ هیچ آستانه‌ای کافی نیست (به خاطر همان اشتباه‌های مطمئن) و همه به انسان می‌روند. این جواب درست و امن است: سیستم وقتی مطمئن نیست، خودکار کار نمی‌کند.

**باید ببینی:**

```
target 0.8: dev {'threshold': 0.44, 'coverage': 0.979, 'accuracy_automated': 0.809, 'to_human': 1}
             test {'threshold': 0.44, 'coverage': 0.85, 'accuracy_automated': 0.843, 'to_human': 9}
target 0.9: dev {'threshold': 1.01, 'coverage': 0.0, 'accuracy_automated': None, 'to_human': 48}
             test {'threshold': 1.01, 'coverage': 0.0, 'accuracy_automated': None, 'to_human': 60}
```

_سلول متنی (Markdown):_

````markdown
## A language model, zero-shot (optional)
Set `TRIAGE_PROVIDER` to `ollama`, `anthropic` or `opencode` before starting the notebook.
````

_سلول کد 7:_

```python
import os
from triage import llm_classifier

if os.environ.get("TRIAGE_PROVIDER"):
    classify = llm_classifier(classes)
    llm_labels = [classify(t["text"]) for t in test]
    print("LLM zero-shot:", scores(test, llm_labels))
else:
    print("No model set: TRIAGE_PROVIDER = ollama | anthropic | opencode (see the guide)")
```

مدل زبانی بدون آموزش معنی «delayed» و «damaged» را می‌فهمد ولی کندتر و (ابری) پولی است. با عدد مقایسه کن.

**باید ببینی:**

```
No model set: TRIAGE_PROVIDER = ollama | anthropic | opencode (see the guide)
```

> **نکته:** اگر نمی‌خواهی سلول‌ها را یکی‌یکی بسازی: دکمه‌ی **دانلود notebook** بالای سلول‌ها فایل آماده را می‌دهد؛ در پوشه‌ی repo بگذار و Run All. ولی یک بار دستی ساختن، کد را بهتر در ذهنت می‌نشاند.

## 11. مقایسه با مدل زبانی (اختیاری)
_VS Code · Ollama / Claude / OpenCode · حدود 10 دقیقه_

**چرا:** مدل زبانی بدون آموزش معنا را می‌فهمد (delayed با damaged فرق دارد) ولی کندتر و برای ابری پولی است. با عدد مقایسه کن.

1. یکی از سه راه را در ترمینال VS Code اجرا کن، kernel را **Restart** و سلول آخر notebook را اجرا کن.

_Ollama (محلی، رایگان)_

```
ollama pull qwen2.5:7b
pip install ollama
$env:TRIAGE_PROVIDER = "ollama"
```

_Claude (کلید API؛ اشتراک Claude.ai کلید API نیست)_

```
pip install anthropic
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:TRIAGE_PROVIDER = "anthropic"
```

_OpenCode_

```
opencode models
$env:TRIAGE_PROVIDER = "opencode"
```

> **حواست باشد:** کلید API را در notebook یا فایل‌های repo ننویس. تیکت واقعی مشتری را بدون اجازه به مدل ابری نفرست.

## 12. commit و push از VS Code
_VS Code · GitHub · حدود 3 دقیقه_

**چرا:** notebook با خروجی‌هایش و فایل نتایج باید در GitHub باشند تا بدون اجرا دیده شوند.

1. پنل Source Control: `Ctrl+Shift+G`. فایل‌های `01_ticket_triage.ipynb` و `results/results.json` را می‌بینی.
2. پیام: `Add notebook: leakage, calibration and human fallback` → **Commit** → **Sync Changes**.

> **باید ببینی:** در GitHub، `01_ticket_triage.ipynb` را باز کن: جدول‌ها و خروجی‌ها بدون اجرا دیده می‌شوند. تب Actions دوباره سبز است.

> **حواست باشد:** قانون ساده: قبل از هر کار در VS Code اول **Pull** بزن، و یک فایل را هم‌زمان در GitHub و VS Code ویرایش نکن.

## 13. README نهایی
_GitHub · حدود 10 دقیقه_

**چرا:** README صفحه‌ی اول پروژه است: در ۳۰ ثانیه بگوید چه مسئله‌ای، چه روشی، چه عددی و چه محدودیتی. عددها را از `results/results.json` خودت بردار، نه از این صفحه.

1. در GitHub روی `README.md` → آیکون مداد → متن زیر را جایگزین کن و عددهای `{...}` را پر کن (یا results.json را پایین paste کن). commit: `Write README`.
2. نام کاربری‌ات را در خط badge جایگزین کن.

````markdown
# Support-ticket triage with a human fallback

![tests](https://github.com/<your-user>/ticket_triage/actions/workflows/tests.yml/badge.svg)

Routes support tickets to 6 intents with TF-IDF (word + character n-grams) and logistic regression, and automates a
ticket only when the calibrated confidence reaches a threshold chosen on dev for a target accuracy; the rest goes to a
human.

## Results (`results/results.json`)
| | accuracy | macro-F1 |
|---|---|---|
| test, split by wording template (honest) | {acc} | {f1} |
| random split (leaky, for comparison) | {leaky_acc} | {leaky_f1} |

Human fallback on test (threshold chosen on dev for 80% target accuracy): coverage {cov80}, accuracy of automated tickets {acc80}.

## What I learned
- A random split looked perfect ({leaky_acc}) because near-identical tickets were on both sides; splitting by template shows the real accuracy.
- The model was most confident on some of its mistakes ("delivery is delayed" → damaged item, from similar character
  n-grams), so a confidence threshold alone cannot reach 90% here: everything goes to a human, which is the safe answer.

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_ticket_triage.ipynb` and run all cells. Optional zero-shot LLM: `TRIAGE_PROVIDER=ollama|anthropic|opencode`.

## Limitations
- Synthetic tickets from 60 templates; real tickets are longer, multilingual and mix intents.
- Temperature and thresholds are fitted on 48 dev tickets.

## Licence
MIT
````

## 14. صیقل نهایی repo
_GitHub · حدود 5 دقیقه_

**چرا:** جزئیات کوچکی که repo را حرفه‌ای نشان می‌دهد.

1. صفحه‌ی repo → چرخ‌دنده‌ی **About** → Topics: `text-classification`, `calibration`, `scikit-learn`, `mlops`, `python`.
2. در پروفایل GitHub: **Customize your pins** → این repo را pin کن.
3. خط رزومه‌ی پایین را با عددهای خودت بردار.

**خط رزومه:** Built a support-ticket triage model (TF-IDF + logistic regression) with a leakage-free split by wording template (accuracy {acc} vs a misleading {leaky_acc} on a random split), temperature calibration, and a dev-tuned confidence threshold that automates {cov80} of test tickets at {acc80} accuracy and sends the rest to a human.

## اگر به خطا خوردی
- **`No module named triage` در notebook**: notebook باید کنار `triage.py` باشد و kernel روی `.venv`.
- **عددهای من کمی فرق دارد**: نسخه‌ی scikit-learn می‌تواند عددها را کمی جابه‌جا کند؛ نتیجه‌ی کلی (نشت، اشتباه مطمئن) باید همان باشد.
- **`python` شناخته نمی‌شود**: Python را با تیک «Add to PATH» نصب کن، یا به‌جای `python` بنویس `py`.
- **تب Actions قرمز است**: روی اجرای قرمز کلیک کن؛ معمولاً یک فایل با نام یا مسیر اشتباه ساخته شده (مثلاً `test/` به‌جای `tests/`).

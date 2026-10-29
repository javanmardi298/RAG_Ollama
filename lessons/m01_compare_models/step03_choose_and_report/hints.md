## Hint 1
هر دو تابع فقط فیلتر، مرتب‌سازی و فرمت‌اند. اول `choose`: یک لیست فیلترشده، بعد `min` با یک کلید چندبخشی.

## Hint 2
کلید `min`: `(latency, -accuracy, model)` یعنی اول کم‌تأخیر، بعد دقت بیشتر، بعد نام. برای جدول: `sorted(rows, key=lambda r: (-r["accuracy"], r["model"]))` و f-string با `:.2f`.

## Hint 3
`None` را قبل از مقایسه حذف کن (در شرط فیلتر). `"-" if r["mean_latency_s"] is None else f"{...:.2f}"`. حل کامل: `python -m learn solution m01_compare_models 3`.

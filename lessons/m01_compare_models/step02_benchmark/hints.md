## Hint 1
سه حلقه‌ی تودرتو (مدل، مورد، تکرار) و برای هر فراخوانی یک `try/except`. شمارنده‌ها را برای هر مدل از صفر شروع کن.

## Hint 2
`start = time.perf_counter()` قبل از `llm.chat(...)`; بعد از موفقیت `times.append(time.perf_counter() - start)`. در `except Exception:` فقط `errors += 1; continue` (پس درست‌ها اضافه نمی‌شود). `n` را قبل از `try` زیاد کن تا خطا هم شمرده شود.

## Hint 3
`accuracy = correct / n if n else 0.0`، `mean_latency_s = sum(times) / len(times) if times else None`. حل کامل: `python -m learn solution m01_compare_models 2`.

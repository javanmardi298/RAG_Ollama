## Hint 1
ترتیب بررسی را مثل جدول درس بنویس: اول ارائه‌دهنده، بعد مدل، بعد شرط‌های ویژه‌ی هر ارائه‌دهنده، بعد بودجه. هر شرط یک `if` با `raise ValueError(...)`.

## Hint 2
`float(...)` خودش `ValueError` می‌دهد ولی با پیام نامفهوم؛ آن را در `try/except ValueError` بگیر و پیام خودت را بالا بیاور. `env.get("X") or default` مقدار خالی را هم پیش‌فرض می‌کند.

## Hint 3
پیام‌ها باید کلمه‌های کلیدی تست را داشته باشند: `unknown provider`، `provider/model`، `LEARN_API_BASE`، `ANTHROPIC_API_KEY`، `number`، `negative`. حل کامل: `python -m learn solution m01_compare_models 1`.

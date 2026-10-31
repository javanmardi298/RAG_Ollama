## Hint 1
اول نرمال‌سازی (یک خط)، بعد سه شرط به ترتیب: سلام/حساب، چندمرحله‌ای، پیش‌فرض.

## Hint 2
`q = question.strip().lower().rstrip("!.? ").strip()`. حساب: `re.fullmatch(r"[\d\s+\-*/().]+", q)`. کلمه‌های پرسشی: `sum(w in QWORDS for w in re.findall(r"[a-z]+", q)) >= 2`.

## Hint 3
شرط چندمرحله‌ای: `" and " in f" {q} " and sum(...) >= 2`. ترتیب مهم است: `direct` اول. حل کامل: `python -m learn solution p22_agentic_rag 1`.

## Hint 1
`content_words` = «کلمه‌های پرمعنا» به شکل یک set. `grade` = «چند تا از کلمه‌های سؤال در تکه هم هست؟» و مقایسه با آستانه.

## Hint 2
`re.findall(r"[a-z0-9]+", text.lower())`، فیلتر `not in STOP`، و برای جمع: `w[:-1] if len(w) > 3 and w.endswith("s") else w`. در `grade` از `&` بین دو set استفاده کن و نسبت `len(q & c) / len(q)`.

## Hint 3
`q = content_words(expand(question))`؛ `if not q: return False`؛ `c = content_words(chunk["heading"] + " " + chunk["text"])`؛ `return len(q & c) / len(q) >= min_ratio`. حل کامل: `python -m learn solution p22_agentic_rag 2`.

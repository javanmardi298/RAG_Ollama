## Hint 1
بخش‌ها مستقل‌اند: اول `tokenize`، بعد شمارش (`Counter`)، بعد idf، بعد امتیاز یک کلمه برای یک سند، و در آخر جمع روی کلمه‌های query. هر بخش را جدا با `print` امتحان کن.

## Hint 2
برای `df`: `Counter(w for t in toks for w in set(t))`. برای `avg`: `sum(len) / n`. در `scores` یک حلقه روی `tokenize(query)` و داخلش حلقه روی سندها؛ اگر `tf == 0` رد شو. برای `search` سندها را با `key=lambda i: (-s[i], i)` مرتب کن و `s[i] > 0` را فیلتر کن.

## Hint 3
`idf = math.log(1 + (n - df + 0.5) / (df + 0.5))`؛ `score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len_i / avg))`. اگر هنوز گیر کردی: `python -m learn solution p01_faq_search 2`.

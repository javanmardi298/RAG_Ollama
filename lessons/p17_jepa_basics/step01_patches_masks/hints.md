## Hint 1
`patchify` یک reshape و یک transpose است و بس. روی کاغذ یک شبکه‌ی ۸×۸ بکش و بنویس patch شماره‌ی ۰ چه خانه‌هایی دارد؛ تست هم همین را می‌پرسد.

## Hint 2
`img.reshape(4, 2, 4, 2)`: محورها = (سطر-patch، سطر-داخل، ستون-patch، ستون-داخل). برای اینکه هر patch چهار پیکسل پشت‌هم داشته باشد، دو محور وسط را جابه‌جا کن: `.transpose(0, 2, 1, 3)`. ماسک: `rng.integers(0, GRID - block + 1, size=2)` دو عدد (r, c) می‌دهد.

## Hint 3
`keep = np.ones((4, 4), bool); r, c = rng.integers(0, 4 - block + 1, size=2); keep[r:r+block, c:c+block] = False; return keep.reshape(-1)`. حل کامل: `python -m learn solution p17_jepa_basics 1`.

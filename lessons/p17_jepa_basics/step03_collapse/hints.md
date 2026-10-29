## Hint 1
دو عدد مستقل‌اند: (۱) پراکندگی بین نمونه‌ها، (۲) رتبه‌ی مؤثر از روی مقدارهای تکین. `diagnose` فقط سه شرط if است.

## Hint 2
`z.std(axis=0).mean()`. برای رتبه: `s = np.linalg.svd(z - z.mean(axis=0), compute_uv=False)`; `p = s / s.sum()`; `np.exp(-(p * np.log(p)).sum())`. حالت `s.sum() == 0` را جدا مدیریت کن (رتبه ۰).

## Hint 3
`p = np.clip(s / total, 1e-12, None)` از `log(0)` جلوگیری می‌کند. ترتیب شرط‌ها در `diagnose` مهم است: collapsed اول. حل کامل: `python -m learn solution p17_jepa_basics 3`.

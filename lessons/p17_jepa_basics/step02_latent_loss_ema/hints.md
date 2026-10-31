## Hint 1
loss: «فقط جاهایی که پنهان‌اند». در PyTorch با ماسک بولی می‌توانی مستقیم اندیس بزنی: `pred[mask]`. EMA: یک حلقه روی جفت پارامترها.

## Hint 2
`hidden = ~keep` (شکل `(B, N)`) و `pred[hidden]` شکل `(تعداد_پنهان, D)` می‌دهد. برای حالت بدون patch پنهان `pred.sum() * 0.0` یک صفر قابل‌مشتق می‌دهد. EMA: `p_t.mul_(m).add_(p_s, alpha=1 - m)` درجا است.

## Hint 3
تابع `ema_update` باید `@torch.no_grad()` داشته باشد (در starter هست). حل کامل: `python -m learn solution p17_jepa_basics 2`.

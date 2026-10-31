## Hint 1
`summarize` = گروه‌بندی با دیکشنری. `verdict` = چهار تصمیم مستقل از روی خلاصه. هر تصمیم را جدا بنویس.

## Hint 2
گروه‌بندی: `groups.setdefault(r["run"], []).append(r["probe"])`. در `verdict` اول `learned = {k: v for k, v in summary.items() if k not in BASELINES}`؛ بهترین: `max(learned, key=lambda k: learned[k]["mean"])`.

## Hint 3
`pixels_win = "raw_pixels" in summary and best is not None and summary["raw_pixels"]["mean"] >= learned[best]["mean"]`. `beats_random`: فقط اگر `rand` وجود دارد. ترتیب لیست‌ها همان ترتیب درج در summary است. حل کامل: `python -m learn solution p17_jepa_basics 4`.

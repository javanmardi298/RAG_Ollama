## Hint 1
سه تکه‌ی کوچک: (۱) verify = زیرمجموعه بودن دو set. (۲) run_agent = یک نردبان از شرط‌ها: direct؟ شاهد دارد؟ ارجاع معتبر دارد؟ verify می‌شود؟ هر شرطی که نیفتاد = امتناع. (۳) report = شمارش.

## Hint 2
verify: `words = cw(re.sub(r"\[[^\]]*\]", " ", answer))` (ارجاع‌ها را حذف کن)، و `words <= cw(" ".join(c["text"] for c in chunks))`. در `run_agent` یک دیکشنری `abstain` از همان اول بساز تا چند بار تکرار نشود.

## Hint 3
ارجاع معتبر: `ids = {c["id"] for c in found["chunks"]}; cites = [c for c in cites if c in ids]`. report: حلقه روی `zip(outcomes, questions)` و `if/elif` روی `q["answerable"]`. حل کامل: `python -m learn solution p22_agentic_rag 4`.

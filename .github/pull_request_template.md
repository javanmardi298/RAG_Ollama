## What changed

## If this adds or changes a lesson step
- [ ] `lesson.md` has: goal, prerequisites, concept (why), line-by-line code explanation, how to run, expected output, "if it differs", pitfalls, next step
- [ ] `starter.py` fails its check, `solution.py` passes (`python -m learn selftest <lesson>`)
- [ ] `hints.md` has three levels, `quiz.yaml` has at least three questions with `why`
- [ ] no real data, no keys; data is synthetic or has its licence stated
- [ ] `python -m learn build` and `python -m learn notebook <lesson>` were run and committed
- [ ] `ruff check lessons src` and `pytest -q` pass

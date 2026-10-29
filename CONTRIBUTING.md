# Contributing

This repository is both a project and a set of step-by-step lessons (`lessons/`). Fixes to wrong or unclear lessons are the most useful contribution.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-panel.txt && pip install -e .
pip install -r requirements-jepa.txt                       # only for the JEPA lessons
```
Full instructions (Ollama, Claude API key, OpenCode, Windows): `lessons/00_setup/README.md`.

## Before you push
```bash
ruff check src scripts app tests lessons
python -m learn selftest          # solutions pass, starters fail, links resolve
python -m learn build             # regenerate lessons/README.md
python -m learn notebook <lesson> # regenerate the notebook of a lesson you changed
pytest -q
```
CI (`.github/workflows/`) runs the same checks.

## Adding a lesson step
Create `lessons/<lesson>/stepNN_name/` with `lesson.md`, `starter.py`, `solution.py`, `check.py`, `hints.md`, `quiz.yaml`.
- `check.py`: functions `check_*(m)` that raise `AssertionError("what was wrong")`; the docstring is the label shown to the learner.
  Optional `REQUIRES = ["torch"]` skips the step when a package is missing. Checks must not need a model or network: pass a fake `llm`.
- `starter.py`: the same function signatures with `raise NotImplementedError("TODO n: ...")` and comments that say what to do.
- `hints.md`: `## Hint 1` (nudge), `## Hint 2` (direction), `## Hint 3` (almost the answer).
- `lesson.md` is written to teach, not to summarise (see the template list in the pull request checklist).

## Rules
- Never commit API keys, `.env`, or real customer data. `work/` (learner answers) is ignored on purpose.
- Lesson datasets are small and synthetic, or their licence is stated in the lesson.
- Keep the lesson text honest: if a technique does not beat the baseline in the exercise, say so (see `p17_jepa_basics`, step 4).

## Licence
Add the licences you choose for the code and for the lesson text here (suggestion: MIT for code, CC BY 4.0 for text).

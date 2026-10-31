# Agent Skills: team procedures as SKILL.md folders

![tests](https://github.com/<your-user>/agent_skills/actions/workflows/tests.yml/badge.svg)

Three skills for coding agents (Claude Code, the Claude Agent SDK and other tools that read `SKILL.md`):

| skill | what it does |
|---|---|
| `project-report` | turns `results/*.json` into a status report (script: `summarize.py`) |
| `invoice-check` | checks invoice fields, totals and dates; masks the IBAN (script: `validate_invoice.py`) |
| `meeting-notes` | decisions, action items with owner and due date, open questions |

Plus a small toolkit (`skills_kit.py`) that validates the skills, measures their context cost and tests activation.

## Results (`results/results.json`)
- Validation problems: none
- Context: {always} tokens always loaded vs {all} if every skill body were in the prompt (progressive disclosure)
- Activation test (keyword proxy): {correct}/{total}

## Use the skills
Copy a skill folder to `~/.claude/skills/` (personal) or `<repo>/.claude/skills/` (project) for Claude Code, then ask
for something its description covers.

## Run the checks
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```

## Licence
MIT

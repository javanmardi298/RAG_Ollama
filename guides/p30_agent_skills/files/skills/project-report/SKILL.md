---
name: project-report
description: Summarise a project's latest results (results/*.json) into a short status report with numbers, gaps and next steps. Use when the user asks how a project is doing, for a status report, or what to do next.
---

# Project report

1. Run `python scripts/summarize.py <project folder>`; it prints every `results/*.json` as compact key numbers.
2. Write the report in this order: the headline metric, what changed since the last run, the weakest part, at most three next steps.
3. Never invent a number. If a results file is missing, say which step has not run yet.

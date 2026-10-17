---
name: project-report
description: Summarise this project's latest results (results/*.json) into a short report with numbers, gaps and next steps. Use when the user asks how the project is doing, for a status report, or what to do next.
---

# Project report

1. Run `python scripts/summarize.py` from this skill's folder; it prints every results/*.json file as compact key numbers.
2. Write the report in this order: headline metric with its confidence interval, what changed since the last run,
   the weakest stage, and at most three next steps.
3. Never invent a number: if a file is missing, say which stage has not run.

---
name: run-stage
description: Run one stage of the support-agent project through the control panel's allow-listed tasks and read its result. Use when the user asks to run, re-run or check a stage (data, intents, RAG, thresholds, red-team, evaluation).
---

# Run a stage

Use the panel's MCP tools (`run_task`, `run_status`, `get_results`); never run arbitrary shell commands.
Before a slow stage (6, 9) say how long it usually takes and ask. After it finishes, report the key metric and
compare it with the previous run (`compare_runs`).

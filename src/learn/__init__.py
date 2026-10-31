"""learn: step-by-step lessons with code, automatic checks, hints, quizzes and a teacher mode (see lessons/README.md).

    api.py       list lessons, show a step, run its check, give hints, record progress (used by the CLI and by the panel / MCP tools)
    _runner.py   runs one check.py against the student's file in a separate process (timeout, readable errors)
    llm.py       the model lessons use: offline by default (no setup), ollama / anthropic / opencode / openai_compatible on request
    notebooks.py one Jupyter notebook per lesson (Colab / Codespaces)
    build.py     regenerate lessons/README.md and the skeleton lessons from presets/projects/*.yaml
    __main__.py  python -m learn ...
"""

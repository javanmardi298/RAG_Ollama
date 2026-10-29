"""One .ipynb per lesson: for every step the lesson text (markdown cells), the starter (code cell) and a check cell.

Works in Jupyter, VS Code and Colab. The first cell clones the repository and installs it when running in Colab.
"""
from __future__ import annotations

import json
import re

import yaml

from support.config import ROOT

from . import api

CONF = ROOT / "lessons" / "learn.yaml"


def _conf() -> dict:
    return yaml.safe_load(CONF.read_text(encoding="utf-8")) if CONF.exists() else {}


def _md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def _code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text.splitlines(keepends=True)}


def build(lesson: str) -> dict:
    c = _conf()
    repo, branch = c.get("repo", "OWNER/REPO"), c.get("branch", "main")
    badge = f"https://colab.research.google.com/github/{repo}/blob/{branch}/lessons/{lesson}/{lesson}.ipynb"
    cells = [_md(f"# {lesson}\n\n[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({badge})\n\n"
                 "Run the cells in order. In each step: read, complete the TODOs in the code cell, run it, then run the check cell."),
             _code("# Setup (Colab: clones the repo; locally: skip if you are already inside it)\n"
                   "import os, sys, subprocess\n"
                   "if 'google.colab' in sys.modules and not os.path.exists('repo'):\n"
                   f"    subprocess.run(['git', 'clone', '--depth', '1', '-b', '{branch}', 'https://github.com/{repo}.git', 'repo'], check=True)\n"
                   "    subprocess.run([sys.executable, '-m', 'pip', '-q', 'install', '-r', 'repo/requirements.txt', '-e', 'repo'], check=True)\n"
                   "if os.path.exists('repo'): os.chdir('repo')\n"
                   "os.environ.setdefault('LEARN_PROVIDER', 'offline')   # offline | ollama | anthropic | opencode | openai_compatible\n")]
    for s in api.steps(lesson):
        sd = api.LESSONS / lesson / s
        text = (sd / "lesson.md").read_text(encoding="utf-8")
        cells.append(_md(re.sub(r"\]\((?!https?:|#)[^)]*\)", "](#)", text)))        # relative links do not work inside a notebook
        cells.append(_code((sd / "starter.py").read_text(encoding="utf-8")))
        cells.append(_code("from learn.notebook import check_cell\n" f"check_cell({lesson!r}, {s!r}, globals())"))
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                         "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}


def write(lesson: str) -> str:
    path = ROOT / "lessons" / lesson / f"{lesson}.ipynb"
    path.write_text(json.dumps(build(lesson), ensure_ascii=False, indent=1), encoding="utf-8")
    return str(path.relative_to(ROOT))

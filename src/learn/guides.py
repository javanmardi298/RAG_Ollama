"""Build guides: step-by-step pages to rebuild a project in YOUR OWN GitHub repo (copy each file, create the notebook,
run it, commit). One source per project in guides/<id>/:

    guide.yaml          the steps (where you work, why, what to do, which file or notebook, what you should see)
    files/              the real project files the learner copies (tested here)
    notebook.yaml       the notebook cells (markdown / code, a note, and a regular expression the output must match)
    README.template.md  the final README with {placeholders} for the learner's own numbers
    outputs.json        real outputs captured by `verify` (shown as "you should see" in the page)

python -m learn.guides verify [id]     run every file and the notebook in a clean folder, check the outputs, save outputs.json
python -m learn.guides build           guides/<id>/GUIDE.md (the same guide as a markdown page on GitHub)
python -m learn.guides html out.html   the page (published as a claude.ai artifact)
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from support.config import ROOT

GUIDES = ROOT / "guides"
TEMPLATE = Path(__file__).parent / "guide_template.html"


def ids() -> list[str]:
    return sorted(p.name for p in GUIDES.iterdir() if (p / "guide.yaml").exists())


def load(gid: str) -> dict:
    d = GUIDES / gid
    g = yaml.safe_load((d / "guide.yaml").read_text(encoding="utf-8"))
    g["notebook"] = yaml.safe_load((d / "notebook.yaml").read_text(encoding="utf-8")) if (d / "notebook.yaml").exists() else None
    g["readme"] = (d / "README.template.md").read_text(encoding="utf-8") if (d / "README.template.md").exists() else ""
    g["outputs"] = json.loads((d / "outputs.json").read_text(encoding="utf-8")) if (d / "outputs.json").exists() else {}
    for s in g["steps"]:
        if s.get("file"):
            s["content"] = (d / "files" / s["file"]).read_text(encoding="utf-8")
    return g


def notebook(gid: str) -> dict:
    nb = load(gid)["notebook"]

    def cell(c):
        if "md" in c:
            return {"cell_type": "markdown", "metadata": {}, "source": c["md"].strip().splitlines(keepends=True)}
        return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c["code"].strip().splitlines(keepends=True)}
    return {"cells": [cell(c) for c in nb["cells"]], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}


def _run(cmd: list[str], cwd: Path) -> str:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=600)
    if p.returncode:
        raise AssertionError(f"{' '.join(cmd)} failed:\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}")
    return p.stdout


def verify(gid: str, save: bool = True) -> dict:
    """Rebuild the project exactly as the learner would (only the copied files) and run it end to end."""
    import nbclient
    import nbformat
    g = load(gid)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / g["repo"]
        shutil.copytree(GUIDES / gid / "files", work)
        out = {"check_setup": _run([sys.executable, "check_setup.py"], work),
               "pytest": re.sub(r" in [\d.]+s", "", _run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], work)).strip()}
        out["check_setup"] = re.sub(r"Python \d+\.\d+\.\d+", "Python 3.x.y", out["check_setup"])
        nb = nbformat.reads(json.dumps(notebook(gid)), as_version=4)
        nbclient.NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(work)}}).execute()
        cells, problems = [], []
        for spec, c in zip(g["notebook"]["cells"], nb.cells):
            if "code" not in spec:
                continue
            text = "".join(o.get("text", "") for o in c.outputs if o.get("output_type") == "stream")
            text += "".join(o.get("data", {}).get("text/plain", "") for o in c.outputs if o.get("output_type") in ("execute_result", "display_data"))
            errs = [o for o in c.outputs if o.get("output_type") == "error"]
            if errs:
                problems.append(f"cell {len(cells) + 1}: {errs[0]['ename']}: {errs[0]['evalue']}")
            if spec.get("expect") and not re.search(spec["expect"], text):
                problems.append(f"cell {len(cells) + 1}: output does not match {spec['expect']!r}:\n{text[:400]}")
            cells.append(text.rstrip())
        out["cells"] = cells
        res = work / "results" / "results.json"
        out["results"] = json.loads(res.read_text()) if res.exists() else None
    if problems:
        raise AssertionError("\n".join(problems))
    if save:
        (GUIDES / gid / "outputs.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def _lessons_used(guides: list[dict]) -> dict:
    """Texts of every lesson a guide links to (explain refs and lesson: links), so the page can show them in place."""
    names = set()
    for g in guides:
        names |= {t.split(":", 1)[1] for _, t in g.get("learn", []) if t.startswith("lesson:")}
        for s in g["steps"]:
            names |= {e[2].split("/")[0] for e in s.get("explain", []) if len(e) > 2 and e[2]}
    out = {}
    for name in sorted(names):
        d = ROOT / "lessons" / name
        steps = sorted(p for p in d.iterdir() if p.is_dir() and (p / "lesson.md").exists())
        out[name] = {"title": (d / "README.md").read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip(),
                     "steps": {p.name: (p / "lesson.md").read_text(encoding="utf-8") for p in steps}}
    return out


def export() -> dict:
    out = []
    for gid in ids():
        g = load(gid)
        g["notebook_json"] = notebook(gid) if g["notebook"] else None
        out.append(g)
    conf = yaml.safe_load((ROOT / "lessons" / "learn.yaml").read_text(encoding="utf-8"))
    return {"guides": out, "lessons": _lessons_used(out),
            "links": {"roadmap_url": conf.get("roadmap_url", ""), "guides_url": conf.get("guides_url", "")}}


WHERE = {"gh": "GitHub", "vs": "VS Code", "co": "Colab", "ol": "Ollama / Claude / OpenCode"}


def _md_link(label: str, target: str) -> str:
    kind, _, arg = target.partition(":")
    if kind == "lesson":
        return f"[{label}](../../lessons/{arg}/README.md)"
    if kind == "guide":
        return f"[{label}](../{arg}/GUIDE.md)"
    if kind == "roadmap":
        return f"{label} (نقشه‌ی راه، پروژه‌ی `{arg}`)"
    if kind == "roadmap-tab":
        return f"[{label}](../../docs/{'jepa' if arg == 'jepa' else 'research_2026'}.md)"
    return f"[{label}]({arg})"


def markdown(gid: str) -> str:
    """The same guide as a markdown page for GitHub (guides/<id>/GUIDE.md)."""
    g = load(gid)
    o = g.get("outputs", {})
    L = [f"# {g['title']}", "", g["lede"], "", "> نسخه‌ی تعاملی (تیک مراحل، مقایسه‌ی خروجی، پرسیدن از Claude، دانلود notebook): صفحه‌ی «راهنمای ساخت پروژه‌ها» (claude.ai artifact).", ""]
    if g.get("learn"):
        L += ["**برای فهمیدن بهتر:** " + " · ".join(_md_link(label, t) for label, t in g["learn"]), ""]
    L += ["## مراحل", *[f"{i}. {s['title']}" for i, s in enumerate(g["steps"], 1)], ""]
    for i, s in enumerate(g["steps"], 1):
        L += [f"## {i}. {s['title']}", f"_{' · '.join(WHERE.get(w, w) for w in s.get('where', []))}{' · حدود ' + str(s['minutes']) + ' دقیقه' if s.get('minutes') else ''}_", ""]
        if s.get("why"):
            L += [f"**چرا:** {s['why']}", ""]
        if s.get("pre"):
            L += [s["pre"], ""]
        L += [f"{k}. {d.replace('{description}', g['description'])}" for k, d in enumerate(s.get("do", []), 1)] + [""]
        if s.get("file"):
            lang = "python" if s["file"].endswith(".py") else ("json" if s["file"].endswith(".json") else "")
            L += [f"`{s['file']}`", "", f"````{lang}", s["content"].rstrip(), "````", ""]
        if s.get("note"):
            L += [s["note"], ""]
        if s.get("explain"):
            L += ["<details><summary><b>درک کد: تابع به تابع</b></summary>", ""]
            for e in s["explain"]:
                ref = f" ([درس]({'../../lessons/' + e[2] + '/lesson.md'}))" if len(e) > 2 and e[2] else ""
                L += [f"- **`{e[0]}`**: {e[1]}{ref}"]
            L += ["", "</details>", ""]
        for c in s.get("commands", []):
            L += [f"_{c['label']}_", "", "```", c["code"].rstrip(), "```", ""]
            if c.get("output"):
                L += ["**باید ببینی:**", "", "```", "\n".join(o.get(k, "") for k in c["output"]).strip(), "```", ""]
        if s.get("notebook") and g["notebook"]:
            outs, k, n = o.get("cells", []), 0, 0
            for c in g["notebook"]["cells"]:
                if "md" in c:
                    L += ["_سلول متنی (Markdown):_", "", "````markdown", c["md"].rstrip(), "````", ""]
                    continue
                n += 1
                L += [f"_سلول کد {n}:_", "", "```python", c["code"].rstrip(), "```", ""]
                if c.get("note"):
                    L += [c["note"], ""]
                if k < len(outs) and outs[k]:
                    L += ["**باید ببینی:**", "", "```", outs[k], "```", ""]
                k += 1
        if s.get("readme"):
            L += ["````markdown", g["readme"].rstrip(), "````", ""]
        if s.get("cv"):
            L += [f"**خط رزومه:** {s['cv']}", ""]
        for key, label in (("tip", "نکته"), ("see", "باید ببینی"), ("warn", "حواست باشد")):
            if s.get(key):
                L += [f"> **{label}:** {s[key]}", ""]
    L += ["## اگر به خطا خوردی", *[f"- **{q}**: {a}" for q, a in g.get("trouble", [])], ""]
    return "\n".join(L)


def build() -> list[str]:
    """Write guides/<id>/GUIDE.md and guides/<id>/files/<notebook> for every guide (the learner can also download them)."""
    out = []
    for gid in ids():
        (GUIDES / gid / "GUIDE.md").write_text(markdown(gid), encoding="utf-8")
        out.append(f"guides/{gid}/GUIDE.md")
    return out


def html(path: Path) -> None:
    data = json.dumps(export(), ensure_ascii=False).replace("</", "<\\/")
    Path(path).write_text(TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", data), encoding="utf-8")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "verify":
        for gid in (sys.argv[2:] or ids()):
            o = verify(gid)
            print(gid, "ok:", len(o["cells"]), "code cells,", o["pytest"].splitlines()[-1])
    elif cmd == "build":
        print("\n".join(build()))
    elif cmd == "html":
        html(Path(sys.argv[2]))
        print("wrote", sys.argv[2])

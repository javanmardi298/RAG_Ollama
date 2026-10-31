"""Agent Skills toolkit: validate SKILL.md folders, estimate their context cost (progressive disclosure), and test when each
skill should activate with a simple keyword proxy (a real agent decides from the description)."""
import json
import re
from pathlib import Path

import yaml

NAME = re.compile(r"[a-z0-9-]{1,64}")
STOP = {"the", "a", "an", "and", "or", "to", "of", "is", "when", "use", "user", "asks", "for", "it", "in", "this", "with", "as", "me",
        "please", "here", "give", "out", "how", "what", "one", "its", "into", "wants", "on", "from", "be", "are", "at", "by", "who",
        "which", "should", "do", "next", "based", "s", "data", "list"}


def load_skills(folder="skills"):
    """name -> {"meta": frontmatter, "body": markdown, "dir": path}. Raises ValueError for a SKILL.md without frontmatter."""
    out = {}
    for f in sorted(Path(folder).glob("*/SKILL.md")):
        m = re.match(r"---\n(.*?)\n---\n(.*)", f.read_text(encoding="utf-8"), re.S)
        if not m:
            raise ValueError(f"{f}: missing --- frontmatter ---")
        meta = yaml.safe_load(m.group(1)) or {}
        out[meta.get("name", f.parent.name)] = {"meta": meta, "body": m.group(2), "dir": f.parent}
    return out


def validate(skills):
    """Problems: name format and folder, description length and a 'Use when' clause, referenced files exist."""
    problems = []
    for name, s in skills.items():
        desc = s["meta"].get("description", "")
        if name != s["dir"].name or not NAME.fullmatch(name):
            problems.append(f"{name}: name must equal the folder name (lowercase letters, digits, hyphens)")
        if not 40 <= len(desc) <= 1024:
            problems.append(f"{name}: description should be 40-1024 characters")
        if "use when" not in desc.lower():
            problems.append(f"{name}: description should say when to use the skill ('Use when ...')")
        for ref in re.findall(r"`((?:scripts|reference)/[^`\s]+)", s["body"]):
            if not (s["dir"] / ref).exists():
                problems.append(f"{name}: references a missing file {ref}")
    return problems


def tokens(text):
    """About 4 characters per token: good enough to compare sizes."""
    return max(1, len(text) // 4)


def context_cost(skills):
    """Always in context: name + description. Loaded only when used: the body (and files it reads)."""
    always = sum(tokens(s["meta"]["name"] + s["meta"]["description"]) for s in skills.values())
    bodies = sum(tokens(s["body"]) for s in skills.values())
    return {"always_loaded_tokens": always, "on_demand_tokens": bodies, "if_all_in_prompt_tokens": always + bodies}


def words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP and len(w) > 2}


def activate(request, skills, min_overlap=2):
    """Keyword proxy for 'which skill fits this request' (a real agent reads the descriptions); None if nothing fits."""
    scores = {n: len(words(request) & words(s["meta"]["description"])) for n, s in skills.items()}
    best = max(scores, key=scores.get) if scores else None
    return best if best and scores[best] >= min_overlap else None


def activation_report(skills, cases_path="examples/activation_tests.json"):
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    rows = [{"request": c["request"], "expected": c["skill"], "got": activate(c["request"], skills)} for c in cases]
    return {"correct": sum(r["expected"] == r["got"] for r in rows), "total": len(rows), "rows": rows}

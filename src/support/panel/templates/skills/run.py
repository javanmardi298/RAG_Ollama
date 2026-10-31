# Starter: Agent Skills (SKILL.md folders) - validate them and test when each one should activate.
#   python run.py     checks every skills/*/SKILL.md (frontmatter, name, description length, referenced files) and runs
#                     a tiny activation test: which skill's description best matches each request in config/tests.
# Use them: copy skills/<name>/ to ~/.claude/skills/ (personal) or <repo>/.claude/skills/ (project) for Claude Code,
# or load them with the Agent SDK. Only the name + description sit in context until a skill is needed.
import os, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
(HERE / "results").mkdir(exist_ok=True)
import re

TESTS = cfg.get("tests") or [("how is the project doing? give me a status report", "project-report"),
                             ("here is a receipt, pull out the total and the supplier", "invoice-extract"),
                             ("re-run the thresholds stage please", "run-stage"),
                             ("what's the weather in Berlin", None)]
STOP = {"the", "a", "an", "and", "or", "to", "of", "is", "when", "use", "user", "asks", "for", "it", "in", "this", "with", "as",
        "me", "please", "here", "give", "out", "how", "what", "s", "one", "its", "into", "wants"}
words = lambda s: {w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}  # noqa: E731

skills, problems = {}, []
for f in sorted((HERE / "skills").glob("*/SKILL.md")):
    text = f.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        problems.append(f"{f}: missing --- frontmatter ---")
        continue
    meta = yaml.safe_load(m.group(1)) or {}
    name, desc = meta.get("name", ""), meta.get("description", "")
    if name != f.parent.name or not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        problems.append(f"{f}: name must equal the folder name (lowercase, digits, hyphens)")
    if not 20 <= len(desc) <= 1024 or "use when" not in desc.lower():
        problems.append(f"{f}: description should say what it does AND 'Use when ...' (20-1024 chars)")
    for ref in re.findall(r"`((?:scripts|reference)/[^`]+)`", m.group(2)):
        if not (f.parent / ref.split()[0]).exists():
            problems.append(f"{f}: references missing file {ref}")
    skills[name] = desc
print(f"{len(skills)} skills:", list(skills))
print("problems:", problems or "none - skills valid")

hits = 0
for req, expected in TESTS:
    scores = {n: len(words(req) & words(d)) for n, d in skills.items()}
    best = max(scores, key=scores.get) if scores and max(scores.values()) >= 2 else None
    hits += best == expected
    print(f"  {req[:50]:50s} -> {best}  (expected {expected})")
print(f"activation accuracy {hits}/{len(TESTS)} (keyword proxy; a real client lets the model decide from the description)")
(HERE / "results" / "skills.json").write_text(json.dumps({"skills": list(skills), "problems": problems, "activation": hits}, indent=2))
if problems:
    raise SystemExit(1)

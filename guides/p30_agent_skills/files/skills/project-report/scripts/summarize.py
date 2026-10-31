"""Print the numbers in every results/*.json of a project folder (nested keys joined with '.')."""
import json
import sys
from pathlib import Path


def flatten(d, prefix=""):
    out = {}
    for k, v in (d.items() if isinstance(d, dict) else enumerate(d)):
        key = f"{prefix}{k}"
        if isinstance(v, (dict, list)):
            out.update(flatten(v, key + "."))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[key] = v
    return out


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
files = sorted(root.glob("results/*.json"))
if not files:
    print("no results/*.json found: has the notebook been run?")
for f in files:
    nums = flatten(json.loads(f.read_text(encoding="utf-8")))
    print(f.name, "|", ", ".join(f"{k}={v}" for k, v in list(nums.items())[:12]))

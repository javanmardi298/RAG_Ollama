import json, sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
for f in sorted(root.glob("results/*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    flat = {k: v for k, v in (data.items() if isinstance(data, dict) else []) if isinstance(v, (int, float))}
    print(f.name, flat or "(nested: open the file)")

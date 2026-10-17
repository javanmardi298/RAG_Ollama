# Starter: pretrained V-JEPA 2 on your own clips (docs/jepa.md step 7). Needs a GPU runtime (Colab) and
#   pip install -U transformers torchcodec av
#   python run.py            embeds data/*.mp4, finds nearest neighbours, scores surprise, runs the SSv2 action head
import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [Path(os.environ.get("SUPPORT_ROOT", HERE))] + list(HERE.parents) if (p / "src" / "labkit").is_dir()), None)
if ROOT is None:
    raise SystemExit("Repository not found: keep this folder inside the repo (projects/) or set SUPPORT_ROOT.")
sys.path.insert(0, str(ROOT / "src"))
import yaml

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8")) or {}
(HERE / "results").mkdir(exist_ok=True)
import subprocess

videos = sorted(str(p) for p in (HERE / "data").glob("*.mp4"))
if not videos:
    raise SystemExit("Put a few short .mp4 clips in data/ first (10-50 clips, a few seconds each).")
cmd = [sys.executable, str(ROOT / "scripts" / "jepa5_vjepa2_colab.py"), "--videos", *videos,
       "--encoder", cfg.get("encoder", "facebook/vjepa2-vitl-fpc64-256"), "--frames", str(cfg.get("frames", 16)),
       "--out", str(HERE / "results" / "vjepa2.json")]
print(" ".join(cmd[:3]), "...")
raise SystemExit(subprocess.call(cmd))

# JEPA 5: use a PRETRAINED V-JEPA 2 video encoder (Meta, 2025) as a frozen feature extractor. Needs a GPU runtime
# (Colab T4 is enough for the ViT-L model) and: pip install -U transformers torchcodec av
# Not run in CI (downloads ~1.3 GB). Three practical uses, all with a frozen encoder:
#   1) clip embeddings -> nearest-neighbour search / a small linear probe for your own classes (few labels needed)
#   2) "surprise" over time: big jumps between consecutive window embeddings flag unusual events
#   3) ready-made action recognition with the SSv2-finetuned checkpoint
# Usage (Colab):  !python scripts/jepa5_vjepa2_colab.py --videos /content/clips/*.mp4
# Model cards: https://huggingface.co/facebook/vjepa2-vitl-fpc64-256  (Apache-2.0 code / check each card's licence)
# %%
import argparse, glob, json
from pathlib import Path

import torch

ap = argparse.ArgumentParser()
ap.add_argument("--videos", nargs="+", required=True, help="video files or glob patterns")
ap.add_argument("--encoder", default="facebook/vjepa2-vitl-fpc64-256")
ap.add_argument("--classifier", default="facebook/vjepa2-vitl-fpc16-256-ssv2")
ap.add_argument("--frames", type=int, default=16, help="frames per window")
ap.add_argument("--out", default="results/jepa5_vjepa2.json")
args = ap.parse_args()
files = sorted({f for pat in args.videos for f in glob.glob(pat)})
if not files:
    raise SystemExit("no videos matched")

from torchcodec.decoders import VideoDecoder  # noqa: E402
from transformers import AutoModel, AutoModelForVideoClassification, AutoVideoProcessor  # noqa: E402

device = "cuda" if torch.cuda.is_available() else "cpu"
proc = AutoVideoProcessor.from_pretrained(args.encoder)
enc = AutoModel.from_pretrained(args.encoder, torch_dtype=torch.float16 if device == "cuda" else None).to(device).eval()


def windows(path: str, size: int):
    """Consecutive non-overlapping windows of `size` frames, as (T, C, H, W) uint8 tensors."""
    dec = VideoDecoder(path)
    n = dec.metadata.num_frames or len(dec)
    for start in range(0, max(n - size + 1, 1), size):
        yield dec.get_frames_in_range(start, min(start + size, n)).data


@torch.no_grad()
def embed(clip: torch.Tensor) -> torch.Tensor:
    inputs = proc(clip, return_tensors="pt").to(device)
    feats = enc.get_vision_features(**inputs)          # (1, tokens, dim) patch features
    return feats.mean(1).float().squeeze(0).cpu()      # mean-pool -> one vector per window


# %% 1) + 2) embeddings and surprise per video
report = {}
for f in files:
    vecs = [embed(w) for w in windows(f, args.frames)]
    z = torch.nn.functional.normalize(torch.stack(vecs), dim=-1)
    jumps = (1 - (z[1:] * z[:-1]).sum(-1)).tolist()    # cosine distance between consecutive windows
    report[f] = {"windows": len(vecs), "clip_embedding": z.mean(0).tolist()[:8], "surprise_per_window": jumps,
                 "most_surprising_window": int(torch.tensor(jumps).argmax()) + 1 if jumps else None}
    print(Path(f).name, "windows", len(vecs), "max jump", round(max(jumps), 3) if jumps else "-")

if len(files) > 1:
    clip = torch.nn.functional.normalize(torch.stack([torch.tensor(report[f]["clip_embedding"]) for f in files]), dim=-1)
    sim = clip @ clip.T
    sim.fill_diagonal_(-2.0)                            # a clip is not its own neighbour
    for i, f in enumerate(files):
        j = int(sim[i].argmax())
        print("nearest to", Path(f).name, "->", Path(files[j]).name, round(float(sim[i, j]), 3))

# %% 3) action recognition with the SSv2 head (174 "something-something" actions)
clf = AutoModelForVideoClassification.from_pretrained(args.classifier).to(device).eval()
cproc = AutoVideoProcessor.from_pretrained(args.classifier)
for f in files:
    first = next(windows(f, 16))
    with torch.no_grad():
        logits = clf(**cproc(first, return_tensors="pt").to(device)).logits[0]
    top = logits.softmax(-1).topk(3)
    report[f]["ssv2_top3"] = [(clf.config.id2label[int(i)], round(float(p), 3)) for p, i in zip(top.values, top.indices)]
    print(Path(f).name, report[f]["ssv2_top3"])

Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps(report, indent=2))
print("saved", args.out)

"""Run once after installing: checks Python, PyTorch, the data and one training epoch."""
import sys

import torch

from jepa import linear_probe, load_digits_patches, train

print("Python", sys.version.split()[0], "| torch", torch.__version__.split("+")[0], "| GPU:", torch.cuda.is_available())
data = load_digits_patches()
print("train", tuple(data[0].shape), "test", tuple(data[2].shape))
r = train("ema", epochs=1, data=data)
print("one epoch:", round(r["seconds"], 1), "s, probe accuracy", round(linear_probe(r["encoder"], data), 2))
print("setup ok")

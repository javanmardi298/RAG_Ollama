"""Run once after installing: checks Python, scikit-learn, the data and one training run."""
import sys

import sklearn

from triage import load_tickets, predict, scores, split, train

print("Python", sys.version.split()[0], "| scikit-learn", sklearn.__version__)
tickets = load_tickets()
tr, dev, test = split(tickets)
print(len(tickets), "tickets:", len(tr), "train /", len(dev), "dev /", len(test), "test")
model = train(tr)
print("dev", scores(dev, predict(model, dev)[0]))
print("setup ok")

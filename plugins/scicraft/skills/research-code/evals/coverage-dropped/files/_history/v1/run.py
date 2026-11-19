"""Usage: python3 run.py data/preds.csv runs/<date>"""
import json
import os
import sys

from evalkit.load import load_predictions
from evalkit.score import score

src, out = sys.argv[1], sys.argv[2]
n_total = sum(1 for _ in open(src)) - 1
rows = load_predictions(src)
metrics = score(rows, n_total)
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)
print(metrics)

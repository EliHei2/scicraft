"""Toy encoder training loop used by the sweep. Usage: python3 train.py configs/base.json"""
import json
import math
import random
import sys

import config
import evaluate


def make_data(n=500, d=8, k=4, seed=0):
    rng = random.Random(seed)
    centers = [[rng.gauss(0, 1) for _ in range(d)] for _ in range(k)]
    rows = []
    for i in range(n):
        y = i % k
        rows.append(([c + rng.gauss(0, 1.5) for c in centers[y]], y))
    return rows


def train_encoder(rows, cfg):
    """One linear layer trained to pull rows toward their class mean (a stand-in for real training)."""
    rng = random.Random(cfg.seed)
    d = len(rows[0][0])
    w = [[rng.gauss(0, 1 / math.sqrt(d)) for _ in range(d)] for _ in range(d)]
    for _ in range(cfg.epochs):
        for x, _y in rows:
            z = [sum(wi * xi for wi, xi in zip(row, x)) for row in w]
            for i in range(d):
                for j in range(d):
                    w[i][j] -= cfg.learning_rate * 1e-3 * (z[i] - x[i]) * x[j]
    return lambda x: [sum(wi * xi for wi, xi in zip(row, x)) for row in w]


def main(path):
    cfg = config.load(path)
    rows = make_data(seed=cfg.seed)
    enc = train_encoder(rows, cfg)
    embedded = [(enc(x), y) for x, y in rows]
    result = evaluate.evaluate(embedded, cfg)
    result["learning_rate"] = cfg.learning_rate
    print(json.dumps(result))


if __name__ == "__main__":
    main(sys.argv[1])

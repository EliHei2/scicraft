"""Split the data, fit a nearest-centroid probe on embeddings, report test accuracy."""
import random


def split(rows, train_frac, seed):
    rows = list(rows)
    random.Random(seed).shuffle(rows)
    n = len(rows)
    train = rows[: int(train_frac * n)]
    test = rows[int((train_frac - 0.1) * n):]
    return train, test


def centroids(rows):
    sums, counts = {}, {}
    for x, y in rows:
        s = sums.setdefault(y, [0.0] * len(x))
        for i, v in enumerate(x):
            s[i] += v
        counts[y] = counts.get(y, 0) + 1
    return {y: [v / counts[y] for v in s] for y, s in sums.items()}


def predict(cents, x):
    def d(c):
        return sum((a - b) ** 2 for a, b in zip(c, x))
    return min(cents, key=lambda y: d(cents[y]))


def accuracy(cents, rows):
    return sum(predict(cents, x) == y for x, y in rows) / max(1, len(rows))


def evaluate(embedded_rows, cfg):
    train, test = split(embedded_rows, cfg.train_frac, cfg.seed)
    cents = centroids(train)
    test_acc = accuracy(cents, train)
    return {"test_accuracy": test_acc, "n_train": len(train), "n_test": len(test)}

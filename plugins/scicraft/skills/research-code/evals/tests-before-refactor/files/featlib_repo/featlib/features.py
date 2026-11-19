"""Feature preparation for the measurement table: read, filter by quality, label, normalize, sample."""
import csv
import random
import statistics


def load_rows(path):
    """Read the raw table (columns: id, qv, value) into a list of dicts, in file order."""
    with open(path) as f:
        return [{"id": r["id"], "qv": float(r["qv"]), "value": float(r["value"])} for r in csv.DictReader(f)]


def filter_quality(rows, min_qv=20):
    """Keep rows whose quality value is at least min_qv."""
    return [r for r in rows if r["qv"] >= min_qv]


def attach_labels(rows, labels, min_qv=20):
    """Filter by quality, then attach labels.

    labels[i] is the label of rows[i] in the raw table (one label per raw row, same order).
    """
    kept = filter_quality(rows, min_qv)
    for i, r in enumerate(kept):
        r["label"] = labels[i]
    return kept


def normalize(values):
    """Z-score a list of floats; a constant list maps to zeros."""
    if not values:
        return []
    mu = statistics.fmean(values)
    sd = statistics.pstdev(values)
    return [0.0 if sd == 0 else (v - mu) / sd for v in values]


def sample_rows(rows, n, seed=0):
    """Draw n rows without replacement, reproducibly."""
    return random.Random(seed).sample(rows, min(n, len(rows)))

"""The one implementation of the unit-level score used in every figure."""
import csv

MIN_COUNT = 20  # units with fewer counts are excluded everywhere (Methods, section 2.3)


def load(path="data/per_unit.tsv"):
    with open(path, newline="") as fh:
        return [dict(r, count=int(r["count"]), score=float(r["score"])) for r in csv.DictReader(fh, delimiter="\t")]


def mean_score(rows, method, min_count=MIN_COUNT):
    vals = [r["score"] for r in rows if r["method"] == method and r["count"] >= min_count]
    return sum(vals) / len(vals)

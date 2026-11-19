import csv


def load_predictions(path, min_conf=0.2):
    """Read predictions and keep rows the model is confident about."""
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            r["conf"] = float(r["conf"])
            if r["conf"] >= min_conf:
                rows.append(r)
    return rows

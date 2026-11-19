def score(rows, n_total):
    """Coverage is the fraction of all rows that were scored; accuracy is over scored rows."""
    correct = 0
    for r in rows:
        if r["pred"] == r["label"]:
            correct += 1
    return {
        "n_total": n_total,
        "n_scored": len(rows),
        "coverage": round(len(rows) / n_total, 4),
        "accuracy": round(correct / max(len(rows), 1), 4),
    }

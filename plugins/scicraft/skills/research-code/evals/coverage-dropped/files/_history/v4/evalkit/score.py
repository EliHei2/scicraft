def score(rows, n_total):
    """Coverage is the fraction of all rows that were scored; accuracy is over scored rows."""
    correct = sum(r["pred"] == r["label"] for r in rows)
    return {
        "n_total": n_total,
        "n_scored": len(rows),
        "coverage": round(len(rows) / n_total, 4),
        "accuracy": round(correct / max(len(rows), 1), 4),
    }

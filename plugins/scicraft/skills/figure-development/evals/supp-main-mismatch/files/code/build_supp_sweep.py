"""Supp Fig S3: score as the minimum-count filter moves (5, 10, 20, 50). 20 is the default."""
import csv

THRESHOLDS = [5, 10, 20, 50]

rows = []
with open("data/per_unit.tsv", newline="") as fh:
    for r in csv.DictReader(fh, delimiter="\t"):
        rows.append((r["method"], int(r["count"]), float(r["score"])))

with open("data/supp_sweep.tsv", "w") as fh:
    fh.write("method\tmin_count\tscore\n")
    for m in ("ours", "baseline_a", "baseline_b"):
        for t in THRESHOLDS:
            vals = [s for (mm, c, s) in rows if mm == m and c > t]
            fh.write(f"{m}\t{t}\t{sum(vals) / len(vals):.6f}\n")

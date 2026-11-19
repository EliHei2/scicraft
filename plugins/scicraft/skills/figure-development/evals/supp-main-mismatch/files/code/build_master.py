"""Main-figure table: one canonical value per method (Fig 2c reads this)."""
from metrics import load, mean_score

rows = load()
with open("data/master.tsv", "w") as fh:
    fh.write("key\tvalue\n")
    for m in ("ours", "baseline_a", "baseline_b"):
        fh.write(f"{m}/score\t{mean_score(rows, m):.6f}\n")

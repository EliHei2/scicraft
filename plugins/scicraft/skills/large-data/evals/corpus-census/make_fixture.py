#!/usr/bin/env python3
"""Regenerate files/ for the corpus-census case: a corpus with a byte-identical duplicate
under another name, a re-processed derivative, an unreadable archive, and a manifest that
lists two entries not present locally."""
import argparse
import gzip
from pathlib import Path

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--out", type=Path, default=Path(__file__).parent / "files")
a = ap.parse_args()
c = a.out / "corpus"
for d in ("site_a", "site_b", "site_c", "downloads_old"):
    (c / d).mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(5)

def table(n):
    return pd.DataFrame({"user_id": rng.integers(0, 10**6, n), "item_id": rng.integers(0, 10**5, n),
                         "ts": rng.integers(1_600_000_000, 1_700_000_000, n)})

a24 = table(12000); a24.to_parquet(c / "site_a/clicks_2024.parquet", index=False)
a25 = table(15000); a25.to_parquet(c / "site_a/clicks_2025.parquet", index=False)
b25 = table(9000); b25.to_parquet(c / "site_b/clicks_2025.parquet", index=False)
b25r = b25.copy(); b25r["session_id"] = rng.integers(0, 10**5, len(b25r))
b25r.to_parquet(c / "site_b/clicks_2025_clean.parquet", index=False)
c24 = table(7000); c24.to_csv(c / "site_c/clicks_2024.csv", index=False)
with gzip.open(c / "site_c/clicks_2025.csv.gz", "wb") as f:
    f.write(b"user_id,item_id,ts\n1,2,3\n")
raw = (c / "site_c/clicks_2025.csv.gz").read_bytes()
(c / "site_c/clicks_2025.csv.gz").write_bytes(raw[: len(raw) // 2])     # truncated download
(c / "downloads_old/export_17.parquet").write_bytes((c / "site_a/clicks_2025.parquet").read_bytes())
pd.DataFrame({
    "path": ["site_a/clicks_2024.parquet", "site_a/clicks_2025.parquet", "site_b/clicks_2025.parquet",
             "site_b/clicks_2025_clean.parquet", "site_c/clicks_2024.csv", "site_c/clicks_2025.csv.gz",
             "site_d/clicks_2024.parquet", "site_d/clicks_2025.parquet"],
    "source": ["site_a", "site_a", "site_b", "site_b", "site_c", "site_c", "site_d", "site_d"],
    "note": ["", "", "", "output of our cleaning pipeline run on site_b 2025", "", "", "", ""],
}).to_csv(a.out / "sources.csv", index=False)
print("wrote", a.out)

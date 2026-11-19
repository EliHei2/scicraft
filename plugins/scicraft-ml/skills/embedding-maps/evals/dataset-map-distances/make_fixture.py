"""Builds files/view_stats.csv and files/view_model.csv for this case.

One vector per dataset from two encoders: 60 real tables, 300 synthetic tables (narrower and shifted), 20
noise-perturbed variants of real tables (clean = False) and 4 row-chunk copies of one real table (ids ending
_chunk0.._chunk3). The second encoder failed on three datasets, so the views share 381 of 384 ids.
Run: python3 make_fixture.py --outdir files  (numpy, pandas)
"""
import argparse
import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--outdir", default="files")
p.add_argument("--seed", type=int, default=0)
a = p.parse_args()
rng = np.random.default_rng(a.seed)
rows = []
for i in range(60):
    rows.append((f"real_{i:03d}", "real", True, rng.normal(0, 1.0, 24)))
for i in range(300):
    rows.append((f"synth_{i:03d}", "synthetic", True, rng.normal(0, 0.7, 24) + 0.4))
for i in range(0, 60, 6):
    base = rows[i][3]
    for sev in (0.1, 0.3):
        rows.append((f"real_{i:03d}~noise@{sev}", "real (perturbed)", False, base + rng.normal(0, sev * 3, 24)))
for c in range(4):
    rows.append((f"real_007_chunk{c}", "real", True, rows[7][3] + rng.normal(0, 0.05, 24)))
ids = [r[0] for r in rows]
E = np.stack([r[3] for r in rows])
base = pd.DataFrame({"dataset": ids, "source": [r[1] for r in rows], "clean": [r[2] for r in rows]})
v1 = pd.concat([base, pd.DataFrame(E[:, :12], columns=[f"emb_{j}" for j in range(12)])], axis=1)
W = rng.normal(size=(24, 32))
v2 = pd.concat([base, pd.DataFrame(np.tanh(E @ W / 5), columns=[f"emb_{j}" for j in range(32)])], axis=1)
v2 = v2.drop(index=[3, 70, 71])      # three items the second encoder failed on
v1.to_csv(f"{a.outdir}/view_stats.csv", index=False)
v2.to_csv(f"{a.outdir}/view_model.csv", index=False)
print(len(v1), len(v2))

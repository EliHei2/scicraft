#!/usr/bin/env python3
"""Regenerate files/ for the positional-join case: features with labels, and predictions
written by a parallel loader (shuffled, 3% of users missing), plus the user's merge script."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--out", type=Path, default=Path(__file__).parent / "files")
a = ap.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)
n = 20000
feat = pd.DataFrame({"user_id": rng.permutation(np.arange(100000, 100000 + n)),
                     "n_sessions": rng.poisson(12, n), "label": rng.integers(0, 2, n)})
feat.to_csv(a.out / "features.csv", index=False)
correct = rng.random(n) < 0.9
pred = feat[["user_id"]].copy()
pred["pred"] = np.where(correct, feat["label"], 1 - feat["label"])
pred = pred.sample(frac=0.97, random_state=3).reset_index(drop=True)
pred.to_csv(a.out / "preds.csv", index=False)
(a.out / "merge_preds.py").write_text('''import pandas as pd

feat = pd.read_csv("features.csv")
pred = pd.read_csv("preds.csv")

# predictions come back from the inference job, one row per user
df = pd.concat([feat.reset_index(drop=True), pred[["pred"]].reset_index(drop=True)], axis=1)
df = df.dropna()
acc = (df["label"] == df["pred"]).mean()
print(f"n={len(df)} accuracy={acc:.3f}")
''')
print("wrote", a.out)

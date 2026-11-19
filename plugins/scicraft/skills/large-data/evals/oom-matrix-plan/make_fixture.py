#!/usr/bin/env python3
"""Regenerate files/ for the oom-matrix-plan case: three small sample shards of a click log
and the user's script that densifies everything."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--out", type=Path, default=Path(__file__).parent / "files")
a = ap.parse_args()
(a.out / "sample_shards").mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(11)
for s in range(3):
    n = 30000
    pd.DataFrame({
        "user_id": rng.integers(0, 5000, n),
        "item_id": rng.zipf(1.4, n).clip(max=20000),
        "ts": rng.integers(1_700_000_000, 1_710_000_000, n),
        "dwell_ms": rng.exponential(8000, n).astype("int64"),
        "is_bot": rng.random(n) < 0.04,
    }).to_parquet(a.out / "sample_shards" / f"part-{s:05d}.parquet", index=False)
(a.out / "build_matrix.py").write_text('''import glob
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD

files = sorted(glob.glob("/data/clicks/part-*.parquet"))   # 1,800 shards, ~900M rows
df = pd.concat([pd.read_parquet(f) for f in files])
df = df[~df.is_bot]
mat = df.pivot_table(index="user_id", columns="item_id", values="ts", aggfunc="count", fill_value=0)
item_corr = np.corrcoef(mat.values.T)          # used later for item-item neighbours
svd = TruncatedSVD(n_components=128).fit(mat.values)
np.save("user_factors.npy", svd.transform(mat.values))
np.save("item_corr.npy", item_corr)
''')
print("wrote", a.out)

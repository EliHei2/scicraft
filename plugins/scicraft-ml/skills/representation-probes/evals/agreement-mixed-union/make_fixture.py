"""Builds files/ for this case: two embedding spaces of the same 200 items, 100 real and 100 synthetic.
Both spaces separate real from synthetic by a large offset; inside each group the two geometries are
unrelated. Agreement over the union is high only because of the group split. Run: python3 make_fixture.py"""
from pathlib import Path

import numpy as np

rng = np.random.default_rng(3)
n, da, db = 100, 48, 24
group = np.r_[np.zeros(n), np.ones(n)]
off_a = rng.normal(size=da)
off_b = rng.normal(size=db)
A = rng.normal(size=(2 * n, da)) + 4 * group[:, None] * off_a
B = rng.normal(size=(2 * n, db)) + 4 * group[:, None] * off_b
out = Path(__file__).parent / "files"
out.mkdir(exist_ok=True)
np.save(out / "ours.npy", A.astype(np.float32))
np.save(out / "baseline.npy", B.astype(np.float32))
(out / "groups.txt").write_text("\n".join("real" if g == 0 else "synthetic" for g in group) + "\n")
print("wrote", out)

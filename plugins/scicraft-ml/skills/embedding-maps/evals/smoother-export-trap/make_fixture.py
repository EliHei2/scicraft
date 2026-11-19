"""Builds files/dense_field.npz and files/thin_field.npz for this case.

dense: every point of a round sample, vector = token identity + domain direction + noise (keys emb, xy, cell_id).
thin:  a 4% subsample of the SAME points (same coordinates, so a coordinate join works), whose vectors are the mean
       of each point's 40 spatial neighbors (borrowed support: smoother map, higher Moran's I) and then rotated
       by a random orthogonal matrix, standing for a different checkpoint. Joined on coordinates, the two exports
       disagree (cosine near 0), and at matched depth the thin export's smoothness is not reliability.
Run: python3 make_fixture.py  (numpy, scipy)
"""
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(11)
size, d = 2400.0, 12
cxy = rng.uniform(0, size, (1600, 2))
cxy = cxy[np.linalg.norm(cxy - size / 2, axis=1) < size * 0.48]
seeds = rng.uniform(0.2 * size, 0.8 * size, (5, 2))
dom = np.argmin(((cxy[:, None] - seeds[None]) ** 2).sum(-1), 1)
D = rng.normal(size=(5, d))
D /= np.linalg.norm(D, axis=1, keepdims=True)
G = rng.normal(size=(30, d)) * 1.6
cell = np.repeat(np.arange(len(cxy)), rng.poisson(18, len(cxy)).clip(3))
xy = (cxy[cell] + rng.normal(0, 4.0, (len(cell), 2))).astype(np.float32)
emb = G[rng.integers(0, 30, len(cell))] + 1.2 * D[dom[cell]] + rng.normal(0, 0.5, (len(cell), d))
(HERE / "files").mkdir(exist_ok=True)
np.savez_compressed(HERE / "files" / "dense_field.npz", emb=emb.astype(np.float16), xy=xy,
                    cell_id=cell.astype(np.int32))
keep = np.sort(rng.choice(len(cell), int(0.04 * len(cell)), replace=False))
nb = cKDTree(xy).query(xy[keep], k=40)[1]
thin = emb[nb].mean(1)
Q, _ = np.linalg.qr(rng.normal(size=(d, d)))
np.savez_compressed(HERE / "files" / "thin_field.npz", emb=(thin @ Q).astype(np.float16), xy=xy[keep],
                    cell_id=cell[keep].astype(np.int32))
print(len(cell), "dense points,", len(keep), "thin points")

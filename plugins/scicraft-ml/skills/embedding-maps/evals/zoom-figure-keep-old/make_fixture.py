"""Builds files/field_export.npz and files/figures/field_zoom.png for this case.

A round sample of cells in five smooth domains; each point's vector is a token-identity part (large, spatially
white) plus a domain direction plus noise. Keys: emb (n, 12), xy (n, 2) in um, cell_id, cell_type (10 labels).
figures/field_zoom.png stands for a figure the author has already seen; the case checks it is left untouched.
Run: python3 make_fixture.py  (numpy, matplotlib)
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(7)
size, d = 2400.0, 12
cxy = rng.uniform(0, size, (1700, 2))
cxy = cxy[np.linalg.norm(cxy - size / 2, axis=1) < size * 0.48]
seeds = rng.uniform(0.2 * size, 0.8 * size, (5, 2))
dom = np.argmin(((cxy[:, None] - seeds[None]) ** 2).sum(-1), 1)
ctype = (dom * 2 + (rng.random(len(cxy)) < 0.3)).astype(np.int64)
D = rng.normal(size=(10, d))
D /= np.linalg.norm(D, axis=1, keepdims=True)
G = rng.normal(size=(30, d)) * 1.6
cell = np.repeat(np.arange(len(cxy)), rng.poisson(18, len(cxy)).clip(3))
xy = cxy[cell] + rng.normal(0, 4.0, (len(cell), 2))
emb = G[rng.integers(0, 30, len(cell))] + 1.8 * D[ctype[cell]] + rng.normal(0, 0.5, (len(cell), d))
(HERE / "files" / "figures").mkdir(parents=True, exist_ok=True)
np.savez_compressed(HERE / "files" / "field_export.npz", emb=emb.astype(np.float16), xy=xy.astype(np.float32),
                    cell_id=cell.astype(np.int32), cell_type=ctype[cell].astype(np.int16))
fig, ax = plt.subplots(figsize=(3, 3))
ax.scatter(xy[::5, 0], xy[::5, 1], s=0.5, c=ctype[cell][::5], cmap="tab10")
ax.set_axis_off()
fig.savefig(HERE / "files" / "figures" / "field_zoom.png", dpi=150)
print(len(cell), "points,", len(cxy), "cells")

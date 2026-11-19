"""Builds files/ for this case: three encoders over 60 datasets, two disjoint halves each, plus the full
dataset and a label-shuffled copy. alpha moves most under shuffling but is noisy; beta has the best signal over
noise; gamma is label-blind with tight halves. Run: python3 make_fixture.py"""
from pathlib import Path

import numpy as np

rng = np.random.default_rng(7)
n = 60
out = Path(__file__).parent / "files" / "encoders"
spec = {"alpha": (64, 4.0, 14.0), "beta": (32, 2.0, 0.35), "gamma": (16, 0.002, 0.15)}
for name, (d, label, noise) in spec.items():
    base = rng.normal(size=(n, d)) * 3
    task_dir = rng.normal(size=(n, d))
    task_dir /= np.linalg.norm(task_dir, axis=1, keepdims=True)
    full = base + label * task_dir
    shuffled = base
    half_a = full + noise * rng.normal(size=(n, d)) / np.sqrt(d) * 1.4
    half_b = full + noise * rng.normal(size=(n, d)) / np.sqrt(d) * 1.4
    p = out / name
    p.mkdir(parents=True, exist_ok=True)
    for k, v in dict(full=full, shuffled=shuffled, half_a=half_a, half_b=half_b).items():
        np.save(p / f"{k}.npy", v.astype(np.float32))
print("wrote", out)

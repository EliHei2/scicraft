"""Shared helpers for the embedding-maps scripts: read an embedding table, unit-normalize, hash inputs.

An embedding table is one row per item (a token, a point, a row of a dataset) with a d-dimensional vector,
optional coordinates and optional keys. Accepted files:

  .npz      keys: emb (n, d) required; xy (n, 2) optional; any other 1-D key of length n (unit ids, labels)
  .parquet  columns: emb_0 .. emb_{d-1} (prefix set with --emb-prefix), optional x, y and key columns
  .csv      same columns as parquet

Dependencies: numpy; pandas (+ pyarrow) only for .parquet and .csv.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np


def unit(z: np.ndarray) -> np.ndarray:
    """Rows scaled to length 1. A zero row stays zero."""
    z = np.asarray(z, np.float32)
    return z / np.linalg.norm(z, axis=1, keepdims=True).clip(1e-8)


def sha256(path: Path, limit: int | None = None) -> str:
    """Content hash of a file (identity by bytes, never by file name)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        left = limit
        while True:
            b = fh.read(1 << 20 if left is None else min(1 << 20, left))
            if not b:
                break
            h.update(b)
            if left is not None:
                left -= len(b)
                if left <= 0:
                    break
    return h.hexdigest()


def read_table(path: Path, emb_prefix: str = "emb_", keys: list[str] | None = None) -> dict:
    """-> {'emb': (n,d) float32, 'xy': (n,2) float64 or None, <key>: (n,) array for each requested key}."""
    path = Path(path)
    keys = [k for k in (keys or []) if k]
    out: dict = {}
    if path.suffix == ".npz":
        d = np.load(path, allow_pickle=False)
        if "emb" not in d:
            raise SystemExit(f"{path}: no 'emb' array (have {list(d.keys())})")
        out["emb"] = np.asarray(d["emb"], np.float32)
        out["xy"] = np.asarray(d["xy"], np.float64) if "xy" in d else None
        for k in keys:
            if k not in d:
                raise SystemExit(f"{path}: no key {k!r} (have {list(d.keys())})")
            out[k] = np.asarray(d[k])
    elif path.suffix in (".parquet", ".csv"):
        import pandas as pd
        df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        cols = [c for c in df.columns if str(c).startswith(emb_prefix)]
        if not cols:
            raise SystemExit(f"{path}: no columns starting with {emb_prefix!r}")
        cols = sorted(cols, key=lambda c: int(str(c)[len(emb_prefix):]) if str(c)[len(emb_prefix):].isdigit() else 0)
        out["emb"] = df[cols].to_numpy(np.float32)
        out["xy"] = df[["x", "y"]].to_numpy(np.float64) if {"x", "y"} <= set(df.columns) else None
        for k in keys:
            if k not in df.columns:
                raise SystemExit(f"{path}: no column {k!r}")
            out[k] = df[k].to_numpy()
    else:
        raise SystemExit(f"{path}: unsupported format (use .npz, .parquet or .csv)")
    n = len(out["emb"])
    if not np.isfinite(out["emb"]).all():
        raise SystemExit(f"{path}: emb holds NaN or inf")
    for k, v in out.items():
        if v is not None and len(v) != n:
            raise SystemExit(f"{path}: {k} has {len(v)} rows, emb has {n}")
    return out


def add_rows(acc: np.ndarray, idx: np.ndarray, z: np.ndarray) -> None:
    """acc[idx] += z for a 2-D z, one bincount per column (an order of magnitude faster than np.add.at)."""
    nb = acc.shape[0]
    for j in range(z.shape[1]):
        acc[:, j] += np.bincount(idx, weights=z[:, j], minlength=nb)[:nb]

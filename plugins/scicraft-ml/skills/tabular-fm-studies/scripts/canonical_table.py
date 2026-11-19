#!/usr/bin/env python3
"""Equal-budget canonical copy of a real table, as a tabular foundation-model prior would emit it.

Steps (ported from a working study pipeline, October 2026; numpy port checked against tabicl 2.2.0):
  1. encode: ordinal-encode categoricals, parse numbers stored as strings, drop datetime / period /
     timedelta columns and text columns (string columns with more than max(100, 0.5 n) distinct values),
     drop grouping and time key columns you name; count everything dropped.
  2. budget: seeded subsample to at most --max-rows rows (stratified for classification, largest-remainder
     allocation, at least one row per class) and --max-features columns. The seed is a sha256 hash of the
     dataset id, so it does not depend on PYTHONHASHSEED. The original size is kept in the header.
  3. canonical: clamp at inlier mean +/- 4 inlier SD (both re-estimated on inliers, ddof 1, SD floor 1e-6),
     then z-score (clip +/-100), then NaN -> 0 (the column mean). Categorical flags are dropped, because the
     prior emits none. Regression targets get the same clamp and z-score.
  4. optional: regression target binned into --bin-target quantile classes, ties to the lower bin.

Writes one .npz (X, y, header JSON) and prints what was dropped and kept. With --check-tabicl it also
compares the numpy clamp and z-score with tabicl.prior._reg2cls on this table (needs tabicl and torch).

Dependencies: numpy, pandas (pyarrow for .parquet input). Optional: tabicl + torch for --check-tabicl.

Usage:
  python canonical_table.py table.csv --target y --task auto --out table_canon.npz
  python canonical_table.py t.parquet --target label --drop-cols store_id,date --max-rows 1024 --bin-target 10
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd


def stable_seed(*parts) -> int:
    """31-bit seed from named parts, independent of PYTHONHASHSEED."""
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


def task_type_of(y: pd.Series, declared: str = "auto") -> str:
    if declared in ("binary", "multiclass", "regression"):
        return declared
    s = pd.Series(y)
    if s.dtype.kind in "OUSb" or isinstance(s.dtype, pd.CategoricalDtype) or s.dtype.name in ("string", "str"):
        return "binary" if s.nunique(dropna=True) <= 2 else "multiclass"
    if s.dtype.kind in "iu" and s.nunique() <= 30:
        return "binary" if s.nunique() <= 2 else "multiclass"
    return "regression"


def encode_frame(df: pd.DataFrame, max_text_card: float = 0.5):
    """Numeric matrix, categorical mask, column names and drop counts."""
    cols, mask, names = [], [], []
    dropped = {"n_dropped_text": 0, "n_dropped_datetime": 0, "n_dropped_other": 0}
    n = len(df)
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_datetime64_any_dtype(s) or isinstance(s.dtype, pd.PeriodDtype) \
                or pd.api.types.is_timedelta64_dtype(s):
            dropped["n_dropped_datetime"] += 1
            continue
        if pd.api.types.is_bool_dtype(s):
            cols.append(s.astype("float32").to_numpy()); mask.append(True); names.append(str(c))
            continue
        is_cat = isinstance(s.dtype, pd.CategoricalDtype)
        if not is_cat and (s.dtype.kind in "OSU" or s.dtype.name in ("string", "str")):
            if s.nunique(dropna=True) > max(100, max_text_card * n):
                dropped["n_dropped_text"] += 1
                continue
            num = pd.to_numeric(s, errors="coerce")
            if num.notna().sum() == s.notna().sum():          # numbers stored as strings
                cols.append(num.to_numpy(np.float32)); mask.append(False); names.append(str(c))
                continue
            is_cat = True
        if is_cat:
            codes = pd.Categorical(s.astype("object").where(s.notna(), None)).codes.astype(np.float32)
            codes[codes < 0] = np.nan
            cols.append(codes); mask.append(True)
        else:
            try:
                cols.append(pd.to_numeric(s, errors="coerce").to_numpy(np.float32)); mask.append(False)
            except Exception:
                dropped["n_dropped_other"] += 1
                continue
        names.append(str(c))
    X = np.column_stack(cols).astype(np.float32) if cols else np.zeros((n, 0), np.float32)
    X[~np.isfinite(X)] = np.nan
    return X, np.array(mask, dtype=bool), names, dropped


def stratified_rows(y: np.ndarray, n_keep: int, rng: np.random.Generator) -> np.ndarray:
    classes, counts = np.unique(y, return_counts=True)
    quota = counts / counts.sum() * n_keep
    alloc = np.minimum(np.maximum(np.floor(quota).astype(int), 1), counts)
    while alloc.sum() < n_keep:                                   # largest remainder, within class sizes
        room = alloc < counts
        if not room.any():
            break
        alloc[int(np.argmax(np.where(room, quota - alloc, -np.inf)))] += 1
    while alloc.sum() > n_keep:
        alloc[int(np.argmax(alloc))] -= 1
    idx = [rng.choice(np.flatnonzero(y == c), size=a, replace=False) for c, a in zip(classes, alloc)]
    return np.sort(np.concatenate(idx))


def outlier_removing(X: np.ndarray, threshold: float = 4.0) -> np.ndarray:
    """numpy port of tabicl.prior._reg2cls.outlier_removing (tabicl 2.2.0)."""
    X = np.asarray(X, dtype=np.float64)
    ddof = 1 if X.shape[0] > 1 else 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean = np.nanmean(X, axis=0)
        std = np.clip(np.nanstd(X, axis=0, ddof=ddof), 1e-6, None)
        mask = (mean - std * threshold <= X) & (X <= mean + std * threshold) & ~np.isnan(X)
        masked = np.where(mask, X, np.nan)
        m_mean = np.nanmean(masked, axis=0)
        m_std = np.clip(np.nanstd(masked, axis=0, ddof=ddof), 1e-6, None)
    m_mean = np.where(np.isnan(m_mean), mean, m_mean)
    m_std = np.where(np.isnan(m_std), 0.0, m_std)
    lower = np.nan_to_num(m_mean - m_std * threshold, nan=-np.inf)
    upper = np.nan_to_num(m_mean + m_std * threshold, nan=np.inf)
    return np.clip(X, lower, upper)


def standard_scaling(X: np.ndarray, clip_value: float = 100.0) -> np.ndarray:
    """numpy port of tabicl.prior._reg2cls.standard_scaling (tabicl 2.2.0)."""
    X = np.asarray(X, dtype=np.float64)
    ddof = 1 if X.shape[0] > 1 else 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean = np.nanmean(X, axis=0)
        std = np.clip(np.nanstd(X, axis=0, ddof=ddof), 1e-6, None)
    return np.clip((X - mean) / std, -clip_value, clip_value)


def bin_target(y: np.ndarray, n_bins: int = 10) -> np.ndarray:
    """Quantile classes 0..K-1; ties go to the lower bin, so zero-inflated targets keep 2+ classes."""
    y = np.asarray(y, dtype=np.float64)
    qs = np.unique(np.nanquantile(y, np.linspace(0, 1, n_bins + 1)[1:-1]))
    return np.unique(np.searchsorted(qs, y, side="left"), return_inverse=True)[1].astype(np.int64)


def check_against_tabicl(X: np.ndarray) -> float:
    import torch
    from tabicl.prior._reg2cls import outlier_removing as t_or, standard_scaling as t_ss
    ref = t_ss(t_or(torch.tensor(X, dtype=torch.float32))).numpy()
    ours = standard_scaling(outlier_removing(X))
    if not np.array_equal(np.isnan(ref), np.isnan(ours)):
        raise AssertionError("NaN pattern differs from tabicl")
    ok = ~np.isnan(ours)
    return float(np.max(np.abs(ours[ok] - ref[ok]))) if ok.any() else 0.0


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.suffix in (".parquet", ".pq") else pd.read_csv(path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("table", type=Path, help="CSV or parquet file, one row per sample")
    ap.add_argument("--target", required=True, help="target column")
    ap.add_argument("--task", default="auto", choices=["auto", "binary", "multiclass", "regression"])
    ap.add_argument("--dataset-id", default=None, help="id used for the subsample seed (default: file stem)")
    ap.add_argument("--drop-cols", default="", help="comma-separated grouping / time key columns to drop")
    ap.add_argument("--max-rows", type=int, default=1024)
    ap.add_argument("--max-features", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bin-target", type=int, default=0, help="bin a regression target into this many classes")
    ap.add_argument("--out", type=Path, required=True, help="output .npz")
    ap.add_argument("--check-tabicl", action="store_true", help="compare the clamp+z-score with tabicl")
    a = ap.parse_args(argv)

    df = read_table(a.table)
    if a.target not in df.columns:
        print(f"FAIL: target {a.target!r} not in columns", file=sys.stderr)
        return 1
    did = a.dataset_id or a.table.stem
    drop = [c for c in a.drop_cols.split(",") if c]
    missing = [c for c in drop if c not in df.columns]
    if missing:
        print(f"FAIL: --drop-cols not found: {missing}", file=sys.stderr)
        return 1
    y_raw = df[a.target]
    keep = y_raw.notna().to_numpy()
    tt = task_type_of(y_raw, a.task)
    X, cat_mask, names, dropped = encode_frame(df.drop(columns=[a.target] + drop))
    X = X[keep]
    if tt == "regression":
        y = pd.to_numeric(y_raw[keep], errors="coerce").to_numpy(np.float64)
    else:
        y = pd.Categorical(y_raw[keep].astype(str)).codes.astype(np.int64)
    n0, d0 = X.shape

    rng = np.random.default_rng(stable_seed(did, a.seed, "subsample"))
    rows = np.arange(n0)
    if n0 > a.max_rows:
        rows = stratified_rows(y, a.max_rows, rng) if tt != "regression" else np.sort(rng.choice(n0, a.max_rows, replace=False))
    cols = np.arange(d0)
    if d0 > a.max_features:
        cols = np.sort(rng.choice(d0, a.max_features, replace=False))
    X, y = X[np.ix_(rows, cols)], y[rows]
    names, cat_mask = [names[i] for i in cols], cat_mask[cols]
    if tt != "regression":
        y = np.unique(y, return_inverse=True)[1].astype(np.int64)
        tt = "binary" if y.max() <= 1 else "multiclass"

    max_diff = None
    if a.check_tabicl and X.shape[1]:
        max_diff = check_against_tabicl(X)
    Xc = standard_scaling(outlier_removing(X)) if X.shape[1] else X.astype(np.float64)
    n_nan = int(np.isnan(Xc).sum())
    Xc[np.isnan(Xc)] = 0.0
    binned = False
    if tt == "regression":
        if a.bin_target:
            y, binned = bin_target(y, a.bin_target), True
        else:
            y = standard_scaling(outlier_removing(y.reshape(-1, 1))).ravel()
            y[np.isnan(y)] = 0.0

    header = {"dataset_id": did, "task_type": tt, "binned_target": binned, "feature_names": names,
              "original_categorical": [n for n, c in zip(names, cat_mask) if c], "original_n_rows": int(n0),
              "original_n_features": int(d0), "dropped_key_columns": drop, **dropped,
              "n_missing_filled": n_nan, "rows_without_target_dropped": int((~keep).sum()),
              "preprocessing": "ordinal codes; 4-SD inlier clamp; z-score clip 100; NaN->0; no categorical flags"}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, X=Xc.astype(np.float32), y=y, header=np.array(json.dumps(header)))

    print(f"table      {did}: {n0} x {d0} after encoding -> {Xc.shape[0]} x {Xc.shape[1]} (budget "
          f"{a.max_rows} x {a.max_features})")
    print(f"target     {tt}{' binned to %d classes' % len(np.unique(y)) if binned else ''}; "
          f"{int((~keep).sum())} rows without target dropped")
    print(f"dropped    text {dropped['n_dropped_text']}, datetime {dropped['n_dropped_datetime']}, "
          f"other {dropped['n_dropped_other']}, key columns {len(drop)}")
    print(f"canonical  {len(header['original_categorical'])} categorical columns now unflagged z-scored codes; "
          f"{n_nan} missing cells set to 0; max |x| = {np.abs(Xc).max() if Xc.size else 0:.2f}")
    if max_diff is not None:
        status = "ok" if max_diff < 1e-4 else "MISMATCH"
        print(f"tabicl     numpy port vs tabicl._reg2cls max |diff| = {max_diff:.2e} ({status}, tolerance 1e-4)")
        if status != "ok":
            return 1
    print(f"wrote      {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

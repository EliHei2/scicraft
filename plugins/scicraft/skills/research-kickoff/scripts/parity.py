#!/usr/bin/env python3
"""Prove a reimplementation against the authors' own released outputs.

Both inputs are tables with one row per item (a dataset, an image, a sentence) and one column per output
dimension. Rows are matched by an id column when one is given, otherwise by order. The script reports:

  - per-dimension Pearson r between reference and reimplementation, and its minimum over all dimensions;
  - Spearman correlation of the two pairwise-distance structures (are the same items close to each other?);
  - the largest absolute difference.

Released outputs are often min-max normalized per dimension. Pearson r is unaffected by that; distances and
absolute differences are not, so pass --minmax to scale both sides the same way before those two numbers.

The pass rule is the one used when a ported set encoder was accepted: minimum per-dimension r and the
distance-structure Spearman both at or above --min-r (default 0.999; the accepted port reached 1.0000 on both).
Dimensions where either side is constant are listed and fail the check, since r is undefined there.

Requires numpy. Reads .csv, .tsv and .npy.

Usage:
    python3 parity.py authors_outputs.csv my_outputs.csv --id dataset
    python3 parity.py ref.npy mine.npy --min-r 0.9999
    python3 parity.py ref.csv mine.csv --id name --minmax --report parity.md

Exit code: 0 when the check passes, 1 when it fails, 2 on unusable input.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover
    sys.exit("parity.py needs numpy (pip install numpy)")


def load(path: str, id_col: str | None):
    p = Path(path)
    if p.suffix == ".npy":
        X = np.load(p)
        if X.ndim != 2:
            raise ValueError(f"{path}: expected a 2-D array, got shape {X.shape}")
        return None, [f"d{i}" for i in range(X.shape[1])], X.astype(float)
    delim = "\t" if p.suffix == ".tsv" else ","
    with p.open(newline="") as fh:
        rows = list(csv.reader(fh, delimiter=delim))
    header, body = rows[0], [r for r in rows[1:] if r]
    if id_col is not None:
        if id_col not in header:
            raise ValueError(f"{path}: no column {id_col!r}; columns are {header[:8]}")
        k = header.index(id_col)
        ids = [r[k] for r in body]
        cols = [c for i, c in enumerate(header) if i != k]
        X = np.array([[float(v) for i, v in enumerate(r) if i != k] for r in body])
    else:
        ids = None
        cols = header
        X = np.array([[float(v) for v in r] for r in body])
    return ids, cols, X


def rank(a: np.ndarray) -> np.ndarray:
    """Average ranks (ties share the mean rank), as Spearman needs."""
    order = np.argsort(a, kind="mergesort")
    r = np.empty(len(a), dtype=float)
    r[order] = np.arange(len(a), dtype=float)
    s = a[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    return r


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a - a.mean(), b - b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else float("nan")


def pdist(X: np.ndarray) -> np.ndarray:
    sq = (X * X).sum(1)
    D = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * X @ X.T, 0))
    iu = np.triu_indices(len(X), 1)
    return D[iu]


def minmax(X: np.ndarray) -> np.ndarray:
    lo, hi = X.min(0), X.max(0)
    span = np.where(hi > lo, hi - lo, 1.0)
    return (X - lo) / span


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference", help="the authors' released outputs (.csv, .tsv or .npy)")
    ap.add_argument("mine", help="the reimplementation's outputs, same items and dimensions")
    ap.add_argument("--id", default=None, help="id column used to match rows (CSV/TSV only)")
    ap.add_argument("--min-r", type=float, default=0.999, help="pass threshold for both correlations")
    ap.add_argument("--minmax", action="store_true", help="min-max scale each dimension of both before the "
                    "distance structure and the absolute difference (use when the released outputs were normalized)")
    ap.add_argument("--report", default=None, help="also write the result as markdown to this file")
    a = ap.parse_args()

    try:
        ids_r, cols_r, R = load(a.reference, a.id)
        ids_m, cols_m, M = load(a.mine, a.id)
    except (ValueError, OSError) as e:
        print(f"unusable input: {e}", file=sys.stderr)
        return 2

    if ids_r is not None and ids_m is not None:
        common = [i for i in ids_r if i in set(ids_m)]
        dropped = (len(ids_r) - len(common), len(ids_m) - len(common))
        pos_m = {k: n for n, k in enumerate(ids_m)}
        R = R[[ids_r.index(i) for i in common]]
        M = M[[pos_m[i] for i in common]]
    else:
        dropped = (0, 0)
        if R.shape[0] != M.shape[0]:
            print(f"unusable input: {R.shape[0]} vs {M.shape[0]} rows and no --id to match them", file=sys.stderr)
            return 2
    if R.shape[1] != M.shape[1]:
        print(f"unusable input: {R.shape[1]} reference dimensions vs {M.shape[1]} reimplemented "
              "(a dimension mismatch is itself a finding: check the released code, not the paper)", file=sys.stderr)
        return 2
    n, d = R.shape
    if n < 3:
        print("unusable input: fewer than 3 matched items", file=sys.stderr)
        return 2

    rs = np.array([pearson(R[:, j], M[:, j]) for j in range(d)])
    undefined = [cols_r[j] for j in range(d) if np.isnan(rs[j])]
    A, B = (minmax(R), minmax(M)) if a.minmax else (R, M)
    rho = pearson(rank(pdist(A)), rank(pdist(B)))
    maxabs = float(np.abs(A - B).max())
    worst = int(np.nanargmin(rs)) if not np.all(np.isnan(rs)) else 0
    min_r = float(np.nanmin(rs)) if not np.all(np.isnan(rs)) else float("nan")
    ok = (not undefined) and min_r >= a.min_r and rho >= a.min_r

    lines = [
        f"Parity check: {a.mine} against {a.reference}",
        f"- matched items: {n} (dropped: {dropped[0]} reference-only, {dropped[1]} reimplementation-only)",
        f"- dimensions: {d}",
        f"- per-dimension Pearson r: min {min_r:.4f} (dimension {cols_r[worst]}), median {np.nanmedian(rs):.4f}",
        f"- Spearman of pairwise distances ({n * (n - 1) // 2} pairs): {rho:.4f}",
        f"- largest absolute difference{' after min-max scaling' if a.minmax else ''}: {maxabs:.3g}",
    ]
    if undefined:
        lines.append(f"- r undefined (a constant column) for: {', '.join(undefined[:10])}")
    low = [f"{cols_r[j]} ({rs[j]:.4f})" for j in np.argsort(rs) if not np.isnan(rs[j]) and rs[j] < a.min_r]
    if low:
        lines.append(f"- dimensions below {a.min_r}: {', '.join(low[:10])}{' ...' if len(low) > 10 else ''}")
    lines.append(f"- verdict: {'PASS' if ok else 'FAIL'} at threshold {a.min_r}")
    text = "\n".join(lines)
    print(text)
    if a.report:
        Path(a.report).write_text(text + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Prove that look-alike outputs come from different models, and that two runs scored the same rows.

Ported from a diagnostic written when several model variants produced identical-looking
embedding plots, stripped of project specifics. It answers two questions before any A-vs-B
number is trusted:

1. IDENTITY. Are the arrays distinct? Each input gets a content hash (md5 of the raw bytes, never
   the file name). Two arms with the same hash are the same output, whatever their names say.
2. SIMILARITY. How alike are the representations up to rotation and scale? Linear CKA between
   every pair, computed only on rows joined by key. CKA near 1 between arms that should differ
   means the varied component does not reach this readout; CKA near 0 between arms that should
   match (thin vs dense export of one model, say) means they are not the same checkpoint.

Rows are joined by an explicit key column, never by position. The match rate of every pair is
printed; a pair below --min-match is refused, because a positional or partial join scores the
wrong rows without raising an error.

Inputs: --emb NAME=PATH [NAME=PATH ...]. PATH is a .npy (2-D array) or .npz (array under --key,
default "emb"). Row keys come from NAME=PATH:KEYS where KEYS is a text or CSV file with one key
per row (first column), in the order of the array rows. Without keys, pairs are compared only
when the row counts match and the report says the join is positional.

Dependencies: numpy.

Example:
    python3 checkpoint_identity.py --emb thin=thin.npy:thin_ids.txt dense=dense.npy:dense_ids.txt
"""
from __future__ import annotations

import argparse
import hashlib
import sys

import numpy as np


def load(spec, npz_key):
    name, rest = spec.split("=", 1)
    path, keys = (rest.rsplit(":", 1) + [None])[:2] if ":" in rest else (rest, None)
    arr = np.load(path)
    if path.endswith(".npz"):
        arr = arr[npz_key]
    arr = np.asarray(arr)
    if arr.ndim != 2:
        sys.exit(f"error: {name} is not a 2-D array (shape {arr.shape})")
    ids = None
    if keys:
        with open(keys) as fh:
            ids = [ln.rstrip("\n").split(",")[0] for ln in fh if ln.strip()]
        if ids and not _numeric(ids[0]) and len(ids) == arr.shape[0] + 1:
            ids = ids[1:]                              # header line
        if len(ids) != arr.shape[0]:
            sys.exit(f"error: {name}: {len(ids)} keys for {arr.shape[0]} rows")
        if len(set(ids)) != len(ids):
            sys.exit(f"error: {name}: duplicate row keys; the join would be ambiguous")
    return name, arr, ids


def _numeric(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def h(a):
    return hashlib.md5(np.ascontiguousarray(a).tobytes()).hexdigest()[:12]


def linear_cka(x, y):
    """CKA(X,Y) = ||Xc^T Yc||_F^2 / (||Xc^T Xc||_F ||Yc^T Yc||_F), columns mean-centred.
    Invariant to orthogonal transforms and isotropic scale, so two independently trained spaces
    holding the same information read near 1 where a per-row cosine would read low."""
    xc, yc = x - x.mean(0), y - y.mean(0)
    hsic = np.linalg.norm(xc.T @ yc, "fro") ** 2
    nx, ny = np.linalg.norm(xc.T @ xc, "fro"), np.linalg.norm(yc.T @ yc, "fro")
    return float(hsic / (nx * ny + 1e-12))


def join(a, b):
    """Return (rows_a, rows_b, match_rate, kind)."""
    (_, xa, ia), (_, xb, ib) = a, b
    if ia is not None and ib is not None:
        pos = {k: i for i, k in enumerate(ib)}
        pa = [i for i, k in enumerate(ia) if k in pos]
        pb = [pos[ia[i]] for i in pa]
        return np.array(pa, int), np.array(pb, int), len(pa) / max(len(ia), len(ib)), "key"
    if xa.shape[0] == xb.shape[0]:
        r = np.arange(xa.shape[0])
        return r, r, 1.0, "positional (unverified)"
    return None, None, 0.0, "none"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--emb", nargs="+", required=True, metavar="NAME=PATH[:KEYS]")
    ap.add_argument("--key", default="emb", help="array name inside .npz files")
    ap.add_argument("--min-match", type=float, default=0.95, help="smallest key match rate accepted")
    ap.add_argument("--max-rows", type=int, default=200000, help="subsample joined rows above this (seed 0)")
    a = ap.parse_args(argv)
    items = [load(s, a.key) for s in a.emb]

    print("| arm | rows | dim | content hash | keys |")
    print("|---|---|---|---|---|")
    hashes = {}
    for name, x, ids in items:
        hashes[name] = h(x)
        print(f"| {name} | {x.shape[0]} | {x.shape[1]} | {hashes[name]} | {'yes' if ids else 'no'} |")
    dup = {}
    for n, hv in hashes.items():
        dup.setdefault(hv, []).append(n)
    same = [v for v in dup.values() if len(v) > 1]
    print()
    for grp in same:
        print(f"IDENTICAL CONTENT: {', '.join(grp)} are byte-identical arrays (same output under different names)")
    bad = 0
    print("\n| pair | join | matched rows | match rate | linear CKA |")
    print("|---|---|---|---|---|")
    rng = np.random.default_rng(0)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            pa, pb, rate, kind = join(items[i], items[j])
            pair = f"{items[i][0]} vs {items[j][0]}"
            if pa is None or rate < a.min_match:
                bad += 1
                print(f"| {pair} | {kind} | {0 if pa is None else len(pa)} | {rate:.3f} | refused |")
                continue
            if len(pa) > a.max_rows:
                s = rng.choice(len(pa), a.max_rows, replace=False)
                pa, pb = pa[s], pb[s]
            c = linear_cka(items[i][1][pa].astype(np.float64), items[j][1][pb].astype(np.float64))
            print(f"| {pair} | {kind} | {len(pa)} | {rate:.3f} | {c:.3f} |")
    print()
    if same:
        print("VERDICT: some arms are the same output. Fix the run or the path before comparing them.")
        return 1
    if bad:
        print(f"VERDICT: {bad} pair(s) could not be joined above the match bar; their comparison is not valid.")
        return 1
    print("VERDICT: every arm is a distinct output and every pair joined above the match bar. Read CKA against "
          "what the design predicts (near 1 where the varied part cannot reach this readout).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

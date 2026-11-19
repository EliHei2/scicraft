#!/usr/bin/env python3
"""Measure fold leakage before any model is scored: shared groups, cross-fold neighbours, and the
score a pure-noise representation earns under your folds.

The rule this script enforces comes from a benchmark where a pure-noise embedding, with zero label
information, scored 22 standard deviations above its own grouped-fold value once the folds were
spatial blocks with about half of every unit's neighbours in another fold. A score the noise row
can earn is fabricated, whatever row earns it.

Three checks:
1. GROUPS. Every group (donor, patient, section, source table) must sit in exactly one fold. A
   group present in two folds puts near-duplicates of test rows into training. Ported from the
   leakage helper of that benchmark.
2. NEIGHBOURS (needs x, y). For each unit, the share of its k nearest neighbours (within its
   section, if a section column exists) that sit in another fold. Any feature built by averaging
   neighbours (a niche, a context window, a smoothing step) mixes train and test through them.
3. NOISE PROBE. Draws Gaussian noise features (no label information), optionally averages them
   over the k nearest neighbours (the operator in check 2), and scores them with a kNN classifier
   under your folds, against label-permuted copies of the same pipeline. The noise row must sit at
   chance; its excess over chance, in units of the permuted spread, is printed.

The noise probe stands in for your scorer. A final check runs your own scorer on the noise file
written with --write-noise.

Input CSV columns: fold, label, and optionally group, x, y, section (rename with --fold-col and the
other --*-col options). Units are rows.

Dependencies: numpy; scipy (cKDTree) is used when present for the neighbour search, otherwise a
brute-force search caps the input at 20,000 rows.

Example:
    python3 fold_leakage.py units.csv --k 15 --smooth --repeats 5
    python3 fold_leakage.py units.csv --write-noise noise.npy      # then score noise.npy with your scorer
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys

import numpy as np


def read(path, names):
    """names maps the roles fold, label, group, section, x, y to column names in the file."""
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    cols = set(rows[0]) if rows else set()
    if not rows or not {names["fold"], names["label"]} <= cols:
        sys.exit(f"error: CSV needs at least columns {names['fold']!r} and {names['label']!r}; found {sorted(cols)}")
    out = dict(fold=np.array([r[names["fold"]] for r in rows]), label=np.array([r[names["label"]] for r in rows]))
    for c in ("group", "section"):
        if names[c] in cols:
            out[c] = np.array([r[names[c]] for r in rows])
    if names["x"] in cols and names["y"] in cols:
        out["xy"] = np.array([[float(r[names["x"]]), float(r[names["y"]])] for r in rows])
    return out


def group_leak(group, fold):
    """Units whose group also appears in another fold."""
    g2f = collections.defaultdict(set)
    for g, f in zip(group, fold):
        g2f[g].add(f)
    bad = {g for g, fs in g2f.items() if len(fs) > 1}
    n = int(sum(g in bad for g in group))
    return dict(n_units=n, frac=n / max(1, len(group)), groups_split=sorted(bad), n_groups=len(g2f))


def knn(xy, section, k):
    """Indices of the k nearest neighbours (self included as the first), within section."""
    n = xy.shape[0]
    nb = np.empty((n, k + 1), dtype=np.int64)
    secs = section if section is not None else np.zeros(n, dtype=object)
    try:
        from scipy.spatial import cKDTree
    except ImportError:
        cKDTree = None
        if n > 20000:
            sys.exit("error: more than 20,000 rows needs scipy for the neighbour search")
    for s in np.unique(secs):
        idx = np.flatnonzero(secs == s)
        kk = min(k + 1, idx.size)
        if cKDTree is not None:
            _, j = cKDTree(xy[idx]).query(xy[idx], kk)
            j = np.atleast_2d(j)
        else:
            d = ((xy[idx, None, :] - xy[None, idx, :]) ** 2).sum(-1)
            j = np.argsort(d, axis=1)[:, :kk]
        if kk < k + 1:
            j = np.concatenate([j, np.repeat(j[:, -1:], k + 1 - kk, axis=1)], axis=1)
        nb[idx] = idx[j]
    return nb


def balanced_accuracy(y, p, classes):
    rec = [np.mean(p[y == c] == c) for c in classes if np.any(y == c)]
    return float(np.mean(rec))


def knn_probe(Z, y, fold, k):
    """Leave-one-fold-out kNN classifier (majority vote of k nearest train rows) -> balanced accuracy."""
    classes = np.unique(y)
    pred = np.empty_like(y)
    for f in np.unique(fold):
        te, tr = fold == f, fold != f
        A, B, ya = Z[tr], Z[te], y[tr]
        out = []
        for i in range(0, B.shape[0], 2048):
            d = (B[i:i + 2048, None, :] - A[None, :, :]) ** 2
            j = np.argpartition(d.sum(-1), min(k, A.shape[0] - 1), axis=1)[:, :k]
            votes = ya[j]
            out.extend(collections.Counter(v).most_common(1)[0][0] for v in votes)
        pred[te] = np.array(out)
    return balanced_accuracy(y, pred, classes)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("csv")
    for role in ("fold", "label", "group", "section", "x", "y"):
        ap.add_argument(f"--{role}-col", default=role, help=f"column holding the {role} (default {role!r})")
    ap.add_argument("--k", type=int, default=15, help="neighbours for the smoothing operator and the probe")
    ap.add_argument("--dim", type=int, default=16, help="width of the noise features")
    ap.add_argument("--smooth", action="store_true", help="average noise over k spatial neighbours (needs x, y)")
    ap.add_argument("--repeats", type=int, default=5, help="noise draws and label permutations")
    ap.add_argument("--max-rows", type=int, default=6000, help="subsample rows for the probe (seed 0)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--write-noise", help="write one noise draw (rows x dim, .npy) for your own scorer")
    ap.add_argument("--max-excess-sd", type=float, default=3.0, help="fail when noise exceeds chance by this")
    a = ap.parse_args(argv)
    d = read(a.csv, {r: getattr(a, f'{r}_col') for r in ('fold', 'label', 'group', 'section', 'x', 'y')})
    n = d["fold"].size
    rng = np.random.default_rng(a.seed)
    status = 0
    print(f"units: {n}; folds: {np.unique(d['fold']).size}; classes: {np.unique(d['label']).size}")

    if "group" in d:
        g = group_leak(d["group"], d["fold"])
        print(f"[groups] {g['n_groups']} groups; {len(g['groups_split'])} split across folds; "
              f"{g['n_units']} units ({100 * g['frac']:.1f}%) share a group with another fold")
        if g["groups_split"]:
            print("  split groups: " + ", ".join(g["groups_split"][:10]) + (" ..." if len(g["groups_split"]) > 10 else ""))
            status = 1
    else:
        print("[groups] no group column: cannot check that donors, sections or sources stay in one fold")

    nb = None
    if "xy" in d:
        nb = knn(d["xy"], d.get("section"), a.k)
        cross = (d["fold"][nb[:, 1:]] != d["fold"][:, None]).mean()
        print(f"[neighbours] {100 * cross:.1f}% of each unit's {a.k} nearest neighbours sit in another fold"
              + (" (within section)" if "section" in d else ""))
    elif a.smooth:
        sys.exit("error: --smooth needs x and y columns")

    Z0 = rng.standard_normal((n, a.dim))
    Zs = Z0[nb].mean(1) if (a.smooth and nb is not None) else Z0
    if a.write_noise:
        np.save(a.write_noise, Zs.astype(np.float32))
        print(f"[noise] wrote {a.write_noise} ({n} x {a.dim}{', neighbour-averaged' if a.smooth else ''})")

    sub = rng.choice(n, min(n, a.max_rows), replace=False)
    y, fold = d["label"][sub], d["fold"][sub]
    chance = 1.0 / np.unique(y).size
    real, perm = [], []
    for r in range(a.repeats):
        Z = rng.standard_normal((n, a.dim))
        if a.smooth and nb is not None:
            Z = Z[nb].mean(1)
        real.append(knn_probe(Z[sub], y, fold, a.k))
        perm.append(knn_probe(Z[sub], rng.permutation(y), fold, a.k))
    real, perm = np.array(real), np.array(perm)
    sd = max(perm.std(ddof=1) if perm.size > 1 else 0.0, 1e-9)
    excess = (real.mean() - perm.mean()) / sd
    print(f"[noise probe] kNN (k={a.k}) balanced accuracy on {'neighbour-averaged ' if a.smooth else ''}noise: "
          f"{real.mean():.4f} +/- {real.std(ddof=1) if real.size > 1 else 0:.4f}; "
          f"label-permuted {perm.mean():.4f} +/- {sd:.4f}; uniform chance {chance:.4f}")
    print(f"[noise probe] excess over the permuted control: {excess:+.1f} SD ({a.repeats} draws, {sub.size} rows)")
    if excess > a.max_excess_sd:
        print("VERDICT: LEAK. A representation with no label information beats the permuted control. "
              "Make every fold a whole group, or confine neighbour operators to one fold, before scoring anything.")
        return 1
    if status:
        print("VERDICT: LEAK. Groups are split across folds.")
        return 1
    print("VERDICT: no leakage detected by these checks. Run your own scorer on the noise file to confirm.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Attribute a reference-candidate gap with controlled perturbations of known, measured severity.

Inputs are item vectors in one shared column set (the same representation used for the comparison):
  --reference, --candidate  the two collections (CSV with an id column)
  --variants                perturbed items: id, parent_id, kind, severity, optional measured_severity
                            and tolerance (as written by perturb_tables.py), then the same feature columns; every parent_id must be an id in --reference,
                            --candidate or --parents
  --halves (optional)       two disjoint halves of each parent: parent_id, half, features; gives the noise
                            floor (median distance between the halves of one item)

All vectors are placed in one cleaned, scaled PCA space fitted once on a balanced set of reference and
candidate items (variants are only transformed, never fitted). For each variant it reports:
  displacement            distance from its parent
  disp_rel_noise          displacement / noise floor (how far above resampling noise)
  disp_rel_spread         displacement / median distance between items
  delta_cand, delta_ref   change in distance to the nearest candidate / reference item, in units of the
                          held-out candidate nearest-neighbour distance (< 0 = moved toward that side)
  cos_to_gap              cosine of the displacement with the reference -> candidate mean difference
                          (> 0 = the perturbation points the way the gap points)
and per (kind, severity): medians, the mean pairwise cosine of displacements across parents (direction
agreement), and the largest |measured - requested| severity, flagged above each row's tolerance column
when present (perturb_tables.py writes the kind-specific one) and above --sev-tol otherwise.

Ported from the author's perturbation_table and direction_agreement functions (tabular study), with the
project's catalog replaced by CSV files. Dependencies: numpy, scipy, scikit-learn; imports twosample.py.

Example:
  python3 gap_attribution.py --reference real.csv --candidate synth.csv --variants variants.csv \
      --halves halves.csv --id-col id --out attribution.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.spatial.distance import cdist, pdist

sys.path.insert(0, str(Path(__file__).resolve().parent))
import twosample as ts  # noqa: E402

META = ("parent_id", "kind", "severity", "measured_severity", "tolerance", "half", "seed", "n_rows", "n_cols", "file")


def read_table(path: str, id_col: str, features=None):
    if not Path(path).exists():
        raise FileNotFoundError(f"file not found: {path}")
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"{path}: empty")
    head = list(rows[0])
    if features is None:
        features = [c for c in head if c != id_col and c not in META]
    missing = [c for c in features if c not in head]
    if missing:
        raise ValueError(f"{path}: missing feature columns {missing[:5]}")

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return np.nan
    X = np.array([[num(r[c]) for c in features] for r in rows], dtype=np.float64)
    meta = {c: [r.get(c, "") for r in rows] for c in head if c == id_col or c in META}
    return X, features, meta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--variants", required=True)
    ap.add_argument("--parents", default=None, help="extra parent items not in either collection")
    ap.add_argument("--halves", default=None, help="parent_id, half, features: two disjoint halves per parent")
    ap.add_argument("--id-col", default="id")
    ap.add_argument("--pca-dim", type=int, default=32)
    ap.add_argument("--scaler", choices=["standard", "robust", "none"], default="standard")
    ap.add_argument("--signed-log", action="store_true")
    ap.add_argument("--holdout-frac", type=float, default=0.2)
    ap.add_argument("--sev-tol", type=float, default=0.02,
                    help="flag a kind when |measured - requested| severity exceeds this (rows without a tolerance column)")
    ap.add_argument("--out", default=None, help="per-variant CSV")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    try:
        A, feats, ma = read_table(args.reference, args.id_col)
        B, _, mb = read_table(args.candidate, args.id_col, feats)
        V, _, mv = read_table(args.variants, args.id_col, feats)
        P, _, mp = read_table(args.parents, args.id_col, feats) if args.parents else (np.zeros((0, len(feats))), feats, {args.id_col: []})
        H, _, mh = read_table(args.halves, args.id_col, feats) if args.halves else (None, feats, {})
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for c in ("parent_id", "kind", "severity"):
        if c not in mv:
            print(f"error: --variants needs a {c} column", file=sys.stderr)
            return 2

    cfg = SimpleNamespace(signed_log=args.signed_log, corr_prune=None, scaler=args.scaler, clip=10.0,
                          pca_dim=args.pca_dim, seed=args.seed)
    ra, rb = ts.balanced_fit_rows(len(A), len(B), args.seed)
    space = ts.make_pipeline(cfg).fit(np.vstack([A[ra], B[rb]]))
    ZA, ZB, ZV = space.transform(A), space.transform(B), space.transform(V)
    ZP = space.transform(P) if len(P) else np.zeros((0, ZA.shape[1]))
    lookup = {}
    for Z, ids in ((ZA, ma[args.id_col]), (ZB, mb[args.id_col]), (ZP, mp[args.id_col])):
        for i, k in enumerate(ids):
            lookup.setdefault(k, Z[i])
    orphan = sorted({p for p in mv["parent_id"] if p not in lookup})
    if orphan:
        print(f"error: {len(orphan)} parent ids not found, e.g. {orphan[:5]}", file=sys.stderr)
        return 2

    rng = np.random.default_rng(args.seed + 104729)
    hold = np.zeros(len(B), bool)
    hold[rng.choice(len(B), max(5, int(round(args.holdout_frac * len(B)))), replace=False)] = True
    scale = float(np.median(cdist(ZB[hold], ZB[~hold]).min(1))) or 1.0
    spread = float(np.median(pdist(np.vstack([ZA, ZB]))))
    gap = ZB.mean(0) - ZA.mean(0)   # reference -> candidate
    noise = np.nan
    if H is not None:
        ZH = space.transform(H)
        by = {}
        for i, (p, h) in enumerate(zip(mh.get("parent_id", []), mh.get("half", []))):
            by.setdefault(p, {})[h] = ZH[i]
        d = [np.linalg.norm(v[a] - v[b]) for v in by.values() if len(v) == 2 for a, b in [tuple(sorted(v))]]
        if d:
            noise = float(np.median(d))

    Zpar = np.array([lookup[p] for p in mv["parent_id"]])
    dvec = ZV - Zpar
    disp = np.linalg.norm(dvec, axis=1)
    near = lambda Z, R: cdist(Z, R).min(1) / scale  # noqa: E731
    d_cand = near(ZV, ZB[~hold]) - near(Zpar, ZB[~hold])
    d_ref = near(ZV, ZA) - near(Zpar, ZA)
    cos = (dvec @ gap) / (disp * np.linalg.norm(gap) + 1e-12)
    sev = np.array([float(s) for s in mv["severity"]])
    meas = np.array([float(s) if s not in ("", None) else np.nan for s in mv.get("measured_severity", [""] * len(V))])
    tol = np.array([float(s) if s not in ("", None) else args.sev_tol
                    for s in mv.get("tolerance", [""] * len(V))])

    print(f"{len(V)} variants of {len(set(mv['parent_id']))} parents; space {ZA.shape[1]}-d; "
          f"noise floor {noise:.3f}; median spread {spread:.3f}; distance unit {scale:.3f}")
    print(f"{'kind':<14}{'severity':>9}{'n':>4}{'disp/noise':>12}{'d_cand':>9}{'cos_gap':>9}{'dir_agree':>10}{'|meas-req|':>11}")
    bad = 0
    groups = {}
    for i, key in enumerate(zip(mv["kind"], sev)):
        groups.setdefault(key, []).append(i)
    for (kind, s), idx in sorted(groups.items()):
        idx = np.array(idx)
        dv = dvec[idx]
        nrm = np.linalg.norm(dv, axis=1)
        u = dv[nrm > 1e-9] / nrm[nrm > 1e-9, None]
        agree = float((u @ u.T)[np.triu_indices(len(u), 1)].mean()) if len(u) >= 2 else np.nan
        dev = np.nanmax(np.abs(meas[idx] - s)) if np.isfinite(meas[idx]).any() else np.nan
        over = np.abs(meas[idx] - s) > tol[idx] + 1e-12
        flag = " FLAG" if np.isfinite(dev) and over.any() else ""
        bad += bool(flag)
        rel = np.median(disp[idx]) / noise if np.isfinite(noise) and noise > 0 else np.nan
        print(f"{kind:<14}{s:>9.3g}{len(idx):>4}{rel:>12.2f}{np.median(d_cand[idx]):>9.3f}"
              f"{np.mean(cos[idx]):>9.3f}{agree:>10.3f}{dev:>11.3g}{flag}")
    if args.out:
        with open(args.out, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "parent_id", "kind", "severity", "measured_severity", "displacement",
                        "disp_rel_noise", "disp_rel_spread", "delta_cand", "delta_ref", "cos_to_gap"])
            for i in range(len(V)):
                w.writerow([mv[args.id_col][i], mv["parent_id"][i], mv["kind"][i], sev[i], meas[i], disp[i],
                            disp[i] / noise if np.isfinite(noise) and noise > 0 else "", disp[i] / spread,
                            d_cand[i], d_ref[i], cos[i]])
        print(f"wrote {args.out}")
    if bad:
        print(f"error: {bad} kind/severity cells deliver a severity other than requested (beyond tolerance); "
              "fix the perturbation before reading its displacement", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

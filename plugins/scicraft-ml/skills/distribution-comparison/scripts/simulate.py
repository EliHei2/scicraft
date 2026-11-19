#!/usr/bin/env python3
"""Calibrate the two-sample battery on Gaussian data where the answer is known.

Draws N reference items from a standard Gaussian in d dimensions and M candidate items that are either
identical in distribution (null), shifted along one axis by s SD, or contracted by a factor c on every
axis (the narrow-candidate case). For each scenario it reports the mean linear and random-forest C2ST AUC,
the rejection rate of the energy and MMD permutation tests at alpha, mean precision / recall / density /
coverage at matched sizes, and the share of reference items flagged out of support.

Use it before trusting a battery on your own sizes: run with your N, M and d and read what each metric
does when there is no difference and when there is one you can name.

--selftest runs a small fixed grid and asserts the known answers (exit 1 on any failure):
  null: AUCs near 0.5, energy rejection rate low, out-of-support share near 0.05;
  contraction x0.7: linear AUC near 0.5 while forest AUC, energy and MMD detect it;
  shift 1 SD: every test detects it; the analytic coverage null matches simulated coverage.

Dependencies: numpy, scipy, scikit-learn; imports twosample.py from the same folder.

Examples:
  python3 simulate.py --n-ref 100 --n-cand 500 --dim 16 --reps 20
  python3 simulate.py --selftest
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import twosample as ts  # noqa: E402

SCENARIOS = {"null": ("none", 0.0), "shift_0.5sd": ("shift", 0.5), "shift_1sd": ("shift", 1.0),
             "contract_0.85": ("contract", 0.85), "contract_0.7": ("contract", 0.7),
             "contract_0.5": ("contract", 0.5)}


def draw(kind: str, s: float, n: int, m: int, d: int, rng: np.random.Generator):
    A = rng.standard_normal((n, d))
    B = rng.standard_normal((m, d))
    if kind == "shift":
        B[:, 0] += s
    elif kind == "contract":
        B *= s
    return A, B


def run_one(A, B, args, seed: int, c2st: bool) -> dict:
    cfg = SimpleNamespace(signed_log=False, corr_prune=None, scaler="standard", clip=10.0, pca_dim=args.dim,
                          seed=seed, folds=5, jobs=args.jobs)
    ra, rb = ts.balanced_fit_rows(len(A), len(B), seed)
    space = ts.make_pipeline(cfg).fit(np.vstack([A[ra], B[rb]]))
    ZA, ZB = space.transform(A), space.transform(B)
    out = {}
    if c2st:
        X = np.vstack([A, B])
        lab = np.r_[np.ones(len(A)), np.zeros(len(B))].astype(int)
        out["lr_auc"] = ts.c2st(X, lab, cfg, "logreg", repeats=1, n_boot=50)["auc"]
        out["rf_auc"] = ts.c2st(X, lab, cfg, "rf", repeats=1, n_boot=50)["auc"]
    e = ts.energy_test(ZA, ZB, args.n_perm, seed)
    k = ts.mmd_test(ZA, ZB, args.n_perm, seed)
    out["energy_reject"] = float(e["energy_p"] < args.alpha)
    out["mmd_reject"] = float(k["mmd_p"] < args.alpha)
    out["energy_z"] = e["energy_z"]
    out.update({key: v for key, v in ts.prdc_balanced(ZA, ZB, 5, reps=3, seed=seed).items()
                if key in ("precision", "recall", "density", "coverage", "coverage_null")})
    hold = np.zeros(len(B), bool)
    hold[np.random.default_rng(seed + 1).choice(len(B), max(5, len(B) // 5), replace=False)] = True
    out["frac_oos"] = ts.nearest_reference_distance(ZA, ZB[~hold], ZB[hold])["frac_out_of_support"]
    return out


def grid(args, names, c2st=True) -> dict:
    table = {}
    for name in names:
        kind, s = SCENARIOS[name]
        rows = []
        for r in range(args.reps):
            # stable per-scenario seed: hash() of a string changes with PYTHONHASHSEED
            rng = np.random.default_rng(args.seed + 1000 * r + list(SCENARIOS).index(name))
            A, B = draw(kind, s, args.n_ref, args.n_cand, args.dim, rng)
            rows.append(run_one(A, B, args, args.seed + r, c2st))
        table[name] = {k: float(np.mean([row[k] for row in rows])) for k in rows[0]}
    return table


def show(table: dict, args) -> None:
    keys = list(next(iter(table.values())))
    print(f"N={args.n_ref} reference vs M={args.n_cand} candidate, d={args.dim}, {args.reps} reps, "
          f"{args.n_perm} permutations, alpha={args.alpha}")
    print(f"{'scenario':<15}" + "".join(f"{k:>14}" for k in keys))
    for name, row in table.items():
        print(f"{name:<15}" + "".join(f"{row[k]:>14.3f}" for k in keys))


def selftest(args) -> int:
    args.n_ref, args.n_cand, args.dim, args.reps, args.n_perm = 100, 500, 16, 6, 200
    t = grid(args, ["null", "shift_1sd", "contract_0.7"])
    show(t, args)
    checks = [
        ("null: linear AUC within 0.40 to 0.60", 0.40 <= t["null"]["lr_auc"] <= 0.60),
        ("null: forest AUC within 0.40 to 0.60", 0.40 <= t["null"]["rf_auc"] <= 0.60),
        ("null: energy rejection rate at most 0.34 (6 reps)", t["null"]["energy_reject"] <= 0.34),
        ("null: out-of-support share within 0.00 to 0.15", t["null"]["frac_oos"] <= 0.15),
        ("null: precision and recall below 0.95 (not 1 at no difference)",
         t["null"]["precision"] < 0.95 and t["null"]["recall"] < 0.95),
        ("null: simulated coverage within 0.05 of the analytic null",
         abs(t["null"]["coverage"] - t["null"]["coverage_null"]) <= 0.05),
        ("contract 0.7: linear AUC below 0.60 (blind)", t["contract_0.7"]["lr_auc"] < 0.60),
        ("contract 0.7: forest AUC above 0.70", t["contract_0.7"]["rf_auc"] > 0.70),
        ("contract 0.7: energy rejects in every rep", t["contract_0.7"]["energy_reject"] == 1.0),
        ("contract 0.7: MMD rejects in every rep", t["contract_0.7"]["mmd_reject"] == 1.0),
        ("contract 0.7: recall falls below the null recall", t["contract_0.7"]["recall"] < t["null"]["recall"]),
        ("contract 0.7: density above 1.5", t["contract_0.7"]["density"] > 1.5),
        ("shift 1 SD: energy and MMD reject in every rep",
         t["shift_1sd"]["energy_reject"] == 1.0 and t["shift_1sd"]["mmd_reject"] == 1.0),
        ("shift 1 SD: linear AUC above 0.65", t["shift_1sd"]["lr_auc"] > 0.65),
    ]
    bad = 0
    for text, ok in checks:
        print(("PASS " if ok else "FAIL ") + text)
        bad += not ok
    print(f"{len(checks) - bad}/{len(checks)} checks passed")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-ref", type=int, default=100)
    ap.add_argument("--n-cand", type=int, default=500)
    ap.add_argument("--dim", type=int, default=16)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--scenarios", default=",".join(SCENARIOS), help=f"comma list from {list(SCENARIOS)}")
    ap.add_argument("--no-c2st", action="store_true", help="skip classifiers (fast)")
    ap.add_argument("--jobs", type=int, default=-1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest(args)
    names = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    unknown = [s for s in names if s not in SCENARIOS]
    if unknown:
        print(f"error: unknown scenarios {unknown}", file=sys.stderr)
        return 2
    show(grid(args, names, not args.no_c2st), args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

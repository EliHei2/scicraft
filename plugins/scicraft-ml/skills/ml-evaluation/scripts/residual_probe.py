#!/usr/bin/env python3
"""Does a learned representation carry signal beyond a cheap baseline? Regress the baseline out and
test what is left.

Pattern ported from a residual-correlation check written for a self-supervised model whose training
levers all pushed toward the subspace of a static linear baseline. A gap "model minus baseline",
computed as two separate scalars, cannot tell a new subspace from the same subspace recovered a
little better. Residualizing the baseline out of the representation and scoring the residual can:
if the residual scores at its row-shuffled null, the representation adds nothing on this task, and
no win is reported however healthy the training curves look.

Arms, all through one linear probe and the same grouped folds:
  baseline      the baseline features alone (PCA of raw inputs, ridge on raw columns, a GBDT's
                predictions, a training-free neighbour mean)
  embedding     the representation alone
  concat        baseline and representation side by side; if it equals baseline, the
                representation is redundant on this task
  residual      the representation after the baseline is regressed out (OLS fitted on the train
                fold, applied to both folds)
  residual_null the residual arm with the target permuted within the train fold (the floor)

The probe is ridge regression for a numeric target, or a one-vs-rest least-squares classifier for
a categorical one (balanced accuracy). Features are standardised on the train fold. Leave-one-
group-out folds come from the group column.

Inputs: --emb (.npy, rows x d), --baseline (.npy, rows x b), --meta (CSV with columns target and
group, one row per array row, same order). Arrays must already be aligned by key; checkpoint_identity.py
checks the join.

Dependencies: numpy.

Example:
    python3 residual_probe.py --emb model.npy --baseline pca64.npy --meta rows.csv --task classification
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

import numpy as np


def standardise(tr, te):
    mu, sd = tr.mean(0), tr.std(0)
    sd[sd < 1e-9] = 1.0
    return (tr - mu) / sd, (te - mu) / sd


def residualize(Btr, Bte, Ztr, Zte):
    """Remove the span of the baseline (plus an intercept) from Z; coefficients fitted on train only."""
    Dtr = np.column_stack([np.ones(len(Btr)), Btr])
    Dte = np.column_stack([np.ones(len(Bte)), Bte])
    coef, *_ = np.linalg.lstsq(Dtr, Ztr, rcond=None)
    return Ztr - Dtr @ coef, Zte - Dte @ coef


def ridge_fit_predict(Xtr, Ytr, Xte, lam):
    Xtr, Xte = standardise(Xtr, Xte)
    A = Xtr.T @ Xtr + lam * len(Xtr) * np.eye(Xtr.shape[1])
    W = np.linalg.solve(A, Xtr.T @ (Ytr - Ytr.mean(0)))
    return Xte @ W + Ytr.mean(0)


def score_fold(Xtr, ytr, Xte, yte, task, classes, lam):
    if task == "regression":
        p = ridge_fit_predict(Xtr, ytr[:, None], Xte, lam)[:, 0]
        ss = ((yte - yte.mean()) ** 2).sum()
        return float(1 - ((yte - p) ** 2).sum() / ss) if ss > 0 else float("nan")
    Y = (ytr[:, None] == classes[None, :]).astype(float)
    p = classes[np.argmax(ridge_fit_predict(Xtr, Y, Xte, lam), 1)]
    rec = [np.mean(p[yte == c] == c) for c in classes if np.any(yte == c)]
    return float(np.mean(rec))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--emb", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--meta", required=True, help="CSV with columns target, group")
    ap.add_argument("--task", choices=["classification", "regression"], required=True)
    ap.add_argument("--lam", type=float, default=1e-2, help="ridge strength (per row)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    Z, B = np.load(a.emb).astype(np.float64), np.load(a.baseline).astype(np.float64)
    with open(a.meta, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not (len(rows) == len(Z) == len(B)):
        sys.exit(f"error: row counts differ (meta {len(rows)}, emb {len(Z)}, baseline {len(B)})")
    if B.ndim == 1:
        B = B[:, None]
    grp = np.array([r["group"] for r in rows])
    y = np.array([float(r["target"]) for r in rows]) if a.task == "regression" else np.array([r["target"] for r in rows])
    classes = np.unique(y) if a.task == "classification" else None
    rng = np.random.default_rng(a.seed)
    arms = {k: [] for k in ("baseline", "embedding", "concat", "residual", "residual_null")}
    groups = np.unique(grp)
    if groups.size < 2:
        sys.exit("error: need at least two groups for leave-one-group-out folds")
    for g in groups:
        te, tr = grp == g, grp != g
        Rtr, Rte = residualize(B[tr], B[te], Z[tr], Z[te])
        sets = dict(baseline=(B[tr], B[te]), embedding=(Z[tr], Z[te]),
                    concat=(np.hstack([B[tr], Z[tr]]), np.hstack([B[te], Z[te]])), residual=(Rtr, Rte))
        for k, (xtr, xte) in sets.items():
            arms[k].append(score_fold(xtr, y[tr], xte, y[te], a.task, classes, a.lam))
        arms["residual_null"].append(score_fold(Rtr, rng.permutation(y[tr]), Rte, y[te], a.task, classes, a.lam))
    metric = "R^2" if a.task == "regression" else "balanced accuracy"
    print(f"{groups.size} leave-one-group-out folds; metric: {metric}; ridge lambda {a.lam}")
    print("| arm | median over folds | SD | folds |")
    print("|---|---|---|---|")
    summ = {}
    for k, v in arms.items():
        v = np.array(v)
        summ[k] = dict(median=float(np.nanmedian(v)), sd=float(np.nanstd(v, ddof=1)) if v.size > 1 else None,
                       per_fold=[float(x) for x in v])
        sd = f"{summ[k]['sd']:.4f}" if summ[k]["sd"] is not None else "n/a"
        print(f"| {k} | {summ[k]['median']:.4f} | {sd} | {v.size} |")
    beyond = np.array(arms["residual"]) - np.array(arms["residual_null"])
    added = np.array(arms["concat"]) - np.array(arms["baseline"])
    print(f"\nresidual minus its null, per fold: median {np.median(beyond):+.4f}, positive in "
          f"{int((beyond > 0).sum())} of {beyond.size} folds")
    print(f"concat minus baseline, per fold: median {np.median(added):+.4f}, positive in "
          f"{int((added > 0).sum())} of {added.size} folds")
    print("Test these per-fold differences with paired_folds.py before calling either one a gain.")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(task=a.task, metric=metric, arms=summ), fh, indent=1)
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

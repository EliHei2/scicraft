#!/usr/bin/env python3
"""Compare two collections of items, every number beside its same-size baseline.

Each input is a matrix with one row per item (a table summarized as a vector, an image or document
embedding, a sample of a cohort) and the same columns in both files. The script runs, for the observed
pair and for two no-difference baselines at matched sizes (reference halves, candidate halves):

  - classifier two-sample tests with a linear (logistic regression) and a non-linear (random forest)
    classifier; cleaning and PCA are refit inside every training fold; out-of-fold ROC AUC with a
    stratified bootstrap interval, the spread over repeats and balanced accuracy;
  - energy distance and unbiased MMD^2 (RBF kernel, pooled median bandwidth), each with a label
    permutation p value p = (1 + C) / (1 + B) and a z-score against the permutation null;
  - precision, recall, density and coverage with the candidate subsampled to the reference size and
    averaged over draws, the analytic coverage null and a saturation flag, recall at extra k;
  - for the observed pair: each reference item's distance to its nearest candidate item, in units of the
    median nearest-neighbour distance of held-out candidate items, and an out-of-support flag above the
    held-out 95th percentile.

Distances, PRDC and nearest-reference distances are computed in one cleaned, scaled PCA space fitted
once on a balanced set (all of the smaller side plus an equal-sized seeded subset of the larger, at least
30), so the larger side does not define the axes. `--fit pooled` fits on all items without labels.

Ported from the author's analysis module of a tabular foundation-model study (functions c2st, mmd_test,
energy_test, prdc, prdc_balanced, prior_distance, comparisons, balanced_ref, ViewCleaner), with the
project's data model replaced by two matrices.

Dependencies: numpy, scipy, scikit-learn. Python 3.9 or later.

Examples:
  python3 twosample.py --reference real.csv --candidate synth.csv --out result.json
  python3 twosample.py --reference test.npy --candidate train.npy --quick --per-item items.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist, pdist
from scipy.stats import rankdata
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline


# ---------------------------------------------------------------------------
# preprocessing (fitted once for distances, refit inside every fold for classifiers)
# ---------------------------------------------------------------------------


class Cleaner(BaseEstimator, TransformerMixin):
    """Optional signed log, drop sparse / constant / near-duplicate columns, impute, scale, clip."""

    def __init__(self, slog: bool = False, max_nan_frac: float = 0.3, corr_prune=None,
                 scaler: str = "standard", clip: float = 10.0):
        self.slog = slog
        self.max_nan_frac = max_nan_frac
        self.corr_prune = corr_prune
        self.scaler = scaler
        self.clip = clip

    def _pre(self, X) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64).copy()
        X[~np.isfinite(X)] = np.nan
        return np.sign(X) * np.log1p(np.abs(X)) if self.slog else X

    def fit(self, X, y=None):
        Z = self._pre(X)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            keep = np.isnan(Z).mean(0) <= self.max_nan_frac
            med = np.nanmedian(Z, axis=0)
            med = np.where(np.isfinite(med), med, 0.0)
            Zi = np.where(np.isnan(Z), med, Z)
            sd = Zi.std(0)
        keep &= sd > 1e-9
        idx = np.flatnonzero(keep)
        if self.corr_prune is not None and idx.size > 1:
            C = np.abs(np.corrcoef(Zi[:, idx], rowvar=False))
            np.fill_diagonal(C, 0)
            drop = set()
            for a in range(idx.size):
                if a in drop:
                    continue
                drop.update(int(b) for b in np.flatnonzero(C[a] > self.corr_prune) if b > a)
            idx = np.array([c for k, c in enumerate(idx) if k not in drop], dtype=int)
        if idx.size == 0:
            raise ValueError("no usable column left after cleaning (all sparse or constant)")
        self.idx_ = idx
        self.med_ = med[idx]
        Zs = Zi[:, idx]
        if self.scaler == "robust":
            q75, q25 = np.percentile(Zs, [75, 25], axis=0)
            scale = (q75 - q25) / 1.349
            scale = np.where(scale > 1e-9, scale, Zs.std(0))
            self.center_ = np.median(Zs, 0)
        elif self.scaler == "standard":
            scale, self.center_ = Zs.std(0), Zs.mean(0)
        else:
            scale, self.center_ = np.ones(idx.size), np.zeros(idx.size)
        self.scale_ = np.where(scale > 1e-9, scale, 1.0)
        return self

    def transform(self, X) -> np.ndarray:
        Z = self._pre(X)[:, self.idx_]
        Z = np.where(np.isnan(Z), self.med_, Z)
        Z = (Z - self.center_) / self.scale_
        return np.clip(Z, -self.clip, self.clip) if self.clip else Z


class AutoPCA(BaseEstimator, TransformerMixin):
    """PCA to min(n_components, n_features, n_samples - 1) dimensions."""

    def __init__(self, n_components: int = 32, seed: int = 0):
        self.n_components = n_components
        self.seed = seed

    def fit(self, X, y=None):
        k = int(max(1, min(self.n_components, X.shape[1], X.shape[0] - 1)))
        self.pca_ = PCA(n_components=k, random_state=self.seed).fit(X)
        return self

    def transform(self, X):
        return self.pca_.transform(X)


def make_pipeline(args) -> Pipeline:
    clean = Cleaner(slog=args.signed_log, corr_prune=args.corr_prune, scaler=args.scaler, clip=args.clip)
    return Pipeline([("clean", clean), ("pca", AutoPCA(args.pca_dim, args.seed))])


def balanced_fit_rows(n_a: int, n_b: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """All of the smaller side plus an equal-sized (min 30) seeded subset of the larger side."""
    rng = np.random.default_rng(seed)
    if n_a <= n_b:
        k = min(n_b, max(n_a, 30))
        return np.arange(n_a), np.sort(rng.choice(n_b, k, replace=False))
    k = min(n_a, max(n_b, 30))
    return np.sort(rng.choice(n_a, k, replace=False)), np.arange(n_b)


# ---------------------------------------------------------------------------
# two-sample statistics
# ---------------------------------------------------------------------------


def _median_bandwidth(Z: np.ndarray) -> float:
    d = pdist(Z)
    return float(np.median(d[d > 0])) if (d > 0).any() else 1.0


def _perm_indicators(n: int, m: int, n_perm: int, seed: int) -> np.ndarray:
    """(n+m, 1+n_perm) group-A indicators: column 0 is the observed split, the rest are label permutations."""
    rng = np.random.default_rng(seed)
    lab = np.r_[np.ones(n), np.zeros(m)]
    return np.column_stack([lab] + [rng.permutation(lab) for _ in range(n_perm)])


def _two_sample_sums(K: np.ndarray, I: np.ndarray):
    """Sums of K within A, within B and across, for every indicator column at once (one matrix product)."""
    J = 1.0 - I
    KI, KJ = K @ I, K @ J
    return (I * KI).sum(0), (J * KJ).sum(0), (I * KJ).sum(0)


def _p_and_z(stat: np.ndarray) -> tuple[float, float, float]:
    obs, null = stat[0], stat[1:]
    p = float((1 + (null >= obs).sum()) / (1 + len(null)))
    z = float((obs - null.mean()) / (null.std() + 1e-12))
    return float(obs), p, z


def mmd_test(A: np.ndarray, B: np.ndarray, n_perm: int = 1000, seed: int = 0) -> dict:
    """Unbiased MMD^2 (RBF kernel, pooled median-heuristic bandwidth) with a permutation p value and z."""
    Z = np.vstack([A, B])
    n, m = len(A), len(B)
    s = _median_bandwidth(Z)
    K = np.exp(-cdist(Z, Z, "sqeuclidean") / (2 * s ** 2))
    np.fill_diagonal(K, 0.0)  # unbiased: drop i == j terms
    saa, sbb, sab = _two_sample_sums(K, _perm_indicators(n, m, n_perm, seed))
    obs, p, z = _p_and_z(saa / (n * (n - 1)) + sbb / (m * (m - 1)) - 2 * sab / (n * m))
    return {"mmd2": obs, "mmd_p": p, "mmd_z": z}


def energy_test(A: np.ndarray, B: np.ndarray, n_perm: int = 1000, seed: int = 0) -> dict:
    """Energy distance 2E|X-Y| - E|X-X'| - E|Y-Y'| with a permutation p value and z."""
    Z = np.vstack([A, B])
    n, m = len(A), len(B)
    D = cdist(Z, Z)
    saa, sbb, sab = _two_sample_sums(D, _perm_indicators(n, m, n_perm, seed + 1))
    obs, p, z = _p_and_z(2 * sab / (n * m) - saa / (n * (n - 1)) - sbb / (m * (m - 1)))
    return {"energy": obs, "energy_p": p, "energy_z": z}


def prdc(ref: np.ndarray, cand: np.ndarray, k: int = 5) -> dict:
    """kNN precision / recall (Kynkaanniemi 2019) and density / coverage (Naeem 2020); ref = reference."""
    k = max(1, min(k, len(ref) - 1, len(cand) - 1))
    r_rad = np.sort(cdist(ref, ref), axis=1)[:, k]
    c_rad = np.sort(cdist(cand, cand), axis=1)[:, k]
    D = cdist(ref, cand)
    return {"precision": float((D < r_rad[:, None]).any(0).mean()),
            "recall": float((D < c_rad[None, :]).any(1).mean()),
            "density": float((D < r_rad[:, None]).sum(0).mean() / k),
            "coverage": float((D.min(1) < r_rad).mean())}


def coverage_null(n_ref: int, n_cand: int, k: int) -> float:
    """Expected coverage under identical distributions: 1 - prod_{i=1..k} (N - i) / (M + N - i) (Naeem 2020)."""
    return float(1 - np.prod([(n_ref - i) / (n_cand + n_ref - i) for i in range(1, k + 1)]))


def prdc_balanced(ref: np.ndarray, cand: np.ndarray, k: int = 5, reps: int = 10, seed: int = 0,
                  extra_k=(3, 10)) -> dict:
    """PRDC with both sides subsampled to the smaller size, averaged over draws; recall at extra k."""
    rng = np.random.default_rng(seed)
    n = min(len(ref), len(cand))
    res = []
    for _ in range(reps):
        r = ref if len(ref) == n else ref[rng.choice(len(ref), n, replace=False)]
        c = cand if len(cand) == n else cand[rng.choice(len(cand), n, replace=False)]
        row = prdc(r, c, k)
        for kk in extra_k:
            row[f"recall_k{kk}"] = prdc(r, c, kk)["recall"]
        res.append(row)
    out = {key: float(np.mean([r[key] for r in res])) for key in res[0]}
    out["prdc_n"] = n
    out["coverage_null"] = coverage_null(n, n, k)
    out["coverage_saturated"] = bool(out["coverage_null"] >= 0.99)
    return out


def fast_auc(y: np.ndarray, p: np.ndarray) -> float:
    """ROC AUC via the Mann-Whitney rank identity (ties get average ranks)."""
    r = rankdata(p)
    n1 = int(y.sum())
    n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")


def c2st(X: np.ndarray, label: np.ndarray, args, model: str = "logreg", repeats: int = 5,
         n_boot: int = 1000) -> dict:
    """Classifier two-sample test: out-of-fold ROC AUC, preprocessing refit inside every fold, bootstrap CI."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score
    from sklearn.model_selection import StratifiedKFold
    if model == "logreg":
        clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000)
    else:
        clf = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced",
                                     n_jobs=args.jobs, random_state=args.seed)
    n_min = int(min((label == 0).sum(), (label == 1).sum()))
    folds = max(2, min(args.folds, n_min))
    probs = np.zeros((repeats, len(label)))
    rep_auc = []
    for r in range(repeats):
        skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=args.seed + r)
        for tr, te in skf.split(X, label):
            pipe = Pipeline([*make_pipeline(args).steps, ("clf", clone(clf))])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pipe.fit(X[tr], label[tr])
            probs[r, te] = pipe.predict_proba(X[te])[:, 1]
        rep_auc.append(fast_auc(label, probs[r]))
    p = probs.mean(0)
    auc = fast_auc(label, p)
    rng = np.random.default_rng(args.seed)
    i0, i1 = np.flatnonzero(label == 0), np.flatnonzero(label == 1)
    boots = [fast_auc(label[np.r_[a, b]], p[np.r_[a, b]])
             for a, b in ((rng.choice(i0, i0.size), rng.choice(i1, i1.size)) for _ in range(n_boot))] or [auc]
    return {"auc": auc, "auc_lo": float(np.quantile(boots, 0.025)), "auc_hi": float(np.quantile(boots, 0.975)),
            "auc_sd_repeats": float(np.std(rep_auc)), "bal_acc": float(balanced_accuracy_score(label, p > 0.5)),
            "folds": folds, "repeats": repeats, "oof_prob": p}


def c2st_permutation_p(X: np.ndarray, label: np.ndarray, args, observed: float, n_perm: int) -> float:
    """Label-permutation p value for the linear C2ST AUC: the whole CV pipeline is rerun per permutation."""
    rng = np.random.default_rng(args.seed + 31337)
    null = [c2st(X, rng.permutation(label), args, "logreg", repeats=1, n_boot=0)["auc"] for _ in range(n_perm)]
    return float((1 + (np.array(null) >= observed).sum()) / (1 + n_perm))


def nearest_reference_distance(Zr: np.ndarray, Zc_ref: np.ndarray, Zc_hold: np.ndarray, q: float = 0.95) -> dict:
    """Nearest-candidate distances of reference items, in units of the held-out candidate NN distance."""
    d_ref = cdist(Zr, Zc_ref).min(1)
    d_hold = cdist(Zc_hold, Zc_ref).min(1)
    scale = float(np.median(d_hold)) or 1.0
    thr = float(np.quantile(d_hold / scale, q))
    return {"d_ref": d_ref / scale, "d_hold": d_hold / scale, "threshold": thr,
            "median_rel_nn": float(np.median(d_ref / scale)),
            "frac_out_of_support": float((d_ref / scale > thr).mean())}


def comparisons(n_a: int, n_b: int, seed: int) -> dict:
    """Observed pair plus two no-difference baselines.

    cand_halves mirrors the observed sample sizes (N vs M): its first part has min(N, M // 2) items and its
    second part the rest, so its values are the 'no gap' level every observed number is read against.
    """
    rng = np.random.default_rng(seed + 7919)
    comps = {"observed": (("ref", np.arange(n_a)), ("cand", np.arange(n_b)))}
    r = rng.permutation(n_a)
    if n_a >= 8:
        comps["ref_halves"] = (("ref", r[: n_a // 2]), ("ref", r[n_a // 2:]))
    c = rng.permutation(n_b)
    n = min(n_a, n_b // 2)
    if n >= 4:
        comps["cand_halves"] = (("cand", c[:n]), ("cand", c[n:]))
    return comps


# ---------------------------------------------------------------------------
# input / output
# ---------------------------------------------------------------------------


def load_matrix(path: str, id_col):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"file not found: {path}")
    if p.suffix == ".npy":
        X = np.load(p).astype(np.float64)
        if X.ndim != 2:
            raise ValueError(f"{path}: expected a 2-D array, got shape {X.shape}")
        return X, [f"c{j}" for j in range(X.shape[1])], [str(i) for i in range(len(X))]
    with open(p, newline="") as fh:
        rows = list(csv.reader(fh))
    if len(rows) < 2:
        raise ValueError(f"{path}: needs a header and at least one row")
    head, body = rows[0], rows[1:]
    ids = [str(i) for i in range(len(body))]
    if id_col is not None:
        if id_col not in head:
            raise ValueError(f"{path}: id column {id_col!r} not in header")
        j = head.index(id_col)
        ids = [r[j] for r in body]
    cols, data = [], []
    for j, name in enumerate(head):
        if name == id_col:
            continue
        vals = []
        for r in body:
            v = r[j].strip() if j < len(r) else ""
            try:
                vals.append(float(v) if v not in ("", "NA", "nan", "NaN") else np.nan)
            except ValueError:
                vals = None
                break
        if vals is not None:
            cols.append(name)
            data.append(vals)
    if not cols:
        raise ValueError(f"{path}: no numeric column")
    return np.array(data, dtype=np.float64).T, cols, ids


def cap_rows(X: np.ndarray, ids: list, cap: int, seed: int, side: str):
    if cap and len(X) > cap:
        idx = np.sort(np.random.default_rng(seed).choice(len(X), cap, replace=False))
        print(f"note: {side} subsampled from {len(X)} to {cap} items (seed {seed})", file=sys.stderr)
        return X[idx], [ids[i] for i in idx]
    return X, ids


def fmt(v) -> str:
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, float):
        return "nan" if not np.isfinite(v) else (f"{v:.3g}" if abs(v) < 1e-3 and v != 0 else f"{v:.3f}")
    return str(v)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="Read every observed number against the ref_halves and cand_halves columns.")
    ap.add_argument("--reference", required=True, help="CSV or .npy, one row per item (the real or target side)")
    ap.add_argument("--candidate", required=True, help="CSV or .npy, same columns (synthetic, prior, train side)")
    ap.add_argument("--id-col", default=None, help="CSV column holding item ids (excluded from features)")
    ap.add_argument("--out", default=None, help="write all results as JSON here")
    ap.add_argument("--per-item", default=None, help="write per-item out-of-fold P(reference) and distances (CSV)")
    ap.add_argument("--quick", action="store_true", help="screening profile: 3 repeats, 200 permutations, 500 boots")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--repeats", type=int, default=5, help="repeated stratified CV for the linear C2ST")
    ap.add_argument("--n-perm", type=int, default=1000, help="permutations for energy and MMD (200 to screen)")
    ap.add_argument("--n-boot", type=int, default=1000, help="stratified bootstrap draws for the AUC interval")
    ap.add_argument("--k", type=int, default=5, help="neighbours for PRDC")
    ap.add_argument("--prdc-reps", type=int, default=10)
    ap.add_argument("--pca-dim", type=int, default=32)
    ap.add_argument("--scaler", choices=["standard", "robust", "none"], default="standard",
                    help="robust (median, IQR/1.349) for hand-crafted summary statistics")
    ap.add_argument("--signed-log", action="store_true", help="sign(x)*log1p(|x|) first (heavy-tailed statistics)")
    ap.add_argument("--corr-prune", type=float, default=None, help="drop one of each pair with |r| above this")
    ap.add_argument("--clip", type=float, default=10.0)
    ap.add_argument("--fit", choices=["balanced", "pooled"], default="balanced",
                    help="rows the distance space is fitted on (pooled = all items, labels unused)")
    ap.add_argument("--holdout-frac", type=float, default=0.2,
                    help="share of candidate items held out to calibrate nearest-reference distance")
    ap.add_argument("--max-per-side", type=int, default=3000, help="seeded subsample cap per side (0 = none)")
    ap.add_argument("--no-c2st", action="store_true", help="skip the classifier tests")
    ap.add_argument("--c2st-perm", type=int, default=0,
                    help="label permutations for a linear C2ST p value (observed pair only; 200 to screen)")
    ap.add_argument("--jobs", type=int, default=1, help="random forest n_jobs")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    if args.quick:
        args.repeats, args.n_perm, args.n_boot = 3, 200, 500

    try:
        A, cols_a, ids_a = load_matrix(args.reference, args.id_col)
        B, cols_b, ids_b = load_matrix(args.candidate, args.id_col)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    common = [c for c in cols_a if c in set(cols_b)]
    if not common:
        print("error: the two files share no numeric column", file=sys.stderr)
        return 2
    dropped = sorted(set(cols_a) ^ set(cols_b))
    if dropped:
        print(f"note: {len(dropped)} columns present on one side only were dropped: {dropped[:10]}", file=sys.stderr)
    A = A[:, [cols_a.index(c) for c in common]]
    B = B[:, [cols_b.index(c) for c in common]]
    A, ids_a = cap_rows(A, ids_a, args.max_per_side, args.seed, "reference")
    B, ids_b = cap_rows(B, ids_b, args.max_per_side, args.seed + 1, "candidate")
    if len(A) < 6 or len(B) < 6:
        print("error: need at least 6 items per side", file=sys.stderr)
        return 2

    # one projection for distances, PRDC and nearest-reference distance
    if args.fit == "balanced":
        ra, rb = balanced_fit_rows(len(A), len(B), args.seed)
        fit_rows = np.vstack([A[ra], B[rb]])
    else:
        fit_rows = np.vstack([A, B])
    space = make_pipeline(args).fit(fit_rows)
    ZA, ZB = space.transform(A), space.transform(B)
    sides = {"ref": (A, ZA), "cand": (B, ZB)}

    rng = np.random.default_rng(args.seed + 104729)
    n_hold = int(round(args.holdout_frac * len(B)))
    hold = np.zeros(len(B), bool)
    if n_hold >= 5:
        hold[rng.choice(len(B), n_hold, replace=False)] = True

    results, per_item = {}, {}
    for name, ((sa, ia), (sb, ib)) in comparisons(len(A), len(B), args.seed).items():
        Xa, Za = sides[sa][0][ia], sides[sa][1][ia]
        Xb, Zb = sides[sb][0][ib], sides[sb][1][ib]
        row = {"n_a": len(ia), "n_b": len(ib)}
        if not args.no_c2st:
            X = np.vstack([Xa, Xb])
            lab = np.r_[np.ones(len(ia)), np.zeros(len(ib))].astype(int)
            lr = c2st(X, lab, args, "logreg", args.repeats, args.n_boot)
            rf = c2st(X, lab, args, "rf", max(1, args.repeats // 2), min(args.n_boot, 200))
            for key in ("auc", "auc_lo", "auc_hi", "auc_sd_repeats", "bal_acc"):
                row[f"lr_{key}"] = lr[key]
                row[f"rf_{key}"] = rf[key]
            if name == "observed":
                per_item["p_ref_lr"], per_item["p_ref_rf"] = lr["oof_prob"], rf["oof_prob"]
                if args.c2st_perm:
                    row["lr_auc_perm_p"] = c2st_permutation_p(X, lab, args, lr["auc"], args.c2st_perm)
        row.update(energy_test(Za, Zb, args.n_perm, args.seed))
        row.update(mmd_test(Za, Zb, args.n_perm, args.seed))
        row.update(prdc_balanced(Za, Zb, args.k, args.prdc_reps, args.seed))
        if name == "observed" and hold.any():
            nd = nearest_reference_distance(Za, Zb[~hold], Zb[hold])
            row.update(median_rel_nn=nd["median_rel_nn"], frac_out_of_support=nd["frac_out_of_support"],
                       oos_threshold=nd["threshold"], n_holdout=int(hold.sum()))
            per_item["rel_nn"] = nd["d_ref"]
            per_item["out_of_support"] = nd["d_ref"] > nd["threshold"]
        results[name] = row

    settings = {k: v for k, v in vars(args).items() if k not in ("out", "per_item")}
    settings.update(n_reference=len(A), n_candidate=len(B), n_columns=len(common),
                    space_dim=int(ZA.shape[1]), columns_dropped=dropped)
    keys = []
    for r in results.values():
        keys += [k for k in r if k not in keys]
    names = list(results)
    print(f"reference N={len(A)}, candidate M={len(B)}, {len(common)} columns, space {ZA.shape[1]}-d "
          f"(fit: {args.fit}), {args.n_perm} permutations")
    print(f"{'metric':<22}" + "".join(f"{n:>14}" for n in names))
    for k in keys:
        print(f"{k:<22}" + "".join(f"{fmt(results[n].get(k, '')):>14}" for n in names))
    obs = results["observed"]
    if obs.get("coverage_saturated"):
        print(f"note: coverage null is {obs['coverage_null']:.3f} at n={obs['prdc_n']}: coverage is saturated, "
              "read recall and density instead", file=sys.stderr)
    if obs.get("lr_auc", 0) >= 0.98:
        print("note: linear AUC near 1, the p value carries no information; read per-item P(reference) "
              "(--per-item) and the classifier coefficients", file=sys.stderr)
    if args.out:
        Path(args.out).write_text(json.dumps({"settings": settings, "results": results}, indent=2, default=float))
        print(f"wrote {args.out}")
    if args.per_item:
        with open(args.per_item, "w", newline="") as fh:
            w = csv.writer(fh)
            cols = ["id", "side"] + list(per_item)
            w.writerow(cols)
            n_obs = len(A) + len(B)
            for i in range(n_obs):
                side, iid = ("reference", ids_a[i]) if i < len(A) else ("candidate", ids_b[i - len(A)])
                vals = []
                for k, v in per_item.items():
                    if len(v) != n_obs and i >= len(A):  # reference-only arrays
                        vals.append("")
                    else:
                        vals.append(str(int(v[i])) if v.dtype == bool else fmt(float(v[i])))
                w.writerow([iid, side] + vals)
        print(f"wrote {args.per_item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

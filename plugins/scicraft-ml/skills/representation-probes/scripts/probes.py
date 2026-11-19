#!/usr/bin/env python3
"""Probes that judge an embedding space: noise floor, retrieval, label sensitivity, agreement between two
spaces, perturbation trajectories, redundancy and informativeness, and parity of a reimplementation.

Every input is a plain .npy matrix (items x dims) or a small CSV. Rows of matrices that are compared must
describe the same items in the same order; the script refuses mismatched row counts.

Subcommands
  quality     noise floor, retrieval top-1 and MRR, label shift and sensitivity, one row per encoder, ranked
  agree       Spearman-Mantel, k-NN overlap with chance, debiased and biased linear CKA, per subset
  trajectory  displacement over the noise floor, direction agreement, monotonicity per perturbation kind
  beyond      cross-validated ridge R^2: view from simple statistics, behavior from view (needs scikit-learn)
  parity      reimplementation against published outputs: min per-dimension Pearson r, distance Spearman
  selftest    every probe on synthetic vectors with known answers

Dependencies: numpy and scipy; scikit-learn for `beyond` only. Python 3.9 or later.
Exit code 1 when an input is malformed, a selftest fails, or `parity` misses its threshold.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist, pdist, squareform
from scipy.stats import rankdata, spearmanr

# ---------------------------------------------------------------------------
# core probes (ported from a working analysis package; logic unchanged)
# ---------------------------------------------------------------------------


def linear_cka(X: np.ndarray, Y: np.ndarray, debiased: bool = True) -> float:
    """Linear CKA (Kornblith 2019); debiased HSIC estimator (Song 2012) by default."""
    X = X - X.mean(0)
    Y = Y - Y.mean(0)
    K, L = X @ X.T, Y @ Y.T
    n = K.shape[0]
    if not debiased or n < 4:
        def hsic(A, B):
            return (A * B).sum()
    else:
        def hsic(A, B):
            A, B = A.copy(), B.copy()
            np.fill_diagonal(A, 0)
            np.fill_diagonal(B, 0)
            return ((A * B).sum() + A.sum() * B.sum() / ((n - 1) * (n - 2))
                    - 2 * (A.sum(0) @ B.sum(0)) / (n - 2)) / (n * (n - 3))
    kl, kk, ll = hsic(K, L), hsic(K, K), hsic(L, L)
    return float(kl / np.sqrt(max(kk * ll, 1e-300)))


def knn_overlap(Za: np.ndarray, Zb: np.ndarray, k: int = 10) -> float:
    """Mean share of each item's k nearest neighbors that two spaces have in common. Chance is k/(n-1)."""
    k = min(k, len(Za) - 1)
    na = np.argsort(squareform(pdist(Za)) + np.eye(len(Za)) * 1e18, axis=1)[:, :k]
    nb = np.argsort(squareform(pdist(Zb)) + np.eye(len(Zb)) * 1e18, axis=1)[:, :k]
    return float(np.mean([len(set(a) & set(b)) / k for a, b in zip(na, nb)]))


def mantel(Da: np.ndarray, Db: np.ndarray, n_perm: int = 199, seed: int = 0) -> tuple:
    """Spearman correlation of two square distance matrices with a row/column permutation p-value.
    The plain Spearman p-value is wrong here: the n(n-1)/2 entries are not independent."""
    iu = np.triu_indices_from(Da, 1)
    ra = rankdata(Da[iu])
    rb_full = squareform(rankdata(squareform(Db, checks=False)))
    obs = np.corrcoef(ra, rb_full[iu])[0, 1]
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(n_perm):
        p = rng.permutation(len(Db))
        null.append(np.corrcoef(ra, rb_full[np.ix_(p, p)][iu])[0, 1])
    return float(obs), float((1 + (np.array(null) >= obs).sum()) / (1 + n_perm))


def noise_and_retrieval(A: np.ndarray, B: np.ndarray) -> dict:
    """A[i] and B[i] embed two disjoint halves of item i. Noise floor = median ||A_i - B_i||.
    Retrieval: rank of B_i among all B for query A_i (rank 1 = the other half is the nearest)."""
    noise = np.linalg.norm(A - B, axis=1)
    D = cdist(A, B)
    ranks = (D < np.diag(D)[:, None]).sum(1) + 1
    return {"n_items": len(A), "noise_floor": float(np.median(noise)),
            "retrieval_top1": float((ranks == 1).mean()), "retrieval_mrr": float((1 / ranks).mean()),
            "retrieval_chance": 1 / len(A)}


def direction_agreement(D: np.ndarray) -> float:
    """Mean pairwise cosine of displacement vectors (one row per anchor). 1 = every anchor moves the same way."""
    nrm = np.linalg.norm(D, axis=1, keepdims=True)
    keep = nrm[:, 0] > 1e-9
    D = D[keep] / nrm[keep]
    if len(D) < 2:
        return float("nan")
    C = D @ D.T
    return float(C[np.triu_indices_from(C, 1)].mean())


def monotonicity(severity: np.ndarray, displacement: np.ndarray) -> float:
    """Spearman rho between severity and displacement for one anchor and one perturbation kind."""
    if len(np.unique(severity)) < 3:
        return float("nan")
    return float(spearmanr(severity, displacement).statistic)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def load(path, what: str) -> np.ndarray:
    try:
        Z = np.load(path, allow_pickle=False)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"cannot read {what} from {path}: {e}")
    Z = np.asarray(Z, dtype=np.float64)
    if Z.ndim != 2:
        sys.exit(f"{what} in {path} must be a 2-D matrix (items x dims), got shape {Z.shape}")
    if not np.isfinite(Z).all():
        sys.exit(f"{what} in {path} has {int((~np.isfinite(Z)).sum())} non-finite values; fix them first")
    return Z


def same_rows(*pairs):
    n = {name: len(Z) for name, Z in pairs}
    if len(set(n.values())) != 1:
        sys.exit(f"row counts differ, so items are not aligned: {n}")


def zscore_with(ref: np.ndarray):
    mu, sd = ref.mean(0), ref.std(0)
    sd[sd < 1e-12] = 1.0
    return lambda Z: (Z - mu) / sd


def emit(rows, out):
    if not rows:
        print("nothing to report")
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    widths = {k: max(len(k), *(len(fmt(r.get(k))) for r in rows)) for k in keys}
    print("  ".join(k.ljust(widths[k]) for k in keys))
    for r in rows:
        print("  ".join(fmt(r.get(k)).ljust(widths[k]) for k in keys))
    if out:
        Path(out).write_text(json.dumps(rows, indent=2))
        print(f"wrote {out}")


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return "nan" if not np.isfinite(v) else f"{v:.4g}"
    return str(v)


# ---------------------------------------------------------------------------
# subcommands
# ---------------------------------------------------------------------------


def cmd_quality(a):
    rows = []
    for spec in a.encoder:
        if "=" not in spec:
            sys.exit(f"--encoder takes NAME=DIR, got {spec}")
        name, d = spec.split("=", 1)
        d = Path(d)
        A, B = load(d / "half_a.npy", "half_a"), load(d / "half_b.npy", "half_b")
        same_rows(("half_a", A), ("half_b", B))
        extra = {k: load(d / f"{k}.npy", k) for k in ("full", "shuffled", "subsample") if (d / f"{k}.npy").exists()}
        same_rows(("half_a", A), *extra.items())
        if a.zscore:
            ref = extra.get("full", np.vstack([A, B]))
            z = zscore_with(ref)
            A, B = z(A), z(B)
            extra = {k: z(v) for k, v in extra.items()}
        row = {"encoder": name, "dims": A.shape[1], **noise_and_retrieval(A, B)}
        base = extra.get("full")
        spread_src = base if base is not None else A
        row["spread"] = float(np.median(pdist(spread_src))) if len(spread_src) > 2 else float("nan")
        row["noise_over_spread"] = row["noise_floor"] / row["spread"]
        if base is not None and "shuffled" in extra:
            row["label_shift"] = float(np.median(np.linalg.norm(base - extra["shuffled"], axis=1)))
            row["label_sensitivity"] = row["label_shift"] / row["noise_floor"]
        if base is not None and "subsample" in extra:
            row["subsample_shift"] = float(np.median(np.linalg.norm(base - extra["subsample"], axis=1)))
            if "label_shift" in row:
                row["label_over_subsample"] = row["label_shift"] / max(row["subsample_shift"], 1e-300)
        if row["retrieval_top1"] >= 0.99:
            row["note"] = "retrieval saturated: use more items or harder halves"
        rows.append(row)
    key = "label_sensitivity" if all("label_sensitivity" in r for r in rows) else "retrieval_mrr"
    rows.sort(key=lambda r: -r[key])
    print(f"ranked by {key} (higher first); noise floor and shifts in each encoder's own units, "
          f"ratios and *_over_spread are unit-free")
    emit(rows, a.out)


def read_groups(path, n):
    lines = [ln.strip() for ln in Path(path).read_text().splitlines() if ln.strip()]
    if len(lines) != n:
        sys.exit(f"{path} has {len(lines)} labels for {n} items")
    return np.array(lines)


def cmd_agree(a):
    A, B = load(a.a, "space A"), load(a.b, "space B")
    same_rows(("A", A), ("B", B))
    groups = read_groups(a.groups, len(A)) if a.groups else np.array(["all"] * len(A))
    subsets = {g: np.where(groups == g)[0] for g in dict.fromkeys(groups)}
    if a.groups:
        subsets["union"] = np.arange(len(A))
    rng = np.random.default_rng(a.seed)
    rows = []
    for name, idx in subsets.items():
        if len(idx) < 12:
            rows.append({"subset": name, "n": len(idx), "note": "fewer than 12 items: skipped"})
            continue
        if len(idx) > a.max_items:
            idx = np.sort(rng.choice(idx, a.max_items, replace=False))
        Za, Zb = A[idx], B[idx]
        rho, p = mantel(squareform(pdist(Za)), squareform(pdist(Zb)), a.n_perm, a.seed)
        k = min(a.k, len(idx) - 1)
        rows.append({"subset": name, "n": len(idx), "spearman_mantel": rho, "mantel_p": p,
                     f"knn{k}_overlap": knn_overlap(Za, Zb, k), "knn_chance": k / (len(idx) - 1),
                     "cka_debiased": linear_cka(Za, Zb, True), "cka_biased": linear_cka(Za, Zb, False)})
    emit(rows, a.out)
    within = [r for r in rows if r["subset"] != "union" and "spearman_mantel" in r]
    union = [r for r in rows if r["subset"] == "union" and "spearman_mantel" in r]
    if within and union and union[0]["spearman_mantel"] - max(r["spearman_mantel"] for r in within) > 0.2:
        print("warning: agreement over the union is far above every subset; the group split drives it. "
              "Report the subsets.")


def cmd_trajectory(a):
    anchors, P = load(a.anchors, "anchors"), load(a.perturbed, "perturbed")
    with open(a.meta, newline="") as f:
        meta = list(csv.DictReader(f))
    if len(meta) != len(P):
        sys.exit(f"{a.meta} has {len(meta)} rows for {len(P)} perturbed items")
    for need in ("anchor", "kind", "severity"):
        if need not in meta[0]:
            sys.exit(f"{a.meta} needs columns anchor, kind, severity (missing {need})")
    anc = np.array([int(m["anchor"]) for m in meta])
    if anc.max() >= len(anchors) or anc.min() < 0:
        sys.exit("an anchor index is outside the anchors matrix")
    kind = np.array([m["kind"] for m in meta])
    sev = np.array([float(m["severity"]) for m in meta])
    dvec = P - anchors[anc]
    disp = np.linalg.norm(dvec, axis=1)
    spread = float(np.median(pdist(anchors))) if len(anchors) > 2 else float("nan")
    rows = []
    for k in dict.fromkeys(kind):
        mk = kind == k
        row = {"kind": k, "n": int(mk.sum()), "median_disp": float(np.median(disp[mk]))}
        if a.noise_floor:
            row["disp_over_noise"] = row["median_disp"] / a.noise_floor
        row["disp_over_spread"] = row["median_disp"] / spread
        top = sev[mk].max()
        row["direction_agreement_at_max"] = direction_agreement(dvec[mk & (sev == top)])
        mono = [monotonicity(sev[mk & (anc == i)], disp[mk & (anc == i)]) for i in np.unique(anc[mk])]
        mono = [m for m in mono if np.isfinite(m)]
        row["monotonicity_median"] = float(np.median(mono)) if mono else float("nan")
        row["anchors_with_3plus_levels"] = len(mono)
        rows.append(row)
    emit(rows, a.out)


def cmd_beyond(a):
    try:
        from sklearn.linear_model import RidgeCV
        from sklearn.model_selection import KFold, cross_val_predict
    except ImportError:
        sys.exit("`beyond` needs scikit-learn")
    V = load(a.view, "view")
    rows = {}
    cv = KFold(a.folds, shuffle=True, random_state=a.seed)
    ridge = RidgeCV(alphas=np.logspace(-2, 3, 12))

    def r2(X, Y):
        pred = cross_val_predict(ridge, X, Y, cv=cv)
        return float(1 - ((Y - pred) ** 2).sum() / ((Y - Y.mean(0)) ** 2).sum())

    if a.stats:
        S = load(a.stats, "stats")
        same_rows(("view", V), ("stats", S))
        rows["r2_view_from_stats"] = r2(S, V)
    if a.behavior:
        Bh = load(a.behavior, "behavior")
        same_rows(("view", V), ("behavior", Bh))
        rows["r2_behavior_from_view"] = r2(V, Bh)
        if a.stats:
            rows["r2_behavior_from_stats"] = r2(S, Bh)
    if not rows:
        sys.exit("give --stats, --behavior or both")
    rows["n_items"] = len(V)
    print("redundancy = r2_view_from_stats (high: the view repeats the statistics); informativeness = "
          "r2_behavior_from_view (compare with r2_behavior_from_stats)")
    emit([rows], a.out)


def cmd_parity(a):
    ours, theirs = load(a.ours, "ours"), load(a.theirs, "theirs")
    same_rows(("ours", ours), ("theirs", theirs))
    if ours.shape[1] != theirs.shape[1]:
        sys.exit(f"dimension counts differ: ours {ours.shape[1]}, theirs {theirs.shape[1]}")
    if a.minmax:
        def mm(Z):
            lo, hi = Z.min(0), Z.max(0)
            return (Z - lo) / np.where(hi - lo < 1e-12, 1, hi - lo)
        ours, theirs = mm(ours), mm(theirs)
    r = []
    for j in range(ours.shape[1]):
        x, y = ours[:, j], theirs[:, j]
        r.append(float("nan") if x.std() < 1e-12 or y.std() < 1e-12 else float(np.corrcoef(x, y)[0, 1]))
    r = np.array(r)
    dist_rho = float(spearmanr(pdist(ours), pdist(theirs)).statistic)
    worst = int(np.nanargmin(r)) if np.isfinite(r).any() else -1
    row = {"n_items": len(ours), "dims": ours.shape[1], "min_dim_pearson": float(np.nanmin(r)),
           "worst_dim": worst, "constant_dims": int(np.isnan(r).sum()), "distance_spearman": dist_rho,
           "max_abs_diff": float(np.abs(ours - theirs).max())}
    emit([row], a.out)
    ok = row["min_dim_pearson"] >= a.threshold and dist_rho >= a.threshold
    print(("PASS" if ok else "FAIL") + f": threshold {a.threshold} on min per-dimension r and distance Spearman")
    if not ok:
        sys.exit(1)


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------


def cmd_selftest(a):
    rng = np.random.default_rng(0)
    fails = []

    def check(name, cond, val):
        print(f"{'ok  ' if cond else 'FAIL'} {name}: {val}")
        if not cond:
            fails.append(name)

    n, d = 100, 16
    Z = rng.normal(size=(n, d))
    A, B = Z + 0.05 * rng.normal(size=Z.shape), Z + 0.05 * rng.normal(size=Z.shape)
    q = noise_and_retrieval(A, B)
    check("halves of distinct items find each other", q["retrieval_top1"] == 1.0, q["retrieval_top1"])
    q0 = noise_and_retrieval(rng.normal(size=(n, d)), rng.normal(size=(n, d)))
    check("unrelated halves sit near chance MRR", q0["retrieval_mrr"] < 0.15, round(q0["retrieval_mrr"], 3))
    X, Y = rng.normal(size=(n, d)), rng.normal(size=(n, d))
    cb, cd = linear_cka(X, Y, False), linear_cka(X, Y, True)
    check("biased CKA of independent matrices is inflated (n=100, p=16)", cb > 0.08, round(cb, 3))
    check("debiased CKA of independent matrices is near 0", abs(cd) < 0.05, round(cd, 3))
    check("CKA is invariant to rotation", abs(linear_cka(X, X @ np.linalg.qr(rng.normal(size=(d, d)))[0]) - 1) < 1e-9,
          "1.0")
    ov = knn_overlap(X, Y, 10)
    check("k-NN overlap of unrelated spaces near chance k/(n-1)", abs(ov - 10 / (n - 1)) < 0.05,
          f"{ov:.3f} vs {10 / (n - 1):.3f}")
    rho, p = mantel(squareform(pdist(X)), squareform(pdist(X * 3 + 1)), 99)
    check("Mantel of a rescaled copy is 1 with the minimum p", rho > 0.999 and p == 1 / 100, (round(rho, 3), p))
    rho0, p0 = mantel(squareform(pdist(X)), squareform(pdist(Y)), 99)
    check("Mantel of unrelated spaces is not significant", p0 > 0.05, (round(rho0, 3), p0))
    shift = np.tile(rng.normal(size=(1, d)), (20, 1)) + 0.1 * rng.normal(size=(20, d))
    check("a shared shift has direction agreement near 1", direction_agreement(shift) > 0.9,
          round(direction_agreement(shift), 3))
    check("random displacements have direction agreement near 0",
          abs(direction_agreement(rng.normal(size=(20, d)))) < 0.1,
          round(direction_agreement(rng.normal(size=(20, d))), 3))
    check("monotone severity gives rho 1", monotonicity(np.array([0, .25, .5, 1.]), np.array([0, .1, .3, .9])) == 1,
          1.0)
    # a mixed union inflates agreement: two groups far apart, unrelated geometry inside each
    G = np.r_[np.zeros(60), np.ones(60)]
    Ua = np.c_[rng.normal(size=(120, d)) + 8 * G[:, None]]
    Ub = np.c_[rng.normal(size=(120, d)) + 8 * G[:, None]]
    ru = mantel(squareform(pdist(Ua)), squareform(pdist(Ub)), 49)[0]
    rw = mantel(squareform(pdist(Ua[:60])), squareform(pdist(Ub[:60])), 49)[0]
    check("union agreement is driven by the group split", ru > 0.5 and abs(rw) < 0.2, (round(ru, 3), round(rw, 3)))
    print(f"{'all checks passed' if not fails else f'{len(fails)} failed'}")
    if fails:
        sys.exit(1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("quality", help="noise floor, retrieval, label sensitivity; ranks encoders")
    q.add_argument("--encoder", action="append", required=True, metavar="NAME=DIR",
                   help="DIR holds half_a.npy, half_b.npy (required) and full.npy, shuffled.npy, subsample.npy "
                        "(optional); row i of every file is item i")
    q.add_argument("--zscore", action="store_true",
                   help="z-score each encoder's dims with the mean and SD of full.npy (or of both halves)")
    q.add_argument("--out", help="write the table as JSON")
    q.set_defaults(fn=cmd_quality)

    g = sub.add_parser("agree", help="agreement of two spaces on the same items, per subset")
    g.add_argument("--a", required=True, help="space A, .npy items x dims")
    g.add_argument("--b", required=True, help="space B, .npy items x dims, same item order")
    g.add_argument("--groups", help="text file, one subset label per item (for example real / synthetic)")
    g.add_argument("--k", type=int, default=10)
    g.add_argument("--n-perm", type=int, default=199, help="Mantel permutations (199 to screen, 999 to report)")
    g.add_argument("--max-items", type=int, default=600, help="subsample larger subsets to keep permutations cheap")
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--out")
    g.set_defaults(fn=cmd_agree)

    t = sub.add_parser("trajectory", help="perturbation displacement, direction agreement, monotonicity")
    t.add_argument("--anchors", required=True, help="unperturbed items, .npy")
    t.add_argument("--perturbed", required=True, help="perturbed items, .npy")
    t.add_argument("--meta", required=True, help="CSV with one row per perturbed item: anchor,kind,severity")
    t.add_argument("--noise-floor", type=float, help="noise floor from `quality`, same space")
    t.add_argument("--out")
    t.set_defaults(fn=cmd_trajectory)

    b = sub.add_parser("beyond", help="redundancy with statistics and informativeness about behavior")
    b.add_argument("--view", required=True)
    b.add_argument("--stats", help="simple statistics of the same items, .npy")
    b.add_argument("--behavior", help="behavior to predict (for example per-item model scores), .npy")
    b.add_argument("--folds", type=int, default=5)
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--out")
    b.set_defaults(fn=cmd_beyond)

    p = sub.add_parser("parity", help="reimplementation against the authors' published outputs")
    p.add_argument("--ours", required=True)
    p.add_argument("--theirs", required=True)
    p.add_argument("--minmax", action="store_true", help="min-max normalize each dimension of both first "
                                                         "(when the published file was normalized that way)")
    p.add_argument("--threshold", type=float, default=0.9999)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_parity)

    s = sub.add_parser("selftest", help="run every probe on synthetic vectors with known answers")
    s.set_defaults(fn=cmd_selftest)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()

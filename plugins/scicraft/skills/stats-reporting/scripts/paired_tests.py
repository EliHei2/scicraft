#!/usr/bin/env python3
"""Paired per-unit comparisons and one multiple-testing correction, with print-ready values.

Two subcommands.

  paired   Long CSV with one row per (comparison, unit): columns family, comparison, unit, a, b
           (a = the method under test, b = the reference it is compared with, both on the same unit:
           the same fold, seed, dataset or block). Per comparison it reports n, the medians and IQRs of
           a and b, the Hodges-Lehmann shift of a - b (optional percentile bootstrap CI over units), the
           exact two-sided Wilcoxon signed-rank p (tie-aware), the Benjamini-Hochberg adjusted p within
           the family, and the text the declared display rule allows. With --strata COLUMN it also runs
           the stratified sign-flip test per comparison over the strata (each stratum weighs equally).

  adjust   CSV with columns family, label, p (unadjusted). Optional columns stored_adjusted and
           stored_method ("holm" or "bh"): the script first checks that it reproduces the stored values
           exactly, and refuses to go on when it does not (the inputs are then not what you think).
           Then it writes BH adjusted p for every row, the count significant per family, the largest
           significant adjusted p and its printable bound.

The display rule (--print-threshold, default 0.01) is applied to every row alike: a value at or below
the threshold is printed as a bound ("p < .001", "p <= .004"); a significant value above it is printed
as "significant (adjusted p < .05)"; a non-significant value is printed in full, because a "no change"
claim needs its number. The exact adjusted p always stays in the output table. Declare the rule in the
document. P values are never rounded down.

Statistics code ported from the author's own rebuttal statistics module (Hodges-Lehmann, exact
signed-rank with midranks, stratified sign flip, Holm, BH). Command-line interface added here.

Requires numpy and scipy (scipy only for midranks). Python 3.9 or later.

Examples:
  python3 paired_tests.py paired folds.csv --out tests.tsv --ci 2000 --seed 0
  python3 paired_tests.py paired folds.csv --strata task --flips 20000
  python3 paired_tests.py adjust pvalues.csv --out adjusted.tsv
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import OrderedDict, defaultdict

import numpy as np

TIE_TOL = 1e-12  # paired scores that differ by less than this are a tie (float rounding)


# ---------------------------------------------------------------- statistics (ported)
def walsh(x):
    x = np.asarray(x, float)
    i, j = np.triu_indices(len(x))
    return (x[i] + x[j]) / 2.0


def hl(x):
    """Hodges-Lehmann one-sample estimate: the median of the Walsh averages."""
    return float(np.median(walsh(x)))


def hl_boot_ci(x, B, rng, level=0.95):
    x = np.asarray(x, float)
    n = len(x)
    idx = rng.integers(0, n, size=(B, n))
    est = np.array([hl(x[r]) for r in idx])
    lo = (1 - level) / 2 * 100
    return float(np.percentile(est, lo)), float(np.percentile(est, 100 - lo))


def clean(d):
    """|d| <= TIE_TOL set to 0 (a tie up to float rounding)."""
    d = np.asarray(d, float).copy()
    d[np.abs(d) <= TIE_TOL] = 0.0
    return d


def signed_rank_weights(d):
    """Midranks of |d| with signs; zeros dropped (Wilcoxon's rule); |d| equal to 12 decimals tied."""
    from scipy.stats import rankdata
    d = clean(d)
    d = d[d != 0]
    r = rankdata(np.round(np.abs(d), 12))
    return r, np.sign(d)


def exact_signrank_p(d):
    """Exact two-sided Wilcoxon signed-rank p, tie-aware, by convolution over 2 x rank.
    Equals scipy's method='exact' when there are no ties or zeros. Returns (p, n used)."""
    r, s = signed_rank_weights(d)
    n = len(r)
    if n == 0:
        return 1.0, 0
    r2 = np.round(2 * r).astype(int)
    tot = int(r2.sum())
    pmf = np.zeros(tot + 1)
    pmf[0] = 1.0
    for v in r2:
        new = pmf.copy()
        new[v:] += pmf[:tot + 1 - v]
        pmf = new
    pmf /= 2.0 ** n
    obs = int(r2[s > 0].sum())
    sup = np.arange(tot + 1)
    p = float(pmf[np.abs(sup - tot / 2) >= abs(obs - tot / 2) - 1e-9].sum())
    return min(1.0, p), n


def stratified_signflip(diffs_by_stratum, N, rng):
    """Two-sided stratified sign-flip permutation test. S = sum_t Z_t / sqrt(T), Z_t the stratum's
    standardized signed-rank statistic, so each stratum weighs equally whatever its unit count.
    p = (1 + #{|S*| >= |S|}) / (1 + N)."""
    strata = [t for t, d in diffs_by_stratum.items() if np.any(clean(d) != 0)]
    T = len(strata)
    if T == 0:
        return dict(S=0.0, p=1.0, n_strata=0, N=N)
    S_obs = 0.0
    S_null = np.zeros(N)
    for t in strata:
        r, s = signed_rank_weights(diffs_by_stratum[t])
        den = math.sqrt(float((r ** 2).sum()))
        S_obs += float((r * s).sum()) / den
        flips = rng.choice(np.array([-1.0, 1.0]), size=(N, len(r)))
        S_null += (flips @ r) / den
    S_obs /= math.sqrt(T)
    S_null /= math.sqrt(T)
    p = (1 + int((np.abs(S_null) >= abs(S_obs) - 1e-12).sum())) / (1 + N)
    return dict(S=S_obs, p=p, n_strata=T, N=N)


def holm(ps):
    m = len(ps)
    o = sorted(range(m), key=lambda i: ps[i])
    adj = [0.0] * m
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (m - r) * ps[i]))
        adj[i] = run
    return adj


def bh(ps):
    m = len(ps)
    o = sorted(range(m), key=lambda i: ps[i])
    q = [0.0] * m
    prev = 1.0
    for r, i in reversed(list(enumerate(o, 1))):
        prev = min(prev, ps[i] * m / r)
        q[i] = prev
    return q


# ---------------------------------------------------------------- printing
def fmt_p(p):
    """APA style without the leading zero, never rounded down."""
    if p < 0.001:
        return "< .001"
    digits = 2 if p >= 0.1 else 3
    v = math.ceil(p * 10 ** digits - 1e-9) / 10 ** digits
    return ("%.*f" % (digits, v)).lstrip("0")


def bound(p):
    """Printable upper bound: '< .001', else three decimals rounded up ('<= .009' for .0085)."""
    if p < 0.001:
        return "p < .001"
    v = math.ceil(p * 1000 - 1e-9) / 1000
    return "p <= " + ("%.3f" % v).lstrip("0")


def display_text(adj_p, alpha, threshold):
    if adj_p <= threshold:
        return bound(adj_p)
    if adj_p < alpha:
        return "significant (adjusted p < %s)" % ("%g" % alpha).lstrip("0")
    return "no significant difference (adjusted p = %s)" % fmt_p(adj_p)


def iqr(x):
    q25, q50, q75 = np.percentile(np.asarray(x, float), [25, 50, 75])
    return q50, q25, q75


# ---------------------------------------------------------------- commands
def read_csv(path):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("error: %s has no rows" % path)
    return rows


def need(rows, cols, path):
    missing = [c for c in cols if c not in rows[0]]
    if missing:
        sys.exit("error: %s lacks column(s) %s" % (path, ", ".join(missing)))


def write_tsv(rows, out):
    if not rows:
        return
    cols = list(rows[0].keys())
    fh = open(out, "w") if out else sys.stdout
    fh.write("\t".join(cols) + "\n")
    for r in rows:
        fh.write("\t".join(("%.6g" % v) if isinstance(v, float) else str(v) for v in (r[c] for c in cols)) + "\n")
    if out:
        fh.close()
        print("wrote %s (%d rows)" % (out, len(rows)), file=sys.stderr)


def cmd_paired(a):
    rows = read_csv(a.csv)
    cols = ["family", "comparison", "unit", "a", "b"] + ([a.strata] if a.strata else [])
    need(rows, cols, a.csv)
    groups = OrderedDict()
    seen = set()
    for r in rows:
        key = (r["family"], r["comparison"], r.get(a.strata, "") if a.strata else "", r["unit"])
        if key in seen:
            sys.exit("error: duplicate unit %r for comparison %r; pair each unit once" % (r["unit"], r["comparison"]))
        seen.add(key)
        groups.setdefault((r["family"], r["comparison"]), []).append(r)
    rng = np.random.default_rng(a.seed)
    out = []
    for (fam, comp), rs in groups.items():
        va = np.array([float(r["a"]) for r in rs])
        vb = np.array([float(r["b"]) for r in rs])
        d = va - vb
        if a.lower_better:
            d = -d
        p, n_used = exact_signrank_p(d)
        ma, a25, a75 = iqr(va)
        mb, b25, b75 = iqr(vb)
        row = OrderedDict(family=fam, comparison=comp, n_units=len(d), n_untied=n_used,
                          median_a=ma, iqr_a="%.4g to %.4g" % (a25, a75),
                          median_b=mb, iqr_b="%.4g to %.4g" % (b25, b75),
                          hl_shift=hl(d) if len(d) else float("nan"))
        if a.ci:
            lo, hi = hl_boot_ci(d, a.ci, rng)
            row["hl_ci95"] = "%.4g to %.4g" % (lo, hi)
        row["wins"] = int((clean(d) > 0).sum())
        row["losses"] = int((clean(d) < 0).sum())
        row["ties"] = int((clean(d) == 0).sum())
        row["p"] = p
        if a.strata:
            by = defaultdict(list)
            for r, x in zip(rs, d):
                by[r[a.strata]].append(x)
            res = stratified_signflip({k: np.array(v) for k, v in by.items()}, a.flips, rng)
            row["strata"] = res["n_strata"]
            row["p_stratified"] = res["p"]
        if len(d) < a.min_units:
            row["note"] = "fewer than %d units: too few for this test" % a.min_units
        else:
            row["note"] = ""
        out.append(row)
    # one correction (BH) within each family, over every comparison in it
    for key in ["p"] + (["p_stratified"] if a.strata else []):
        fams = defaultdict(list)
        for r in out:
            fams[r["family"]].append(r)
        for fam, rs in fams.items():
            q = bh([r[key] for r in rs])
            for r, v in zip(rs, q):
                r["adj_" + key] = v
                r["display_" + key] = display_text(v, a.alpha, a.print_threshold)
    write_tsv(out, a.out)
    nfam = len(set(r["family"] for r in out))
    nsig = sum(r["adj_p"] < a.alpha for r in out)
    print("checked %d comparisons in %d families; %d significant at adjusted p < %g (BH within family); "
          "display threshold %g applied to every row" % (len(out), nfam, nsig, a.alpha, a.print_threshold),
          file=sys.stderr)
    few = [r for r in out if r["note"]]
    if few:
        print("warning: %d comparison(s) have fewer than %d units" % (len(few), a.min_units), file=sys.stderr)
    return 0


def cmd_adjust(a):
    rows = read_csv(a.csv)
    need(rows, ["family", "label", "p"], a.csv)
    fams = OrderedDict()
    for r in rows:
        fams.setdefault(r["family"], []).append(r)
    bad = 0
    out = []
    summary = []
    for fam, rs in fams.items():
        ps = [float(r["p"]) for r in rs]
        if "stored_adjusted" in rs[0] and rs[0].get("stored_adjusted", "") != "":
            method = (rs[0].get("stored_method") or "").strip().lower()
            if method not in ("holm", "bh"):
                sys.exit("error: stored_method must be holm or bh in family %r" % fam)
            redo = holm(ps) if method == "holm" else bh(ps)
            for r, v in zip(rs, redo):
                if abs(v - float(r["stored_adjusted"])) > a.tol:
                    bad += 1
                    print("MISMATCH %s / %s: stored %s adjusted %s, recomputed %.6g"
                          % (fam, r["label"], method, r["stored_adjusted"], v), file=sys.stderr)
        q = bh(ps)
        sig = [v for v in q if v < a.alpha]
        for r, v in zip(rs, q):
            out.append(OrderedDict(family=fam, label=r["label"], p=float(r["p"]), adj_p_bh=v,
                                   significant="yes" if v < a.alpha else "no",
                                   display=display_text(v, a.alpha, a.print_threshold)))
        summary.append((fam, len(rs), len(sig), max(sig) if sig else None))
    if bad:
        print("error: %d stored adjusted values did not reproduce; fix the inputs before re-adjusting" % bad,
              file=sys.stderr)
        return 1
    write_tsv(out, a.out)
    for fam, m, k, mx in summary:
        tail = "largest significant adjusted p %.6g, printed %s" % (mx, bound(mx)) if mx is not None else "none significant"
        print("family %s: %d of %d significant (BH, alpha %g); %s" % (fam, k, m, a.alpha, tail), file=sys.stderr)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--alpha", type=float, default=0.05, help="significance level for adjusted p (default 0.05)")
    common.add_argument("--print-threshold", type=float, default=0.01,
                        help="adjusted p at or below this is printed as a bound (default 0.01)")
    common.add_argument("--out", help="output TSV (default stdout)")
    p1 = sub.add_parser("paired", parents=[common], help="paired per-unit tests with BH within family")
    p1.add_argument("csv")
    p1.add_argument("--lower-better", action="store_true", help="scores where lower is better (sign flipped)")
    p1.add_argument("--ci", type=int, default=0, help="bootstrap draws for a 95%% CI of the HL shift (0 = none)")
    p1.add_argument("--strata", help="column naming strata (e.g. task) for the stratified sign-flip test")
    p1.add_argument("--flips", type=int, default=20000, help="sign-flip draws for --strata (default 20000)")
    p1.add_argument("--min-units", type=int, default=6, help="warn below this many paired units (default 6)")
    p1.add_argument("--seed", type=int, default=0)
    p2 = sub.add_parser("adjust", parents=[common], help="re-adjust stored p values with BH")
    p2.add_argument("csv")
    p2.add_argument("--tol", type=float, default=1e-9, help="tolerance for reproducing stored values")
    a = ap.parse_args(argv)
    return cmd_paired(a) if a.cmd == "paired" else cmd_adjust(a)


if __name__ == "__main__":
    sys.exit(main())

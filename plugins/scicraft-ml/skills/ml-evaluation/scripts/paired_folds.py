#!/usr/bin/env python3
"""Paired per-fold comparison of methods against one reference, with one multiple-testing correction.

Ported from the acceptance-chain script of a foundation-model benchmark (its exact signed-rank,
Hodges-Lehmann interval, intersection-union rule and Benjamini-Hochberg step) and stripped of
project specifics.

The test, per (method, task):
* Paired differences method - reference over the folds both have. Folds only one of them has
  are counted and reported as unpaired; they never enter the test.
* Exact two-sided Wilcoxon signed-rank test. Zero differences are dropped, tied |d| get
  mid-ranks, the null is the exact conditional sign-flip distribution.
* With fewer than 6 pairs the exact test cannot reach .05 (its smallest two-sided p is 2/2^n),
  so the two-sided paired t-test is used. The switch depends on the design (fold count), never
  on the data. The t-test needs scipy.
* With a fold_seed column and more than one seed (repeated partitions re-test the same units),
  the column's p is the largest per-seed p, and it counts only when every seed points the same
  way (otherwise p = 1). This is an intersection-union test.
* Hodges-Lehmann shift (median of Walsh averages) with its distribution-free 95% interval from
  the exact signed-rank null, or a t interval when n is too small; counts of folds where the
  method is above (+) and below (-) the reference.
* Benjamini-Hochberg over the whole family printed in one run (every method x task pair). One
  correction method for the whole paper; do not mix it with another.
* Optional noise unit: --replicate names a config-identical rerun of the reference. Its paired
  differences against the reference give a tie band of 3 x their SD; a shift inside the band is
  printed as a tie whatever its p.

Input: long CSV with columns task, fold, method, score and optionally fold_seed. Lower-is-better
tasks are listed with --lower-better (differences are then reference - method, so positive
always means the method is better).

Dependencies: Python standard library; scipy only for the paired t-test at fewer than 6 folds.

Example:
    python3 paired_folds.py scores.csv --reference ours --json paired.json
    python3 paired_folds.py scores.csv --reference ours --replicate ours_rerun --methods baseline_a
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import statistics as st
import sys

MIN_EXACT_N = 6
NDIG = 10


def _sign(x):
    return (x > 0) - (x < 0)


def _signed_rank_counts(r2):
    """Number of sign assignments giving each value of the positive (doubled) rank sum."""
    counts = [0] * (sum(r2) + 1)
    counts[0] = 1
    hi = 0
    for r in r2:
        for s in range(hi, -1, -1):
            if counts[s]:
                counts[s + r] += counts[s]
        hi += r
    return counts


def signed_rank_exact(d):
    """Exact two-sided Wilcoxon signed-rank test of paired differences d."""
    x = [v for v in (round(float(v), NDIG) for v in d) if v != 0.0]
    n = len(x)
    if n == 0:
        return dict(n=0, w_plus=0.0, w_minus=0.0, p=1.0)
    order = sorted(range(n), key=lambda i: abs(x[i]))
    r2 = [0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(x[order[j + 1]]) == abs(x[order[i]]):
            j += 1
        for k in range(i, j + 1):
            r2[order[k]] = i + j + 2                    # 2 x the mid-rank of positions i..j (1-based)
        i = j + 1
    tot = sum(r2)
    wp2 = sum(r2[i] for i in range(n) if x[i] > 0)
    counts = _signed_rank_counts(r2)
    dev = abs(2 * wp2 - tot)
    tail = sum(c for s, c in enumerate(counts) if c and abs(2 * s - tot) >= dev)
    return dict(n=n, w_plus=wp2 / 2.0, w_minus=(tot - wp2) / 2.0, p=min(1.0, tail / 2 ** n))


def paired_t(d):
    """Two-sided paired t-test of differences d (small-n columns only)."""
    n = len(d)
    if n < 2:
        return dict(n=n, t=float("nan"), p=1.0, mean=(d[0] if d else 0.0))
    m, s = st.mean(d), st.stdev(d)
    if s == 0.0:
        return dict(n=n, t=math.copysign(math.inf, m) if m else 0.0, p=0.0 if m else 1.0, mean=m)
    try:
        from scipy.stats import t as tdist
    except ImportError:
        sys.exit("error: fewer than 6 paired folds needs the paired t-test, which needs scipy")
    t = m / (s / math.sqrt(n))
    return dict(n=n, t=t, p=float(min(1.0, 2.0 * tdist.sf(abs(t), n - 1))), mean=m)


def hodges_lehmann(d, conf=0.95):
    """(estimate, lo, hi, kind): HL shift with its exact distribution-free CI, else a t interval."""
    n = len(d)
    if n == 0:
        return float("nan"), None, None, "none"
    walsh = sorted((d[i] + d[j]) / 2.0 for i in range(n) for j in range(i, n))
    est = st.median(walsh)
    counts = _signed_rank_counts(list(range(1, n + 1)))
    cum, c = 0, -1
    for s, k in enumerate(counts):
        cum += k
        if cum / 2 ** n <= (1 - conf) / 2:
            c = s
        else:
            break
    if c >= 0:
        k = c + 1
        return est, walsh[k - 1], walsh[len(walsh) - k], "HL"
    if n < 2:
        return est, None, None, "none"
    try:
        from scipy.stats import t as tdist
    except ImportError:
        return est, None, None, "none"
    m, s = st.mean(d), st.stdev(d)
    h = float(tdist.ppf(0.5 + conf / 2, n - 1)) * s / math.sqrt(n)
    return m, m - h, m + h, "t"


def bh_adjusted(ps):
    """Benjamini-Hochberg adjusted p-values (reject at q iff adjusted <= q)."""
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    adj, run = [1.0] * m, 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        run = min(run, ps[i] * m / rank)
        adj[i] = min(1.0, run)
    return adj


def column_test(fa, fb):
    """Paired test of a against b on their shared (fold_seed, fold) cells."""
    keys = sorted(set(fa) & set(fb))
    out = dict(pairs=len(keys), unpaired=len(set(fa) ^ set(fb)))
    if not keys:
        return dict(out, p=1.0, dir=0, test="none", note="no shared folds")
    per = []
    for s in sorted({k[0] for k in keys}):
        d = [round(fa[k] - fb[k], NDIG) for k in keys if k[0] == s]
        if len(d) >= MIN_EXACT_N:
            r = signed_rank_exact(d)
            per.append(dict(seed=s, n=len(d), test="wilcoxon", p=r["p"], dir=_sign(r["w_plus"] - r["w_minus"])))
        else:
            r = paired_t(d)
            per.append(dict(seed=s, n=len(d), test="t", p=r["p"], dir=_sign(r["mean"])))
    dirs = {x["dir"] for x in per}
    note = ""
    if len(per) > 1 and (len(dirs) > 1 or 0 in dirs):
        p, direction = 1.0, 0
        note = "fold seeds disagree: " + ", ".join(f"s{x['seed']} {x['dir']:+d}" for x in per)
    else:
        p, direction = max(x["p"] for x in per), per[0]["dir"]
    d_all = [fa[k] - fb[k] for k in keys]
    est, lo, hi, kind = hodges_lehmann(d_all)
    if out["unpaired"]:
        note = (note + "; " if note else "") + f"{out['unpaired']} unpaired fold(s) left out"
    test = "+".join(sorted({x["test"] for x in per})) + (f" IUT x{len(per)}" if len(per) > 1 else "")
    return dict(out, p=p, dir=direction, test=test, median_diff=st.median(d_all), est=est, lo=lo, hi=hi,
                ci=kind, n_pos=sum(v > 0 for v in d_all), n_neg=sum(v < 0 for v in d_all), note=note,
                sd_diff=(st.stdev(d_all) if len(d_all) > 1 else None))


def read(path, lower):
    data = collections.defaultdict(dict)            # (method, task) -> {(seed, fold): score}
    with open(path, newline="") as fh:
        rd = csv.DictReader(fh)
        if not {"task", "fold", "method", "score"} <= set(rd.fieldnames or []):
            sys.exit("error: CSV needs columns task, fold, method, score")
        for r in rd:
            try:
                v = float(r["score"])
            except (TypeError, ValueError):
                continue                             # a missing run plays no pair
            if math.isnan(v):
                continue
            t = r["task"].strip()
            key = (r.get("fold_seed", "0") or "0", r["fold"].strip())
            cell = data[(r["method"].strip(), t)]
            if key in cell:
                sys.exit(f"error: duplicate row {r['method']}/{t}/{key}")
            cell[key] = -v if t in lower else v
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("csv")
    ap.add_argument("--reference", required=True, help="the method every other method is paired against")
    ap.add_argument("--methods", nargs="*", help="methods to test (default: all others)")
    ap.add_argument("--tasks", nargs="*", help="tasks to test (default: all)")
    ap.add_argument("--lower-better", nargs="*", default=[], metavar="TASK")
    ap.add_argument("--replicate", help="config-identical rerun of the reference, used as the noise unit")
    ap.add_argument("--q", type=float, default=0.05, help="BH level")
    ap.add_argument("--json")
    a = ap.parse_args(argv)

    data = read(a.csv, set(a.lower_better))
    tasks = sorted(a.tasks or {t for _, t in data})
    methods = sorted(a.methods or {m for m, _ in data if m not in (a.reference, a.replicate)})
    band = {}
    if a.replicate:
        for t in tasks:
            r = column_test(data.get((a.replicate, t), {}), data.get((a.reference, t), {}))
            if r.get("sd_diff") is not None:
                band[t] = 3.0 * r["sd_diff"]
    res = []
    for m in methods:
        for t in tasks:
            fa, fb = data.get((m, t)), data.get((a.reference, t))
            if not fa or not fb:
                res.append(dict(method=m, task=t, status="missing", p=None))
                continue
            res.append(dict(method=m, task=t, status="tested", **column_test(fa, fb)))
    tested = [r for r in res if r["status"] == "tested" and r["pairs"]]
    adj = bh_adjusted([r["p"] for r in tested]) if tested else []
    for r, q in zip(tested, adj):
        r["p_bh"] = q
        r["tie_band"] = band.get(r["task"])
        if r["tie_band"] is not None and abs(r["est"]) < r["tie_band"]:
            r["reading"] = "tie (inside replicate band)"
        elif q <= a.q:
            r["reading"] = "significant gain" if r["dir"] > 0 else "significant loss"
        else:
            r["reading"] = "no significant difference"

    print(f"reference: {a.reference}; family: {len(tested)} comparisons, Benjamini-Hochberg at q = {a.q}")
    if a.replicate:
        print(f"noise unit: {a.replicate} vs {a.reference}; tie band = 3 x SD of their paired differences")
    print()
    print("| method | task | pairs | test | HL shift [95% CI] | +/- folds | p | p (BH) | reading |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in res:
        if r["status"] != "tested" or not r.get("pairs"):
            print(f"| {r['method']} | {r['task']} | 0 | none | | | | | missing run |")
            continue
        ci = f"[{r['lo']:+.4f}, {r['hi']:+.4f}]" if r["lo"] is not None else "[n/a]"
        print(f"| {r['method']} | {r['task']} | {r['pairs']} | {r['test']} | {r['est']:+.4f} {ci} | "
              f"{r['n_pos']}/{r['n_neg']} | {r['p']:.4g} | {r['p_bh']:.4g} | {r['reading']} |")
        if r["note"]:
            print(f"|  |  |  |  | note: {r['note']} |  |  |  |  |")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(reference=a.reference, q=a.q, replicate=a.replicate, results=res), fh, indent=1)
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

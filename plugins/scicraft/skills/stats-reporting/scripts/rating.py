#!/usr/bin/env python3
"""Bradley-Terry ratings (Elo scale) and mean rank from per-unit scores of many methods on many tasks.

Input: a long CSV with columns task, unit, method, score. A unit is the arena: one held-out fold, seed or
dataset that every method was scored on identically (same split, same metric). Every pair of methods
present in a unit plays one game, won by the higher score (or the lower with --lower-better); equal
scores count as no game.

What it does, in order:
  1. Coverage gate: a method is rated only if it has scores on at least max(--min-cols,
     floor(--coverage x tasks)) tasks, capped at the number of tasks (for example 3 of 4). A method present on one or two easy tasks has an easier schedule,
     not a better model. Excluded methods are listed.
  2. Equal task weights: each task carries total weight 1 whatever its unit count, so a task with many
     folds does not cast most of the votes.
  3. Bradley-Terry MLE by the MM algorithm (Hunter 2004) with a symmetric prior of --prior virtual
     wins and losses against an average player, which keeps an undefeated or winless method finite.
     Ratings are on the 400/ln10 scale, centred at --center, or shifted so that --anchor gets
     --anchor-value.
  4. Uncertainty: a bootstrap that resamples units within each task (--boot draws). Reported as the
     interquartile range of the rating, the share of draws in which each method has the highest
     rating, and for --pair A B the share of draws in which A is rated above B.
  5. Mean rank: per task, methods are ranked by their median score over units (1 = best, ties get the
     mean rank); the mean over tasks is reported beside the rating.

Ported from the author's benchmark report script (per-fold arenas, MM fit with prior, equal task weights,
stratified bootstrap, IQR, coverage gate). Mean rank, the top share, --pair, --anchor and the CSV
interface were added here.

Requires numpy. Python 3.9 or later.

Example:
  python3 rating.py scores.csv --boot 300 --seed 0 --out ratings.tsv --pair ours baseline_a
"""
from __future__ import annotations

import argparse
import collections
import csv
import math
import sys

import numpy as np

SCALE = 400.0 / math.log(10.0)


def read(path, lower_better):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    for c in ("task", "unit", "method", "score"):
        if not rows or c not in rows[0]:
            sys.exit("error: %s needs columns task, unit, method, score" % path)
    arenas = collections.defaultdict(dict)
    for r in rows:
        if r["score"] in ("", "nan", "NA"):
            continue
        v = float(r["score"])
        key = (r["task"], r["unit"])
        if r["method"] in arenas[key]:
            sys.exit("error: method %r appears twice in task %r unit %r; canonicalise method names first"
                     % (r["method"], r["task"], r["unit"]))
        arenas[key][r["method"]] = -v if lower_better else v
    return [(t, u, sc) for (t, u), sc in sorted(arenas.items())]


def bt(W, n, iters=400, prior=1.0):
    """MM algorithm (Hunter 2004) with a symmetric prior against a fictitious average player."""
    N = W + W.T
    w = W.sum(1) + prior
    p = np.ones(n)
    for _ in range(iters):
        pm = p.mean()
        S = (N / (p[:, None] + p[None, :] + 1e-12)).sum(1) + 2 * prior / (p + pm + 1e-12)
        pn = w / np.maximum(S, 1e-12)
        pn = pn / np.exp(np.log(pn).mean())
        if np.max(np.abs(np.log(pn + 1e-12) - np.log(p + 1e-12))) < 1e-10:
            p = pn
            break
        p = pn
    r = SCALE * np.log(p)
    return r - r.mean()


def mean_ranks(ars, meths):
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for t, u, sc in ars:
        for m, v in sc.items():
            per[t][m].append(v)
    ranks = collections.defaultdict(list)
    for t, d in per.items():
        med = {m: float(np.median(v)) for m, v in d.items() if m in meths}
        vals = sorted(med.values(), reverse=True)
        for m, v in med.items():
            better = sum(1 for x in vals if x > v)
            equal = sum(1 for x in vals if x == v)
            ranks[m].append(better + (equal + 1) / 2.0)
    return {m: float(np.mean(ranks[m])) for m in meths}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("csv")
    ap.add_argument("--lower-better", action="store_true", help="lower scores are better")
    ap.add_argument("--boot", type=int, default=300, help="bootstrap draws (default 300)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--prior", type=float, default=1.0, help="virtual wins and losses per method (default 1)")
    ap.add_argument("--min-methods", type=int, default=3, help="drop units with fewer rated methods (default 3)")
    ap.add_argument("--coverage", type=float, default=0.6, help="share of tasks a method must cover (default 0.6)")
    ap.add_argument("--min-cols", type=int, default=5,
                    help="minimum number of tasks a method must cover, capped at the number of tasks (default 5)")
    ap.add_argument("--center", type=float, default=1000.0, help="mean rating (default 1000)")
    ap.add_argument("--anchor", help="method whose rating is fixed at --anchor-value instead of centring")
    ap.add_argument("--anchor-value", type=float, default=1500.0)
    ap.add_argument("--pair", nargs=2, action="append", metavar=("A", "B"),
                    help="report the bootstrap share of draws with A rated above B (repeatable)")
    ap.add_argument("--out", help="output TSV (default stdout)")
    a = ap.parse_args(argv)

    ars = read(a.csv, a.lower_better)
    tasks = sorted(set(t for t, _, _ in ars))
    cov = collections.Counter()
    for m, t in set((m, t) for t, _, sc in ars for m in sc):
        cov[m] += 1
    need = min(len(tasks), max(a.min_cols, int(a.coverage * len(tasks))))
    meths = sorted(m for m in cov if cov[m] >= need)
    dropped = sorted(m for m in cov if cov[m] < need)
    print("coverage gate: >= %d of %d tasks -> %d rated, %d excluded%s"
          % (need, len(tasks), len(meths), len(dropped), (" (" + ", ".join(dropped) + ")") if dropped else ""),
          file=sys.stderr)
    keep = set(meths)
    ars = [(t, u, {m: v for m, v in sc.items() if m in keep}) for t, u, sc in ars]
    ars = [x for x in ars if len(x[2]) >= a.min_methods]
    if not ars or len(meths) < 2:
        sys.exit("error: fewer than two rated methods or no usable units")
    idx = {m: i for i, m in enumerate(meths)}
    n = len(meths)
    Ws = []
    for t, u, sc in ars:
        ms = sorted(sc)
        v = np.array([sc[m] for m in ms])
        ii = np.array([idx[m] for m in ms])
        W = np.zeros((n, n))
        gt = (v[:, None] > v[None, :]).astype(float)
        np.fill_diagonal(gt, 0.0)
        W[np.ix_(ii, ii)] = gt
        Ws.append(W)
    Ws = np.array(Ws)
    per_task = collections.Counter(x[0] for x in ars)
    TW = np.array([1.0 / per_task[x[0]] for x in ars])
    TW = TW / TW.sum() * len(ars)
    print("%d units over %d tasks (%s), %d methods, %d games; each task weighted to 1"
          % (len(ars), len(per_task), ", ".join("%s:%d" % (t, per_task[t]) for t in sorted(per_task)),
             n, int(Ws.sum())), file=sys.stderr)

    def shift(r):
        if a.anchor:
            if a.anchor not in idx:
                sys.exit("error: anchor %r is not among the rated methods" % a.anchor)
            return r - r[idx[a.anchor]] + a.anchor_value
        return r + a.center

    point = shift(bt(np.tensordot(TW, Ws, axes=(0, 0)), n, prior=a.prior))
    rng = np.random.default_rng(a.seed)
    strata = [np.flatnonzero([x[0] == t for x in ars]) for t in per_task]
    boots = np.empty((a.boot, n))
    for b in range(a.boot):
        pick = np.concatenate([rng.choice(s, len(s)) for s in strata])
        boots[b] = shift(bt(np.tensordot(TW[pick], Ws[pick], axes=(0, 0)), n, iters=200, prior=a.prior))
    q25, q50, q75 = np.percentile(boots, [25, 50, 75], axis=0)
    top = np.bincount(boots.argmax(1), minlength=n) / float(a.boot)
    ngames = (Ws.sum(0) + Ws.sum(0).T).sum(1)
    win = Ws.sum(0).sum(1) / np.maximum(ngames, 1)
    mr = mean_ranks(ars, keep)

    order = np.argsort(-point)
    fh = open(a.out, "w") if a.out else sys.stdout
    fh.write("rank\tmethod\telo\telo_q25\telo_q75\ttop_share\tmean_rank\ttasks\tgames\twin_rate\n")
    for k, i in enumerate(order, 1):
        m = meths[i]
        fh.write("%d\t%s\t%.0f\t%.0f\t%.0f\t%.3f\t%.2f\t%d\t%d\t%.3f\n"
                 % (k, m, point[i], q25[i], q75[i], top[i], mr[m], cov[m], int(ngames[i]), win[i]))
    if a.out:
        fh.close()
        print("wrote %s" % a.out, file=sys.stderr)
    for A, B in a.pair or []:
        if A not in idx or B not in idx:
            print("pair %s %s: not both rated" % (A, B), file=sys.stderr)
            continue
        share = float((boots[:, idx[A]] > boots[:, idx[B]]).mean())
        print("pair: %s rated above %s in %.1f%% of %d bootstrap draws" % (A, B, 100 * share, a.boot),
              file=sys.stderr)
    by_elo = meths[order[0]]
    by_rank = min(mr, key=mr.get)
    if by_elo != by_rank:
        print("note: first by rating (%s) differs from first by mean rank (%s); claim first only by the "
              "measure on which it holds" % (by_elo, by_rank), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

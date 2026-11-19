#!/usr/bin/env python3
"""Bradley-Terry ratings (Elo scale) and mean rank from paired per-fold games.

Ported from a benchmark report builder used in a foundation-model paper and stripped of its
project specifics. The rules it keeps:

* Games are played PER HELD-OUT FOLD. Folds are identical across methods (one frozen split
  file), so each (task, fold) is a head-to-head arena. That gives many arenas instead of one
  game per task column.
* Ratings are the Bradley-Terry maximum-likelihood fit (MM algorithm, Hunter 2004), which does
  not depend on game order, on the 400/ln10 scale. A symmetric prior of one virtual win and one
  virtual loss against an average player keeps undefeated or winless methods finite.
* Every task gets total weight 1, so a task with many folds does not cast most of the votes.
* Coverage gate: a method is rated only if it played at least --min-columns tasks. A method
  present on one or two easy columns has an easier schedule, not a higher rating.
* Uncertainty is a bootstrap over arenas, stratified within task so the task weights hold in
  every replicate. The IQR and the 2.5 to 97.5 percentile band are reported, plus the share of
  replicates in which each method is rated first.
* Method identity must be canonical before rating: two spellings of one model are two players.
  The script refuses duplicate (task, fold, method) rows; map names with --alias.

Input: a long CSV with columns task, fold, method, score (higher is better unless the task is
listed in --lower-better). Extra columns are ignored. Rows whose score is empty or not a number
are treated as missing runs: they play no game and are counted in the coverage report.

Output: a markdown table on stdout and, with --json, every number in a JSON file.

Dependencies: numpy.

Example:
    python3 bt_rating.py scores.csv --anchor baseline=1500 --json elo.json
    python3 bt_rating.py scores.csv --keep declared_field.txt   # rate only a field declared in advance
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import sys

import numpy as np

SCALE = 400.0 / math.log(10.0)


def read_scores(path, lower_better, alias):
    """Return {(task, fold): {method: score}}, missing-run counts and the set of methods seen."""
    arenas = collections.defaultdict(dict)
    missing = collections.Counter()
    seen = set()
    with open(path, newline="") as fh:
        rd = csv.DictReader(fh)
        need = {"task", "fold", "method", "score"}
        if not need <= set(rd.fieldnames or []):
            sys.exit(f"error: {path} needs columns {sorted(need)}; found {rd.fieldnames}")
        for row in rd:
            m = alias.get(row["method"].strip(), row["method"].strip())
            t, f = row["task"].strip(), row["fold"].strip()
            seen.add(m)
            try:
                v = float(row["score"])
                if math.isnan(v):
                    raise ValueError
            except (TypeError, ValueError):
                missing[(m, t)] += 1
                continue
            key = (t, f)
            if m in arenas[key]:
                sys.exit(f"error: duplicate row for method {m!r} on task {t!r} fold {f!r}. "
                         "Canonicalise method names (--alias) instead of keeping a best-of.")
            arenas[key][m] = -v if t in lower_better else v
    return arenas, missing, seen


def bt(W, n, iters=400, prior=1.0):
    """MM algorithm with a symmetric prior against a fictitious average player."""
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


def mean_rank(arenas, meths):
    """Per task: median score over folds, rank 1 = best (ties share the mean rank); then mean over tasks."""
    by_task = collections.defaultdict(lambda: collections.defaultdict(list))
    for (t, _f), sc in arenas.items():
        for m, v in sc.items():
            if m in meths:
                by_task[t][m].append(v)
    ranks = collections.defaultdict(list)
    for t, d in by_task.items():
        med = {m: float(np.median(v)) for m, v in d.items()}
        order = sorted(med, key=lambda m: -med[m])
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and med[order[j + 1]] == med[order[i]]:
                j += 1
            for k in range(i, j + 1):
                ranks[order[k]].append((i + j) / 2.0 + 1.0)
            i = j + 1
    return {m: (float(np.mean(r)), len(r)) for m, r in ranks.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("csv", help="long CSV with task, fold, method, score")
    ap.add_argument("--lower-better", nargs="*", default=[], metavar="TASK",
                    help="tasks whose score is better when lower (sign is flipped before games)")
    ap.add_argument("--alias", help="CSV with columns from,to that maps method spellings to one name")
    ap.add_argument("--keep", help="text file, one method per line: the field declared before scoring")
    ap.add_argument("--min-columns", type=int, default=None,
                    help="coverage gate in tasks (default: max(5, 60%% of tasks), capped at the task count)")
    ap.add_argument("--min-arena", type=int, default=3, help="smallest number of methods in a game arena")
    ap.add_argument("--anchor", default=None, metavar="METHOD=VALUE",
                    help="pin one method's rating (e.g. baseline=1500); default centres the field at 1000")
    ap.add_argument("--boots", type=int, default=300, help="bootstrap replicates over arenas")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", help="write all numbers here")
    a = ap.parse_args(argv)

    alias = {}
    if a.alias:
        with open(a.alias, newline="") as fh:
            alias = {r["from"].strip(): r["to"].strip() for r in csv.DictReader(fh)}
    arenas, missing, seen = read_scores(a.csv, set(a.lower_better), alias)
    if a.keep:
        with open(a.keep) as fh:
            keep = {ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")}
        unknown = sorted(keep - seen)
        if unknown:
            print(f"warning: declared methods with no rows: {', '.join(unknown)}", file=sys.stderr)
        arenas = {k: {m: v for m, v in sc.items() if m in keep} for k, sc in arenas.items()}

    tasks = sorted({t for t, _ in arenas})
    if not tasks:
        sys.exit("error: no scored rows")
    cov = collections.Counter()
    for m, t in {(m, t) for (t, _f), sc in arenas.items() for m in sc}:
        cov[m] += 1
    need = a.min_columns if a.min_columns is not None else min(len(tasks), max(5, int(0.6 * len(tasks))))
    meths = sorted(m for m in cov if cov[m] >= need)
    dropped = sorted(m for m in cov if cov[m] < need)
    ars = [(t, f, {m: v for m, v in sc.items() if m in set(meths)}) for (t, f), sc in sorted(arenas.items())]
    ars = [x for x in ars if len(x[2]) >= a.min_arena]
    if len(meths) < 2 or not ars:
        sys.exit(f"error: fewer than two methods pass the coverage gate ({need} of {len(tasks)} tasks)")
    idx = {m: i for i, m in enumerate(meths)}
    n = len(meths)
    Ws = []
    for _t, _f, sc in ars:
        ms = sorted(sc)
        v = np.array([sc[m] for m in ms])
        ii = np.array([idx[m] for m in ms])
        W = np.zeros((n, n))
        gt = (v[:, None] > v[None, :]).astype(float)          # row beats column; ties play no game
        np.fill_diagonal(gt, 0.0)
        W[np.ix_(ii, ii)] = gt
        Ws.append(W)
    Ws = np.array(Ws)
    per_task = collections.Counter(x[0] for x in ars)
    TW = np.array([1.0 / per_task[x[0]] for x in ars])
    TW = TW / TW.sum() * len(ars)

    point = bt(np.tensordot(TW, Ws, axes=(0, 0)), n)
    rng = np.random.default_rng(a.seed)
    strata = [np.flatnonzero([x[0] == t for x in ars]) for t in sorted(per_task)]
    boots = np.empty((a.boots, n))
    for b in range(a.boots):
        pick = np.concatenate([rng.choice(s, len(s)) for s in strata])
        boots[b] = bt(np.tensordot(TW[pick], Ws[pick], axes=(0, 0)), n, iters=200)

    if a.anchor:
        name, val = a.anchor.rsplit("=", 1)
        if name not in idx:
            sys.exit(f"error: anchor {name!r} is not among the rated methods")
        shift = float(val) - point[idx[name]]
        point = point + shift
        boots = boots - boots[:, [idx[name]]] + float(val)
    else:
        point = point + 1000.0
        boots = boots + 1000.0
    q = np.percentile(boots, [2.5, 25, 50, 75, 97.5], axis=0)
    first = np.bincount(boots.argmax(1), minlength=n) / a.boots
    games = (Ws.sum(0) + Ws.sum(0).T).sum(1)
    wins = Ws.sum(0).sum(1)
    mr = mean_rank(dict(((t, f), sc) for t, f, sc in ars), set(meths))

    rows = []
    for m in meths:
        i = idx[m]
        rows.append(dict(method=m, rating=float(point[i]), q2_5=float(q[0, i]), q25=float(q[1, i]),
                         q75=float(q[3, i]), q97_5=float(q[4, i]), share_first=float(first[i]),
                         games=int(games[i]), win_rate=float(wins[i] / max(games[i], 1)),
                         tasks_covered=int(cov[m]), mean_rank=mr[m][0], tasks_ranked=mr[m][1]))
    rows.sort(key=lambda r: -r["rating"])

    print(f"arenas: {len(ars)} (one per task x fold); tasks: {len(tasks)}; each task weighted to 1")
    print("arenas per task: " + ", ".join(f"{t}={per_task[t]}" for t in sorted(per_task)))
    print(f"coverage gate: >= {need} of {len(tasks)} tasks; rated {len(meths)}, excluded {len(dropped)}"
          + (f" ({', '.join(dropped)})" if dropped else ""))
    if missing:
        print("missing runs (empty or non-numeric score): "
              + ", ".join(f"{m}@{t} x{c}" for (m, t), c in sorted(missing.items())))
    print(f"bootstrap: {a.boots} replicates over arenas, stratified by task, seed {a.seed}")
    print()
    print("| # | method | rating | IQR | 95% band | first in | mean rank | tasks | games | win rate |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for k, r in enumerate(rows, 1):
        print(f"| {k} | {r['method']} | {r['rating']:.0f} | {r['q25']:.0f} to {r['q75']:.0f} | "
              f"{r['q2_5']:.0f} to {r['q97_5']:.0f} | {100 * r['share_first']:.1f}% | {r['mean_rank']:.2f} | "
              f"{r['tasks_covered']} | {r['games']} | {r['win_rate']:.3f} |")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(rows=rows, tasks=tasks, arenas=len(ars), arenas_per_task=dict(per_task),
                           coverage_gate=need, excluded=dropped,
                           missing={f"{m}@{t}": c for (m, t), c in missing.items()},
                           boots=a.boots, seed=a.seed, anchor=a.anchor), fh, indent=1)
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

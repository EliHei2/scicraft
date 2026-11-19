#!/usr/bin/env python3
"""Thin the richer arm of a comparison to the poorer arm's budget, unit by unit.

Two arms of a comparison often differ in how much input each unit carries (reads per cell, tokens per document,
rows per table). Then a score difference mixes the factor under test with the budget. This script writes a
matched copy of the richer arm in which every unit holds exactly as many counts as the same unit holds in the
poorer arm, so that the published, the matched and the full arm can be scored side by side.

  thin_to_budget.py --rich rich.csv --poor poor.csv --out matched.csv
  thin_to_budget.py --rich rich.csv --budget 500 --out matched.csv      # one fixed budget for every unit
  thin_to_budget.py --rich rich.csv --poor poor.csv --out m.csv --unit cell_id --feature gene --count n --seed 3
  thin_to_budget.py --self-test

Input: long tables with one row per (unit, feature) and a count column. Every other column of the rich table
(fold, label, source) is carried through unchanged, so unit ids and folds stay as they were.

The draw: for each unit, counts are drawn without replacement (multivariate hypergeometric) down to the target
total. The generator is seeded from --seed and the unit id, so the result does not depend on row order and a
rerun gives the same file. A unit that already holds no more than its target is copied unchanged. A unit that is
absent from the poor table is dropped and counted in the report.

Needs numpy. Python 3.9 or later. Exit 0 when every written unit holds min(rich total, target), 1 otherwise.
"""
from __future__ import annotations

import argparse
import csv
import sys
import tempfile
import zlib
from collections import OrderedDict
from pathlib import Path

try:
    import numpy as np
except ImportError as e:  # pragma: no cover
    sys.exit(f"thin_to_budget.py needs numpy ({e})")


def read_long(path: Path, unit: str, feature: str, count: str):
    with open(path, newline="") as f:
        rd = csv.DictReader(f)
        missing = [c for c in (unit, feature, count) if c not in (rd.fieldnames or [])]
        if missing:
            sys.exit(f"{path}: missing column(s) {missing}; found {rd.fieldnames}")
        rows = list(rd)
    return rows, rd.fieldnames


def totals(rows, unit, count):
    out = OrderedDict()
    for r in rows:
        out[r[unit]] = out.get(r[unit], 0) + int(float(r[count]))
    return out


def thin(rows, unit, count, target_of, seed):
    """Return (kept rows, report). target_of(unit id) gives the target total or None to drop the unit."""
    by_unit = OrderedDict()
    for r in rows:
        by_unit.setdefault(r[unit], []).append(r)
    out, rep = [], {"thinned": 0, "unchanged": 0, "dropped": 0, "before": 0, "after": 0, "bad": []}
    for u, rs in by_unit.items():
        counts = np.array([int(float(r[count])) for r in rs], dtype=np.int64)
        tot = int(counts.sum())
        rep["before"] += tot
        target = target_of(u)
        if target is None:
            rep["dropped"] += 1
            continue
        if tot <= target:
            new = counts
            rep["unchanged"] += 1
        else:
            rng = np.random.default_rng([seed, zlib.crc32(str(u).encode())])
            new = rng.multivariate_hypergeometric(counts, target)
            rep["thinned"] += 1
        if int(new.sum()) != min(tot, target):
            rep["bad"].append(u)
        rep["after"] += int(new.sum())
        for r, c in zip(rs, new):
            if c > 0:
                r2 = dict(r)
                r2[count] = str(int(c))
                out.append(r2)
    return out, rep


def run(a) -> int:
    rows, fields = read_long(a.rich, a.unit, a.feature, a.count)
    if a.poor:
        poor_rows, _ = read_long(a.poor, a.unit, a.feature, a.count)
        ptot = totals(poor_rows, a.unit, a.count)
        target_of = lambda u: ptot.get(u)  # noqa: E731
        what = f"the per-unit totals of {a.poor.name}"
    else:
        target_of = lambda u: a.budget  # noqa: E731
        what = f"a budget of {a.budget} per unit"
    out, rep = thin(rows, a.unit, a.count, target_of, a.seed)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    print(f"thin_to_budget: {a.rich.name} thinned to {what} (seed {a.seed})")
    print(f"  units: {rep['thinned']} thinned, {rep['unchanged']} already within budget, {rep['dropped']} dropped "
          f"(absent from the poorer arm)")
    print(f"  counts: {rep['before']} before, {rep['after']} after; wrote {len(out)} rows to {a.out}")
    if rep["bad"]:
        print(f"  ERROR: {len(rep['bad'])} units missed their target: {rep['bad'][:5]}")
        return 1
    return 0


def self_test() -> int:
    rng = np.random.default_rng(0)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        rich, poor = tmp / "rich.csv", tmp / "poor.csv"
        with open(rich, "w", newline="") as fr, open(poor, "w", newline="") as fp:
            wr, wp = csv.writer(fr), csv.writer(fp)
            wr.writerow(["unit", "feature", "count", "fold"])
            wp.writerow(["unit", "feature", "count"])
            for u in range(30):
                for g in range(12):
                    c = int(rng.poisson(8))
                    if c:
                        wr.writerow([f"u{u}", f"f{g}", c, u % 3])
                    c2 = int(rng.poisson(2))
                    if c2 and u != 29:           # unit u29 is absent from the poorer arm
                        wp.writerow([f"u{u}", f"f{g}", c2])
        ns = argparse.Namespace(rich=rich, poor=poor, budget=None, out=tmp / "m1.csv", unit="unit",
                                feature="feature", count="count", seed=5)
        code = run(ns)
        ns2 = argparse.Namespace(**{**vars(ns), "out": tmp / "m2.csv"})
        run(ns2)
        m1 = (tmp / "m1.csv").read_text()
        rows1, _ = read_long(tmp / "m1.csv", "unit", "feature", "count")
        prow, _ = read_long(poor, "unit", "feature", "count")
        rrow, _ = read_long(rich, "unit", "feature", "count")
        t1, tp, tr = totals(rows1, "unit", "count"), totals(prow, "unit", "count"), totals(rrow, "unit", "count")
        checks = [
            ("exit code 0", code == 0),
            ("same seed gives the same file", m1 == (tmp / "m2.csv").read_text()),
            ("every unit holds min(rich, poor)", all(t1.get(u, 0) == min(tr[u], tp[u]) for u in tp)),
            ("the unit absent from the poorer arm is dropped", "u29" not in t1),
            ("no feature count grew", all(int(r["count"]) <= next(int(x["count"]) for x in rrow
                                         if x["unit"] == r["unit"] and x["feature"] == r["feature"]) for r in rows1)),
            ("the fold column is carried through", all(r["fold"] == str(int(r["unit"][1:]) % 3) for r in rows1)),
        ]
    for name, ok in checks:
        print(("ok    " if ok else "WRONG ") + name)
    ok = all(c for _, c in checks)
    print("self-test passed" if ok else "self-test FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rich", type=Path, help="long table of the arm with more counts per unit")
    ap.add_argument("--poor", type=Path, help="long table of the arm with fewer counts per unit")
    ap.add_argument("--budget", type=int, help="fixed target per unit, used when --poor is not given")
    ap.add_argument("--out", type=Path, help="where to write the matched table")
    ap.add_argument("--unit", default="unit", help="name of the unit column (default: unit)")
    ap.add_argument("--feature", default="feature", help="name of the feature column (default: feature)")
    ap.add_argument("--count", default="count", help="name of the count column (default: count)")
    ap.add_argument("--seed", type=int, default=0, help="seed of the draw (default 0)")
    ap.add_argument("--self-test", action="store_true", help="run on generated data and check the result")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.rich or not a.out or (a.poor is None and a.budget is None):
        ap.error("give --rich, --out and either --poor or --budget (or --self-test)")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())

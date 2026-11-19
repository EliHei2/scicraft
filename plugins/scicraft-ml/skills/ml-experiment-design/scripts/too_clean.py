#!/usr/bin/env python3
"""Flag numbers that look too clean in a long results table, before anyone reads it as science.

Input: a CSV with one row per (arm, task) or per (arm, task, fold/seed), with columns named by the flags below.
Checks:
  1. identical arms: two arms whose values agree on every shared task to --decimals places
     (did they load the same checkpoint?);
  2. identical SD column: within a task, three or more arms report the same SD to --decimals places
     (is the SD over folds, or computed once?);
  3. coverage holes: an arm missing tasks that other arms have (a claim over "every task" covers only what ran);
  4. constant arm: one arm with the same value on every task;
  5. with --arrays, files with identical content (hash), e.g. embeddings or prediction files per arm.
When the table has a fold or seed column, values are averaged per (arm, task) for checks 1 and 4, and the SD per
(arm, task) is computed from them when no SD column is given.

Dependencies: Python 3.9+ standard library only.

Example:
    python3 too_clean.py results.csv --arm method --task task --value score --sd sd --decimals 3
    python3 too_clean.py results.csv --arrays runs/*/emb.npy

Exit codes: 0 nothing flagged; 1 at least one flag (each is a bug until cleared); 2 bad input.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import statistics
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("table", nargs="?", help="long CSV of results")
    ap.add_argument("--arm", default="arm", help="column naming the arm or method (default: arm)")
    ap.add_argument("--task", default="task", help="column naming the task (default: task)")
    ap.add_argument("--value", default="value", help="column with the score (default: value)")
    ap.add_argument("--sd", help="column with a reported SD (optional)")
    ap.add_argument("--rep", help="column with fold or seed id when rows are per replicate (optional)")
    ap.add_argument("--decimals", type=int, default=3, help="agreement precision (default: 3)")
    ap.add_argument("--arrays", nargs="*", default=[], help="files to compare by content hash")
    a = ap.parse_args(argv)
    if not a.table and not a.arrays:
        ap.print_help()
        return 2

    flags: list[str] = []
    rnd = lambda x: round(x, a.decimals)  # noqa: E731

    if a.table:
        with open(a.table, newline="") as f:
            rows = list(csv.DictReader(f))
        need = [a.arm, a.task, a.value] + ([a.sd] if a.sd else []) + ([a.rep] if a.rep else [])
        missing = [c for c in need if rows and c not in rows[0]]
        if not rows or missing:
            print(f"FAIL  {a.table}: empty or missing column(s) {missing}")
            return 2
        vals: dict = defaultdict(list)
        sds: dict = {}
        for r in rows:
            if r[a.value].strip() in ("", "nan", "NaN", "NA"):
                continue
            key = (r[a.arm], r[a.task])
            vals[key].append(float(r[a.value]))
            if a.sd and r[a.sd].strip() not in ("", "nan", "NaN", "NA"):
                sds[key] = float(r[a.sd])
        if a.rep and not a.sd:
            sds = {k: statistics.stdev(v) for k, v in vals.items() if len(v) > 1}
        mean = {k: statistics.fmean(v) for k, v in vals.items()}
        arms = sorted({k[0] for k in mean})
        tasks = sorted({k[1] for k in mean})
        per_arm = {arm: {t: mean[(arm, t)] for t in tasks if (arm, t) in mean} for arm in arms}

        for x, y in combinations(arms, 2):
            shared = sorted(set(per_arm[x]) & set(per_arm[y]))
            if len(shared) >= 2 and all(rnd(per_arm[x][t]) == rnd(per_arm[y][t]) for t in shared):
                flags.append(f"identical arms: {x} and {y} agree to {a.decimals} decimals on all {len(shared)} "
                             f"shared tasks; check that they loaded different checkpoints")
        for t in tasks:
            col = defaultdict(list)
            for arm in arms:
                if (arm, t) in sds:
                    col[rnd(sds[(arm, t)])].append(arm)
            for sdv, who in col.items():
                if len(who) >= 3:
                    flags.append(f"identical SD column: task {t}, SD {sdv} reported by {len(who)} arms "
                                 f"({', '.join(who)}); check what the SD is taken over")
        for arm in arms:
            hole = [t for t in tasks if t not in per_arm[arm]]
            if hole:
                flags.append(f"coverage hole: {arm} has no value for {', '.join(hole)}; claims over every task "
                             f"cover only {len(tasks) - len(hole)} of {len(tasks)}")
            v = list(per_arm[arm].values())
            if len(v) >= 3 and len({rnd(x) for x in v}) == 1:
                flags.append(f"constant arm: {arm} scores {rnd(v[0])} on all {len(v)} tasks")
        print(f"checked {len(arms)} arms x {len(tasks)} tasks from {a.table}")

    if a.arrays:
        by: dict = defaultdict(list)
        for p in a.arrays:
            by[sha(Path(p))].append(p)
        for h, ps in by.items():
            if len(ps) > 1:
                flags.append(f"identical files: {', '.join(ps)} (sha256 {h[:12]})")
        print(f"hashed {len(a.arrays)} file(s)")

    for fl in flags:
        print(f"FLAG  {fl}")
    print(f"{'FAIL' if flags else 'OK'}  {len(flags)} flag(s); each is a bug until cleared")
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())

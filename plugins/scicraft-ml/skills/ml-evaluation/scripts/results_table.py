#!/usr/bin/env python3
"""Build a results table from per-fold records: raw values, spread, fold counts, explicit statuses,
column definitions, and the too-clean checks run before anyone reads it.

What it enforces:
* Every cell is the raw metric (median over folds) with its spread (sample SD over folds, ddof 1)
  and the number of folds behind it. No normalisation, no rescaling to a best method.
* A missing run is a status, never a blank: each (method, task) without scores prints the status
  given in the status column (OOM, TIMEOUT, CRASH, NOT_ATTEMPTED, ...) or "missing" when none was
  recorded. Coverage per method is printed.
* Too-clean checks, printed as warnings: identical SDs down a column, identical medians for two
  methods on a task, a cell with fewer folds than the task's maximum, and any score outside a
  declared range.
* Column definitions are printed under the table from a definitions file (task, definition), and
  the table refuses to print a task with no definition when --require-defs is set.
* Rows are grouped by an optional family column (pretrained, fitted on eval data, baselines,
  controls) in the order the families first appear.

Input: long CSV with columns task, fold, method, score and optionally status, family. Output:
markdown on stdout; --latex writes a self-terminating LaTeX fragment (it ends with \\bottomrule
and never starts with \\rowcolor, which avoids the "Misplaced \\noalign" error when the fragment
is \\input after a header).

Dependencies: Python standard library.

Example:
    python3 results_table.py scores.csv --defs columns.csv --require-defs --latex tab_results.tex
"""
from __future__ import annotations

import argparse
import collections
import csv
import math
import statistics as st
import sys


def read(path):
    cells = collections.defaultdict(list)
    status = {}
    family = {}
    tasks, methods = [], []
    with open(path, newline="") as fh:
        rd = csv.DictReader(fh)
        if not {"task", "fold", "method", "score"} <= set(rd.fieldnames or []):
            sys.exit("error: CSV needs columns task, fold, method, score")
        for r in rd:
            t, m = r["task"].strip(), r["method"].strip()
            if t not in tasks:
                tasks.append(t)
            if m not in methods:
                methods.append(m)
            if r.get("family"):
                family.setdefault(m, r["family"].strip())
            try:
                v = float(r["score"])
                if math.isnan(v):
                    raise ValueError
                cells[(m, t)].append(v)
            except (TypeError, ValueError):
                if r.get("status"):
                    status[(m, t)] = r["status"].strip()
                else:
                    status.setdefault((m, t), "missing")
    return cells, status, family, tasks, methods


def fmt(vals, nd):
    med = st.median(vals)
    if len(vals) > 1:
        return f"{med:.{nd}f} ± {st.stdev(vals):.{nd}f} (n={len(vals)})"
    return f"{med:.{nd}f} (n=1, no spread)"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("csv")
    ap.add_argument("--defs", help="CSV with columns task, definition (data, labels, split, probe, metric)")
    ap.add_argument("--require-defs", action="store_true", help="fail when a task has no definition")
    ap.add_argument("--digits", type=int, default=3)
    ap.add_argument("--range", nargs=2, type=float, metavar=("LO", "HI"), help="declared metric range")
    ap.add_argument("--latex", help="write a LaTeX row fragment here")
    a = ap.parse_args(argv)
    cells, status, family, tasks, methods = read(a.csv)
    defs = {}
    if a.defs:
        with open(a.defs, newline="") as fh:
            defs = {r["task"].strip(): r["definition"].strip() for r in csv.DictReader(fh)}
    undefined = [t for t in tasks if t not in defs]
    if a.require_defs and undefined:
        sys.exit(f"error: no definition for task(s): {', '.join(undefined)}")

    fams = []
    for m in methods:
        f = family.get(m, "")
        if f not in fams:
            fams.append(f)
    order = [m for f in fams for m in methods if family.get(m, "") == f]

    warn = []
    for t in tasks:
        sds = {m: round(st.stdev(cells[(m, t)]), 6) for m in order if len(cells.get((m, t), [])) > 1}
        if len(sds) >= 3:
            sd_v, sd_n = collections.Counter(sds.values()).most_common(1)[0]
            if sd_n >= 3:
                same = [m for m, v in sds.items() if v == sd_v]
                warn.append(f"{t}: {sd_n} of {len(sds)} methods share SD {sd_v} ({', '.join(same)}); "
                            "check the SD is over folds and not over seeds of one fold")
        meds = collections.defaultdict(list)
        for m in order:
            if cells.get((m, t)):
                meds[round(st.median(cells[(m, t)]), 6)].append(m)
        for v, ms in meds.items():
            if len(ms) > 1:
                warn.append(f"{t}: identical medians {v} for {', '.join(ms)}; check they loaded different checkpoints")
        nmax = max((len(cells.get((m, t), [])) for m in order), default=0)
        for m in order:
            k = len(cells.get((m, t), []))
            if 0 < k < nmax:
                warn.append(f"{t}: {m} has {k} of {nmax} folds; the cell is not comparable as printed")
            if a.range and any(not (a.range[0] <= v <= a.range[1]) for v in cells.get((m, t), [])):
                warn.append(f"{t}: {m} has a score outside the declared range {a.range}")

    head = "| family | method | " + " | ".join(tasks) + " | coverage |"
    print(head)
    print("|" + "---|" * (len(tasks) + 3))
    tex = []
    for m in order:
        row, trow, got = [], [], 0
        for t in tasks:
            v = cells.get((m, t))
            if v:
                got += 1
                row.append(fmt(v, a.digits))
                sd = f" $\\pm$ {st.stdev(v):.{a.digits}f}" if len(v) > 1 else ""
                trow.append(f"{st.median(v):.{a.digits}f}{sd}")
            else:
                s = status.get((m, t), "not run")
                row.append(s)
                trow.append(f"\\textit{{{s}}}")
        print(f"| {family.get(m, '')} | {m} | " + " | ".join(row) + f" | {got}/{len(tasks)} |")
        tex.append(f"{family.get(m, '')} & {m} & " + " & ".join(trow) + r" \\")
    print("\nCells: median over held-out folds ± sample SD of the fold scores (ddof 1), n = folds scored.")
    if defs:
        print("\nColumn definitions:")
        for t in tasks:
            print(f"- {t}: {defs.get(t, 'NO DEFINITION GIVEN')}")
    if warn:
        print("\nWarnings (too-clean or incomplete; resolve or explain before the table is shared):")
        for w in warn:
            print(f"- {w}")
    if a.latex:
        with open(a.latex, "w") as fh:
            fh.write("\n".join(tex).replace("_", r"\_") + "\n\\bottomrule\n")
        print(f"\nwrote {a.latex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

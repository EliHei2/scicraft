#!/usr/bin/env python3
"""Audit a method x dataset results table before it becomes a comparison or scaling figure.

The rule it enforces: every (method, dataset) cell is either a measured value read from a
named source, or an explicit failure with its kind. A run on a subset or crop counts as not
run. A value that was never recorded is a gap: fetch it, or drop that dataset for every
method, so that all methods are drawn on the same set. Nothing is estimated.

Input: a TSV with one row per method x dataset and these columns
    method, dataset, value, failure_kind, source
value is empty when failure_kind is set. failure_kind is one of
    OOM, TIMEOUT, FAILED, SUBSET, NOT_ATTEMPTED   drawn as a failure mark (a red x)
    NOT_RECORDED                                  ran on the full data, number missing: a gap
Optional columns: x (the quantity on the x axis, e.g. dataset size, used to order datasets),
n_items (row or item count the run saw, checked for truncation-like round numbers).

    python coverage_audit.py results.tsv
    python coverage_audit.py results.tsv --methods ours,base_a,base_b --report AUDIT.md --plot-table plot.tsv

Checks, one line per problem:
  * a missing (method, dataset) row, or a duplicate;
  * a row with both a value and a failure kind (a failure drawn as a measurement), or neither;
  * an unknown failure kind; a measured value with no source;
  * NOT_RECORDED gaps, with the datasets to fetch or to drop for all methods;
  * unequal mark counts per method;
  * n_items that is a round power of ten (1,000,000 is the classic truncated export);
    reported as CHECK without failing, since a person has to compare it with the source.
--plot-table writes method, dataset, x, value, mark (point | failure | none) and segment:
consecutive points share a segment, and a failure or gap starts a new one, so a renderer
joins points only where they are connectable.

Exit 1 if any problem was found (gaps included, unless --allow-gaps). Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

FAILURE = {"OOM", "TIMEOUT", "FAILED", "SUBSET", "NOT_ATTEMPTED"}
GAP = {"NOT_RECORDED"}


def read(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    need = {"method", "dataset", "value", "failure_kind", "source"}
    if rows and not need <= set(rows[0]):
        sys.exit(f"{path}: missing columns {sorted(need - set(rows[0]))}")
    return rows


def roundish(n: str) -> bool:
    try:
        v = float(n)
    except ValueError:
        return False
    return v >= 1e4 and math.log10(v).is_integer()


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit a method x dataset results table for coverage and failure marks.")
    ap.add_argument("table", type=Path, help="TSV: method, dataset, value, failure_kind, source[, x, n_items]")
    ap.add_argument("--methods", help="comma list of expected methods, in display order (default: as found)")
    ap.add_argument("--datasets", help="comma list of expected datasets (default: as found)")
    ap.add_argument("--report", type=Path, help="write a markdown audit with the status matrix")
    ap.add_argument("--plot-table", type=Path, help="write a plot-ready TSV with marks and line segments")
    ap.add_argument("--allow-gaps", action="store_true", help="report NOT_RECORDED gaps without failing")
    a = ap.parse_args()

    rows = read(a.table)
    methods = a.methods.split(",") if a.methods else list(dict.fromkeys(r["method"] for r in rows))
    datasets = a.datasets.split(",") if a.datasets else list(dict.fromkeys(r["dataset"] for r in rows))
    xs = {r["dataset"]: r.get("x", "") for r in rows if r.get("x")}
    if xs and all(d in xs for d in datasets):
        datasets.sort(key=lambda d: float(xs[d]))

    cell: dict[tuple[str, str], dict] = {}
    problems: list[str] = []
    checks: list[str] = []  # reported, not failed: a person has to look
    for r in rows:
        k = (r["method"], r["dataset"])
        if k in cell:
            problems.append(f"duplicate row for {k}")
        cell[k] = r

    status: dict[tuple[str, str], str] = {}
    gaps: list[tuple[str, str]] = []
    for m in methods:
        for d in datasets:
            r = cell.get((m, d))
            if r is None:
                problems.append(f"no row for method={m} dataset={d}")
                status[(m, d)] = "MISSING"
                gaps.append((m, d))
                continue
            v, fk = r["value"].strip(), r["failure_kind"].strip().upper()
            if v and fk:
                problems.append(f"{m} / {d}: has value {v} and failure {fk}; a failure is never drawn as a measurement")
            elif not v and not fk:
                problems.append(f"{m} / {d}: neither value nor failure kind")
            elif fk and fk not in FAILURE | GAP:
                problems.append(f"{m} / {d}: unknown failure kind {fk} (allowed: {sorted(FAILURE | GAP)})")
            elif v and not r["source"].strip():
                problems.append(f"{m} / {d}: value {v} has no source file or log")
            if r.get("n_items") and roundish(r["n_items"]):
                checks.append(f"{m} / {d}: n_items = {r['n_items']} is a round power of ten; compare with the source's row count")
            status[(m, d)] = fk if fk else ("ok" if v else "?")
            if fk in GAP:
                gaps.append((m, d))

    marks = {m: sum(status[(m, d)] in {"ok"} | FAILURE for d in datasets) for m in methods}
    if len(set(marks.values())) > 1:
        problems.append(f"unequal mark counts per method: {marks}")
    gap_sets = sorted({d for _, d in gaps})
    gap_msg = ""
    if gaps:
        gap_msg = (f"{len(gaps)} gap(s): fetch {', '.join(f'{m}/{d}' for m, d in gaps)}; "
                   f"or drop dataset(s) {gap_sets} for every method")

    # console
    w = max(len(m) for m in methods) + 2
    print("status matrix (ok = measured; failure kinds drawn as x; NOT_RECORDED/MISSING = gap)")
    print(" " * w + "  ".join(d[:12].ljust(12) for d in datasets))
    for m in methods:
        print(m.ljust(w) + "  ".join(status[(m, d)][:12].ljust(12) for d in datasets))
    print(f"\nmarks per method: {marks}")
    for p in problems:
        print(f"PROBLEM  {p}")
    for c in checks:
        print(f"CHECK    {c}")
    if gap_msg:
        print(f"{'NOTE' if a.allow_gaps else 'PROBLEM'}  {gap_msg}")

    if a.report:
        lines = ["# Coverage audit", "", f"Source table: `{a.table.name}`", "",
                 "| method | " + " | ".join(datasets) + " |", "|---|" + "---|" * len(datasets)]
        for m in methods:
            lines.append(f"| {m} | " + " | ".join(status[(m, d)] for d in datasets) + " |")
        lines += ["", f"Marks per method: {marks}", ""]
        lines += [f"- {p}" for p in problems] + ([f"- {gap_msg}"] if gap_msg else [])
        lines += [f"- Check: {c}" for c in checks]
        if not problems and not gaps:
            lines.append("- No problems: every cell is a measured value with a source or a named failure.")
        a.report.write_text("\n".join(lines) + "\n")
        print(f"wrote {a.report}")

    if a.plot_table:
        out = ["method\tdataset\tx\tvalue\tmark\tsegment"]
        for m in methods:
            seg, prev_point = 0, False
            for d in datasets:
                st, r = status[(m, d)], cell.get((m, d), {})
                mark = "point" if st == "ok" else ("failure" if st in FAILURE else "none")
                if mark == "point" and not prev_point:
                    seg += 1
                prev_point = mark == "point"
                out.append(f"{m}\t{d}\t{xs.get(d, '')}\t{r.get('value', '') if mark == 'point' else ''}\t{mark}\t{seg if mark == 'point' else ''}")
        a.plot_table.write_text("\n".join(out) + "\n")
        print(f"wrote {a.plot_table}")

    failed = bool(problems) or (bool(gaps) and not a.allow_gaps)
    print("coverage audit passed" if not failed else "coverage audit FAILED")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Stage the files of a deposit (supplementary tables, source data) from an explicit whitelist, and nothing else.

    python3 stage_whitelist.py <whitelist.tsv> --src <folder> --out <staging folder> [--max-files 15]
                               [--max-rows 5000]

The whitelist is a TSV with columns `source` (path under --src) and `published` (the name in the deposit, in the
naming scheme the co-authors already use). One row per file; lines starting with # are ignored.

It empties the staging folder (only one it created before, marked by a .staged file), copies each listed file
under its published name, and reports for each table its rows and columns. It fails (exit 1) when a listed file is
missing, two rows publish the same name, or a CSV/TSV has an empty header or a blank first column name (a pandas
index column). It warns when the deposit holds more files than --max-files (default 15: the size of the reference
sets that were accepted) or a table has more rows than --max-rows (default 5000), the shape of a per-unit dump
(per-cell coordinates, per-sample predictions) that belongs in a data deposit, not in the tables.
Standard library only. Nothing is uploaded.
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

MARK = ".staged"


def table_shape(path: Path):
    delim = "\t" if path.suffix.lower() in (".tsv", ".tab") else ","
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=delim)
        header = next(reader, [])
        n = sum(1 for _ in reader)
    return header, n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("whitelist", type=Path)
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-files", type=int, default=15)
    ap.add_argument("--max-rows", type=int, default=5000)
    a = ap.parse_args()
    src, out = a.src.resolve(), a.out.resolve()
    if out == src or out in src.parents:
        print("--out must not be --src or a folder that contains it")
        return 2
    if out.exists() and any(out.iterdir()) and not (out / MARK).exists():
        print(f"{out} exists, is not empty and was not made by this script; choose a new staging folder")
        return 2

    pairs, errors, warns = [], [], []
    for n, line in enumerate(a.whitelist.read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            errors.append(f"whitelist line {n}: needs two tab-separated columns")
            continue
        if parts[0].strip() == "source" and parts[1].strip() == "published":
            continue
        pairs.append((parts[0].strip(), parts[1].strip()))
    names = [p for _, p in pairs]
    for dup in sorted({x for x in names if names.count(x) > 1}):
        errors.append(f"published name used twice: {dup}")
    for s, _ in pairs:
        if not (src / s).is_file():
            errors.append(f"missing: {s}")
    if errors:
        print("\n".join(errors))
        return 1

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARK).write_text("made by stage_whitelist.py; the whole folder is replaced on every run\n")
    for s, p in pairs:
        shutil.copy2(src / s, out / p)
        info = ""
        if Path(p).suffix.lower() in (".csv", ".tsv", ".tab"):
            header, rows = table_shape(out / p)
            info = f"  ({rows} rows x {len(header)} columns)"
            if not header:
                errors.append(f"{p}: empty file or no header")
            elif not header[0].strip():
                errors.append(f"{p}: first column has no name (an index column was written)")
            if rows > a.max_rows:
                warns.append(f"{p}: {rows} rows, more than {a.max_rows}; is this a per-unit dump that belongs in the "
                             "data deposit?")
        print(f"{s}  ->  {p}{info}")
    if len(pairs) > a.max_files:
        warns.append(f"{len(pairs)} files, more than {a.max_files}; match the count of the co-authors' existing files")
    for w in warns:
        print("WARN  " + w)
    for e in errors:
        print("FAIL  " + e)
    print(f"{len(pairs)} files staged in {out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

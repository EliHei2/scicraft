#!/usr/bin/env python3
"""Verify a contract file handed from one repository to another against its frozen reference copy.

The upstream repository (runs, metrics) writes one long-format table; the downstream repository (figures, paper)
reads only that table. This check runs on every regeneration and fails on any drift it was not told about:

- schema: the header equals the expected columns, in order;
- vocabulary: every id in the id columns is one the vocabulary file lists (one source of truth for names);
- grid: with "grid" set, every combination of those columns appears exactly once (no missing cell, no duplicate);
- bytes: the file's hash equals the reference's hash. A legitimate change is recorded by refreshing the reference
  and writing the new hash and date in the provenance log: visible drift, never silent drift.

Vocabulary file (JSON):

    {
      "columns": ["method", "dataset", "metric", "value", "ci95"],
      "ids": {"method": ["ours", "vit_b"], "dataset": ["imagenet_val", "cifar100"], "metric": ["acc", "ece"]},
      "grid": ["method", "dataset", "metric"]
    }

Usage:
    python3 verify_contract.py --actual results/aggregate/scoreboard.tsv --reference reference/scoreboard.tsv \\
        --vocab vocab.json
    python3 verify_contract.py ... --allow-drift      # schema and vocabulary only (prints OK_SCHEMA_ONLY)
    python3 verify_contract.py ... --hash md5

Exit status 0 on OK, 1 on any error. Standard library only. Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path


def read_table(path: Path) -> tuple[list[str], list[dict]]:
    delim = "," if path.suffix == ".csv" else "\t"
    with path.open(newline="") as fh:
        r = csv.DictReader(fh, delimiter=delim)
        return list(r.fieldnames or []), list(r)


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(path: Path, vocab: dict) -> list[str]:
    errs = []
    header, rows = read_table(path)
    want = vocab.get("columns")
    if want and header != want:
        errs.append(f"{path}: header {header} != expected {want}")
    for col, ids in vocab.get("ids", {}).items():
        unknown = sorted({r.get(col, "") for r in rows} - set(ids))
        if unknown:
            errs.append(f"{path}: column {col!r} has ids not in the vocabulary: {unknown[:10]}")
    grid = vocab.get("grid")
    if grid:
        keys = [tuple(r.get(c, "") for c in grid) for r in rows]
        dup = sorted(k for k, n in Counter(keys).items() if n > 1)
        expected = set(itertools.product(*(vocab["ids"][c] for c in grid)))
        missing, extra = sorted(expected - set(keys)), sorted(set(keys) - expected)
        if dup:
            errs.append(f"{path}: duplicate {'/'.join(grid)} keys: {dup[:10]}")
        if missing:
            errs.append(f"{path}: missing keys: {missing[:10]} (n={len(missing)})")
        if extra:
            errs.append(f"{path}: extra keys: {extra[:10]} (n={len(extra)})")
        if len(rows) != len(expected):
            errs.append(f"{path}: row count {len(rows)} != expected {len(expected)}")
    return errs


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--actual", type=Path, required=True, help="the regenerated contract table (.tsv or .csv)")
    p.add_argument("--reference", type=Path, required=True, help="the frozen reference copy")
    p.add_argument("--vocab", type=Path, required=True, help="JSON vocabulary: columns, ids per column, grid")
    p.add_argument("--hash", default="sha256", choices=["sha256", "md5"], help="hash used for the byte check")
    p.add_argument("--allow-drift", action="store_true", help="pass when only the bytes differ (values changed)")
    a = p.parse_args()

    vocab = json.loads(a.vocab.read_text())
    errs = []
    for path in (a.actual, a.reference):
        if not path.is_file():
            errs.append(f"missing table: {path}")
        else:
            errs += check(path, vocab)
    if errs:
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    ha, hr = digest(a.actual, a.hash), digest(a.reference, a.hash)
    if ha != hr and not a.allow_drift:
        print(f"ERROR: {a.hash} drift: actual {ha} != reference {hr}. If the change is intended, refresh the "
              f"reference and log the new hash and date in the provenance file.", file=sys.stderr)
        return 1
    n = len(read_table(a.actual)[1])
    print(f"{'OK' if ha == hr else 'OK_SCHEMA_ONLY'}: rows={n} {a.hash}={ha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Prove that a number reads the same everywhere it appears: main figure, supplement, caption, text.

Two modes.

claims: every number a reader sees, checked against the canonical table.
    canonical TSV: columns key, value (one row per canonical number; the master table)
    claims TSV:    columns where, key, shown[, scale]
        where  the place the number is printed ("Fig 2c bar", "caption line 4", "Supp 3 default")
        shown  the string as printed ("0.81", "85.5%", "1,204")
        scale  optional factor applied to the canonical value first (100 for a fraction shown as %)
    A claim passes when the canonical value, scaled and rounded to the decimals printed, equals it.

    python number_parity.py claims --canonical master.tsv --claims claims.tsv

diff: two tables that should agree row for row (the shipped figure table against the table
rebuilt from the named upstream sources; a supplement's default rows against the main table).
    python number_parity.py diff shipped.tsv rebuilt.tsv --key method,dataset --sig 10

Rows are matched on the key columns; every shared numeric column is compared at --sig
significant digits. Reports rows present in only one table and each disagreeing cell.

Exit 1 on any mismatch. Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path


def read(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def parse_shown(s: str) -> tuple[Decimal, int]:
    t = s.strip().replace(",", "").replace("−", "-").rstrip("%").strip()
    d = Decimal(t)
    decimals = -d.as_tuple().exponent if d.as_tuple().exponent < 0 else 0
    return d, decimals


def claims(a: argparse.Namespace) -> int:
    canon = {r["key"]: r["value"] for r in read(a.canonical)}
    bad = 0
    for r in read(a.claims):
        k, where = r["key"], r["where"]
        if k not in canon:
            print(f"MISMATCH  {where}: key '{k}' is not in the canonical table")
            bad += 1
            continue
        shown, dec = parse_shown(r["shown"])
        val = Decimal(canon[k]) * Decimal(r.get("scale") or "1")
        want = val.quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)
        if want != shown:
            print(f"MISMATCH  {where}: shows {r['shown']}, canonical {k} = {canon[k]} reads {want}")
            bad += 1
        else:
            print(f"ok        {where}: {r['shown']} = {k}")
    print(f"\n{bad} mismatch(es)")
    return 1 if bad else 0


def same(x: str, y: str, sig: int) -> bool:
    try:
        fx, fy = float(x), float(y)
    except ValueError:
        return x.strip() == y.strip()
    if math.isnan(fx) or math.isnan(fy):
        return math.isnan(fx) and math.isnan(fy)
    return f"{fx:.{sig - 1}e}" == f"{fy:.{sig - 1}e}"


def diff(a: argparse.Namespace) -> int:
    keys = a.key.split(",")
    A, B = read(a.left), read(a.right)
    idx = lambda rows: {tuple(r[k] for k in keys): r for r in rows}  # noqa: E731
    ia, ib = idx(A), idx(B)
    cols = [c for c in (A[0].keys() if A else []) if c in (B[0] if B else {}) and c not in keys]
    bad = 0
    for k in sorted(set(ia) - set(ib)):
        print(f"ONLY LEFT   {dict(zip(keys, k))}")
        bad += 1
    for k in sorted(set(ib) - set(ia)):
        print(f"ONLY RIGHT  {dict(zip(keys, k))}")
        bad += 1
    shared = sorted(set(ia) & set(ib))
    for k in shared:
        for c in cols:
            if not same(ia[k][c], ib[k][c], a.sig):
                print(f"DIFFERS     {dict(zip(keys, k))} {c}: {ia[k][c]} vs {ib[k][c]}")
                bad += 1
    print(f"\n{len(shared)} shared row(s), {len(cols)} compared column(s) at {a.sig} significant digits: {bad} problem(s)")
    return 1 if bad else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Check printed numbers against a canonical table, or diff two tables.")
    sub = ap.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("claims", help="check printed numbers against the canonical table")
    c.add_argument("--canonical", type=Path, required=True, help="TSV with key, value")
    c.add_argument("--claims", type=Path, required=True, help="TSV with where, key, shown[, scale]")
    d = sub.add_parser("diff", help="row-wise diff of two tables at N significant digits")
    d.add_argument("left", type=Path)
    d.add_argument("right", type=Path)
    d.add_argument("--key", required=True, help="comma list of key columns")
    d.add_argument("--sig", type=int, default=10, help="significant digits (default 10)")
    a = ap.parse_args()
    sys.exit(claims(a) if a.mode == "claims" else diff(a))


if __name__ == "__main__":
    main()

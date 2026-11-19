#!/usr/bin/env python3
"""Check that two tables join on a key, and show what a join by row position would do.

A join by position (concatenating columns, assigning an array to a column, zipping two
lists) is correct only while both sides keep the same rows in the same order. Streaming
writers, filters, group-bys and parallel readers change the order or drop rows without an
error. In one real case a key dropped during a streaming join left 0.2% of rows correctly
paired; in another, an index assigned after a filter on one side and before it on the
other paired 0.065% of rows correctly, and nothing failed. This script makes that visible.

What it checks, in order:
  1. the key exists on both sides; nulls and duplicate keys are counted
     (duplicates on LEFT are an error; on RIGHT they are an error unless --many-to-one)
  2. overlap: share of LEFT keys found in RIGHT and of RIGHT keys found in LEFT; the run
     aborts (exit 2) when the smaller share is below --min-overlap
  3. positional pairing: for the rows both sides have, how often row i of LEFT carries the
     same key as row i of RIGHT. Below 100%, any join by position is wrong
  4. index space: when RIGHT's key is exactly 0..n-1 while LEFT has more rows, the index
     was probably assigned after a filter
  5. exact invariants: for every --compare column present on both sides, the number of
     key-joined rows whose values differ. It must be 0 (exit 1 otherwise); a ratio bound
     hides small offsets (a 0.9x guard once passed a 0.25% offset)
  6. order independence: the key join repeated on shuffled copies of both sides must give
     the same result, hashed

Use --left-row-index NAME when LEFT is the raw table and the key is its row position: the
script then assigns NAME = 0..n-1 to LEFT before reading anything else, the way a raw scan
must be indexed before any filter.

Examples:
  python3 check_join.py features.parquet preds.csv --key user_id --compare label
  python3 check_join.py raw.parquet derived.parquet --left-row-index row_index --key row_index \\
      --compare x --compare y --min-overlap 0.5

Formats: .parquet, .csv, .tsv (by extension). Needs polars (pip install polars). Reads only
the key and --compare columns. Exit codes: 0 all checks pass, 1 an invariant failed,
2 structural failure (missing key, overlap below threshold, duplicate keys).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import polars as pl
except ImportError:  # pragma: no cover
    sys.exit("check_join.py needs polars: pip install polars")


def scan(path: Path) -> pl.LazyFrame:
    s = path.suffix.lower()
    if s == ".parquet":
        return pl.scan_parquet(path)
    if s in (".csv", ".tsv"):
        return pl.scan_csv(path, separator="\t" if s == ".tsv" else ",", infer_schema_length=10000)
    sys.exit(f"unsupported file type: {path}")


def collect(lf: pl.LazyFrame) -> pl.DataFrame:
    try:
        return lf.collect(engine="streaming")
    except TypeError:
        try:
            return lf.collect(streaming=True)
        except TypeError:
            return lf.collect()


def frame_hash(df: pl.DataFrame, key: str) -> int:
    return int(df.sort(key).hash_rows().sum())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check a key join and its dependence on row order.",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("left", type=Path)
    p.add_argument("right", type=Path)
    p.add_argument("--key", required=True, help="key column (on RIGHT, and on LEFT unless --left-key)")
    p.add_argument("--left-key", default=None, help="key column on LEFT if it has another name")
    p.add_argument("--left-row-index", default=None, metavar="NAME",
                   help="assign NAME = 0..n-1 to LEFT before reading (LEFT is the raw table)")
    p.add_argument("--compare", action="append", default=[], metavar="COL",
                   help="column on both sides that must be equal after the key join (repeatable)")
    p.add_argument("--tolerance", type=float, default=0.0, help="absolute tolerance for numeric --compare")
    p.add_argument("--min-overlap", type=float, default=0.5,
                   help="abort when the smaller overlap share is below this (default 0.5)")
    p.add_argument("--many-to-one", action="store_true", help="allow duplicate keys on RIGHT")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)

    lkey = a.left_key or a.key
    left = scan(a.left)
    if a.left_row_index:
        left = left.with_row_index(a.left_row_index)
        lkey = a.left_row_index
    right = scan(a.right)
    lcols, rcols = left.collect_schema().names(), right.collect_schema().names()
    if lkey not in lcols or a.key not in rcols:
        print(f"FAIL key missing: LEFT has {lkey in lcols}, RIGHT has {a.key in rcols}")
        return 2
    comps = [c for c in a.compare if c in lcols and c in rcols]
    for c in a.compare:
        if c not in comps:
            print(f"warn  --compare {c} is not on both sides; skipped")
    L = collect(left.select([lkey, *comps]).rename({lkey: "__k"}))
    R = collect(right.select([a.key, *comps]).rename({a.key: "__k"}))
    status = 0
    print(f"rows  LEFT {L.height:,}  RIGHT {R.height:,}")

    # 1. nulls and duplicates
    for name, df in (("LEFT", L), ("RIGHT", R)):
        nn = df["__k"].null_count()
        dup = df.height - nn - df["__k"].drop_nulls().n_unique()
        print(f"key   {name}: {nn:,} null, {dup:,} duplicate")
        if dup and (name == "LEFT" or not a.many_to_one):
            print(f"FAIL  duplicate keys on {name}: a join would multiply rows")
            status = 2

    # 2. overlap
    lk, rk = L["__k"].drop_nulls().unique(), R["__k"].drop_nulls().unique()
    if lk.dtype != rk.dtype:
        try:
            rk = rk.cast(lk.dtype)
            R = R.with_columns(pl.col("__k").cast(lk.dtype))
        except Exception:
            print(f"FAIL  key types differ ({lk.dtype} vs {rk.dtype}) and do not cast")
            return 2
    inter = lk.is_in(rk.implode()).sum() if hasattr(rk, "implode") else lk.is_in(rk).sum()
    share_l = inter / max(1, lk.len())
    share_r = inter / max(1, rk.len())
    print(f"overlap {inter:,} shared keys: {share_l:.4f} of LEFT, {share_r:.4f} of RIGHT")
    if min(share_l, share_r) < a.min_overlap:
        print(f"FAIL  overlap {min(share_l, share_r):.4f} below --min-overlap {a.min_overlap}: "
              "wrong file, wrong key or wrong index space")
        return 2

    # 3. positional pairing
    n = min(L.height, R.height)
    if n:
        same = (L["__k"].head(n) == R["__k"].head(n).cast(L["__k"].dtype, strict=False)).fill_null(False).sum()
        print(f"position row i of LEFT has the key of row i of RIGHT for {same / n:.4%} of {n:,} rows")
        if same < n or L.height != R.height:
            print("warn  a join by row position would mis-pair rows here; join on the key")

    # 4. index space hint
    if R.height < L.height and R["__k"].dtype.is_integer():
        rr = R["__k"].drop_nulls()
        if rr.len() == R.height and rr.min() == 0 and rr.max() == R.height - 1 and rr.n_unique() == R.height:
            print("warn  RIGHT's key is exactly 0..n-1 while LEFT has more rows: "
                  "the index was probably assigned after a filter")

    # 5. exact invariants on the key join
    J = L.join(R, on="__k", how="inner", suffix="__r")
    for c in comps:
        x, y = J[c], J[f"{c}__r"]
        if x.dtype.is_numeric() and y.dtype.is_numeric():
            bad = ((x - y).abs() > a.tolerance).fill_null(True).sum()
        else:
            bad = (~x.cast(pl.Utf8).eq_missing(y.cast(pl.Utf8))).sum()
        print(f"invariant {c}: {bad:,} of {J.height:,} key-joined rows differ")
        if bad:
            print(f"FAIL  {c} disagrees after the key join: the two keys are not the same index space")
            status = max(status, 1)
        if n and c in L.columns and c in R.columns:
            px, py = L[c].head(n), R[c].head(n)
            if px.dtype.is_numeric() and py.dtype.is_numeric():
                pbad = ((px - py).abs() > a.tolerance).fill_null(True).sum()
            else:
                pbad = (~px.cast(pl.Utf8).eq_missing(py.cast(pl.Utf8))).sum()
            print(f"          by position instead: {pbad:,} of {n:,} rows would differ")

    # 6. order independence
    Ls = L.sample(fraction=1.0, shuffle=True, seed=a.seed)
    Rs = R.sample(fraction=1.0, shuffle=True, seed=a.seed + 1)
    Js = Ls.join(Rs, on="__k", how="inner", suffix="__r")
    if Js.height != J.height or frame_hash(Js, "__k") != frame_hash(J, "__k"):
        print("FAIL  the key join changed when the inputs were shuffled")
        status = max(status, 1)
    else:
        print(f"order key join identical after shuffling both sides ({J.height:,} rows)")

    print("PASS" if status == 0 else f"FAILED (exit {status})")
    return status


if __name__ == "__main__":
    sys.exit(main())

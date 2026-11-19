#!/usr/bin/env python3
"""Census of a data corpus: fingerprint files by content, deduplicate, count rows, and say what is covered.

Names and metadata keys do not identify data. In one corpus, byte size showed that dozens
of directories shared a few tables, while deduplicating on a (run, region) name key deleted
real datasets. A derived file (a re-processing of a raw file) can carry the parent's row
count to the digit, so a "richest record wins" rule promotes the derivative over the raw
data. This script groups files by size and SHA-256, keeps one file per group, asserts that
nothing was lost in the bookkeeping, and reports the coverage of every total.

Steps:
  1. enumerate files under ROOT matching --pattern (repeatable), plus any --manifest entries
  2. fingerprint each local file: size, then SHA-256 for files whose size is shared
     (a unique size cannot have a byte-identical twin)
  3. group identical files; keep the path listed in --manifest (else the lexically first);
     the others are withheld
  4. conservation: enumerated_local == kept + withheld, asserted (exit 1 if broken)
  5. optional --count-rows: parquet from the footer (pyarrow if installed), csv/tsv and their
     .gz by counting lines minus the header; files that cannot be counted are listed
  6. coverage block: how many entries were enumerated, found locally, counted; every total
     says which population it covers, and a total over part of the corpus is labeled a floor

Outputs: a TSV with one row per file (path, size, sha256, group, kept, rows) via --out, and a
JSON coverage block via --json. Both are generated: copy numbers from them, never by hand.

Examples:
  python3 fingerprint_census.py data/ --pattern '*.parquet' --pattern '*.csv.gz' --count-rows \\
      --out census.tsv --json census.json
  python3 fingerprint_census.py data/ --manifest sources.csv --manifest-col path --count-rows

Standard library only; pyarrow is used for parquet row counts when installed.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def count_rows(path: Path):
    name = path.name.lower()
    try:
        if name.endswith(".parquet"):
            try:
                import pyarrow.parquet as pq
            except ImportError:
                return None, "pyarrow not installed"
            return pq.ParquetFile(path).metadata.num_rows, ""
        if name.endswith((".csv", ".tsv", ".txt")):
            with open(path, "rb") as f:
                return max(0, sum(1 for _ in f) - 1), ""
        if name.endswith((".csv.gz", ".tsv.gz", ".txt.gz")):
            with gzip.open(path, "rb") as f:
                return max(0, sum(1 for _ in f) - 1), ""
    except Exception as e:  # unreadable file: reported, never counted as zero
        return None, f"unreadable: {type(e).__name__}"
    return None, "no row counter for this type"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fingerprint, deduplicate and count a data corpus.",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--pattern", action="append", default=[], help="glob under ROOT, recursive (default '*')")
    p.add_argument("--manifest", type=Path, default=None, help="CSV listing every entry the corpus should have")
    p.add_argument("--manifest-col", default="path", help="manifest column holding the path relative to ROOT")
    p.add_argument("--count-rows", action="store_true", help="count rows of each kept file")
    p.add_argument("--out", type=Path, default=None, help="per-file TSV")
    p.add_argument("--json", type=Path, default=None, help="coverage block as JSON")
    a = p.parse_args(argv)

    pats = a.pattern or ["*"]
    files = sorted({f for pat in pats for f in a.root.rglob(pat) if f.is_file()})
    manifest_entries, missing = [], []
    if a.manifest:
        with open(a.manifest, newline="") as fh:
            manifest_entries = [row[a.manifest_col] for row in csv.DictReader(fh)]
        for e in manifest_entries:
            if not (a.root / e).is_file():
                missing.append(e)

    by_size = defaultdict(list)
    for f in files:
        by_size[f.stat().st_size].append(f)
    recs = []
    for size, group in by_size.items():
        for f in group:
            digest = sha256(f) if len(group) > 1 else f"unique-size:{size}"
            recs.append({"path": str(f.relative_to(a.root)), "size": size, "sha256": digest})
    groups = defaultdict(list)
    for r in recs:
        groups[(r["size"], r["sha256"])].append(r)
    kept = withheld = 0
    for gid, (_, members) in enumerate(sorted(groups.items(), key=lambda kv: sorted(m["path"] for m in kv[1])[0])):
        listed = set(manifest_entries)
        members.sort(key=lambda r: (r["path"] not in listed, r["path"]))
        for i, r in enumerate(members):
            r["group"] = gid
            r["kept"] = i == 0
            r["duplicate_of"] = "" if i == 0 else members[0]["path"]
            kept += i == 0
            withheld += i != 0

    n_local = len(recs)
    ok = n_local - kept == withheld
    print(f"[census] enumerated {n_local} local files; kept {kept}; withheld {withheld} byte-identical duplicates")
    print(f"[census] conservation {n_local} - {kept} == {withheld}: {'OK' if ok else 'BROKEN'}")
    for r in recs:
        if not r["kept"]:
            print(f"         duplicate {r['path']}  ==  {r['duplicate_of']}")

    counted, uncounted, total_rows = 0, [], 0
    if a.count_rows:
        for r in recs:
            r["rows"], r["note"] = (None, "duplicate, not counted") if not r["kept"] else count_rows(a.root / r["path"])
            if r["kept"]:
                if r["rows"] is None:
                    uncounted.append((r["path"], r["note"]))
                else:
                    counted += 1
                    total_rows += r["rows"]

    cov = {
        "manifest_entries": len(manifest_entries) if a.manifest else None,
        "manifest_entries_missing_locally": missing,
        "files_enumerated_local": n_local,
        "files_kept": kept,
        "files_withheld_duplicates": withheld,
        "conservation_ok": ok,
    }
    if a.count_rows:
        population = len(manifest_entries) if a.manifest else kept
        cov.update({
            "files_counted": counted,
            "files_uncounted": [{"path": pth, "why": why} for pth, why in uncounted],
            "rows_total_over_counted": total_rows,
            "rows_per_counted_file": round(total_rows / counted, 1) if counted else None,
            "total_is_floor": counted < population,
            "coverage": f"{counted} of {population} " + ("manifest entries" if a.manifest else "unique files")
                        + f" ({withheld} duplicate withheld, {len(missing)} missing locally, "
                          f"{len(uncounted)} not countable)",
        })
        label = "a FLOOR" if cov["total_is_floor"] else "complete"
        print(f"[census] rows {total_rows:,} over {cov['coverage']} ({label})")
        if counted:
            print(f"[census] rows per counted file {cov['rows_per_counted_file']:,}; do not divide the total "
                  f"by a count from another population")
        for pth, why in uncounted:
            print(f"         not counted: {pth} ({why})")
    if missing:
        print(f"[census] {len(missing)} manifest entries are not present locally: {missing[:10]}"
              + (" ..." if len(missing) > 10 else ""))

    if a.out:
        cols = ["path", "size", "sha256", "group", "kept", "duplicate_of"] + (["rows", "note"] if a.count_rows else [])
        with open(a.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t", extrasaction="ignore")
            w.writeheader()
            w.writerows(recs)
    if a.json:
        a.json.write_text(json.dumps(cov, indent=2) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

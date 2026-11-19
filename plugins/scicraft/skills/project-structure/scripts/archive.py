#!/usr/bin/env python3
"""Move superseded outputs or large data into an archive folder, with a manifest and a reason.

  archive.py PATH [PATH ...] --to DEST --reason "why" [--base DIR] [--symlink] [--apply]

Each PATH moves to DEST/<its path relative to --base> (default base: the current folder), so the
archive keeps the original layout. One row per item is appended to DEST/MANIFEST.tsv:
original path, archived path, bytes, files, date, reason, and whether a link was left behind.

Two uses:
  superseded results   --to results/archived/2026-11-18_split-fix --reason "rerun with fixed split; see RUN_MAP"
  quota relief         --to /mnt/archive/proj_2026-11-18 --symlink --reason "disk at 99.7 %"
                       (--symlink leaves a link at the original path, so existing references keep working)

Without --apply nothing moves: the plan is printed (a dry run). Across file systems the item is
copied, the copy is checked (same byte total and file count), and only then is the original
removed. An item that fails the check stays where it was and the run exits 1.

Standard library only; Python 3.9 or later. Never deletes anything that has not been copied and checked.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import sys
from pathlib import Path

HEADER = "original\tarchived\tbytes\tfiles\tmoved_on\treason\tlink_left\n"


def measure(p: Path):
    if p.is_symlink() or p.is_file():
        return (0 if p.is_symlink() else p.stat().st_size), 1
    total = files = 0
    for dirpath, _, filenames in os.walk(p, followlinks=False):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
            files += 1
    return total, files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog=__doc__.split("\n\n", 1)[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--to", required=True, type=Path, help="archive folder (created if missing)")
    ap.add_argument("--reason", required=True, help="why these items are archived; written to every manifest row")
    ap.add_argument("--base", type=Path, default=Path("."), help="paths are stored relative to this folder")
    ap.add_argument("--symlink", action="store_true", help="leave a symbolic link at each original path")
    ap.add_argument("--apply", action="store_true", help="really move; without it, print the plan only")
    a = ap.parse_args()

    if not a.reason.strip():
        print("a reason is required", file=sys.stderr)
        return 2
    base = a.base.expanduser().resolve()
    dest_root = a.to.expanduser().resolve()
    today = dt.date.today().isoformat()
    failures = 0
    rows = []
    for p in a.paths:
        src = p.expanduser().absolute()
        if not (src.exists() or src.is_symlink()):
            print(f"MISSING  {p}")
            failures += 1
            continue
        try:
            src = src.parent.resolve() / src.name  # resolve folders above, keep a link itself as the item
            rel = src.relative_to(base)
        except ValueError:
            print(f"OUTSIDE  {p} is not under --base {base}")
            failures += 1
            continue
        dst = dest_root / rel
        if dst.exists() or dst.is_symlink():
            print(f"EXISTS   {dst}; refusing to overwrite")
            failures += 1
            continue
        nbytes, nfiles = measure(src)
        print(f"{'MOVE' if a.apply else 'PLAN'}     {rel} -> {dst} ({nbytes} bytes, {nfiles} files)"
              f"{' + link left' if a.symlink else ''}")
        if not a.apply:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.rename(src, dst)  # same file system: atomic
        except OSError:
            if src.is_dir() and not src.is_symlink():
                shutil.copytree(src, dst, symlinks=True)
            else:
                shutil.copy2(src, dst, follow_symlinks=False)
            if measure(dst) != (nbytes, nfiles):
                print(f"FAIL     copy of {rel} does not match (bytes or file count); original kept, copy left at {dst}")
                failures += 1
                continue
            shutil.rmtree(src) if src.is_dir() and not src.is_symlink() else src.unlink()
        if measure(dst) != (nbytes, nfiles):
            print(f"FAIL     {dst} does not match what was measured before the move")
            failures += 1
        if a.symlink:
            os.symlink(dst, src)
        rows.append(f"{rel}\t{dst}\t{nbytes}\t{nfiles}\t{today}\t{a.reason}\t{'yes' if a.symlink else 'no'}\n")

    if rows:
        dest_root.mkdir(parents=True, exist_ok=True)
        man = dest_root / "MANIFEST.tsv"
        new = not man.exists()
        with man.open("a", encoding="utf-8") as fh:
            if new:
                fh.write(HEADER)
            fh.writelines(rows)
        print(f"manifest: {len(rows)} rows appended to {man}")
    if not a.apply:
        print("dry run: nothing moved; add --apply after the owner agrees")
    print(f"archive: {len(rows)} moved, {failures} problems")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

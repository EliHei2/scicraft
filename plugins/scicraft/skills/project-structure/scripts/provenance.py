#!/usr/bin/env python3
"""Copy an input into the project with its provenance row, and check every recorded copy for drift.

  provenance.py copy SRC DST [--prov PROVENANCE.md] [--note TEXT]
  provenance.py check [--prov PROVENANCE.md]

copy   copies the file SRC to DST (inside the project, usually data/<unit>/) and appends a row to
       the "Copied inputs" table of PROVENANCE.md: file, source, source mtime, copied on, md5.
       DST is refused if it exists; refresh a copy on purpose by deleting it first.
check  re-reads every row of that table. For each copy it reports
         ok              the local file and the source both still match the recorded md5
         LOCAL CHANGED   the copy in the project no longer matches its row
         SOURCE CHANGED  the source moved on since the copy (refresh deliberately, add a new row)
         SOURCE GONE     the source path no longer exists here (fine on another machine)
         MISSING         the copy itself is gone
       and exits 1 on LOCAL CHANGED or MISSING, so a drift is visible and never silent.

Paths in the table are written relative to the folder that holds PROVENANCE.md when they lie inside it.
Standard library only; Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import shutil
import sys
from pathlib import Path

ANCHOR = "| File | Source | Source mtime | Copied on | md5 |\n|---|---|---|---|---|\n"


def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rows(text: str):
    if ANCHOR not in text:
        return []
    out = []
    for line in text.split(ANCHOR, 1)[1].splitlines():
        if not line.startswith("|"):
            break
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5:
            out.append(cells[:5])
    return out


def cmd_copy(a) -> int:
    prov = a.prov.resolve()
    root = prov.parent
    src, dst = a.src.expanduser().resolve(), a.dst.expanduser().absolute()
    if not src.is_file():
        print(f"source is not a file: {src}", file=sys.stderr)
        return 1
    if dst.exists():
        print(f"refusing: {dst} exists; delete it first to refresh the copy on purpose", file=sys.stderr)
        return 1
    if not prov.exists():
        print(f"no {prov}; create it with scaffold.py first", file=sys.stderr)
        return 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    digest = md5(dst)
    if digest != md5(src):
        print("copy does not match its source", file=sys.stderr)
        return 1
    try:
        shown = dst.resolve().relative_to(root)
    except ValueError:
        shown = dst
    mtime = dt.datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    note = f" ({a.note})" if a.note else ""
    row = f"| `{shown}` | `{src}`{note} | {mtime} | {dt.date.today().isoformat()} | {digest} |\n"
    text = prov.read_text(encoding="utf-8")
    if ANCHOR in text:
        head, tail = text.split(ANCHOR, 1)
        body = tail.splitlines(keepends=True)
        n = 0
        while n < len(body) and body[n].startswith("|"):
            n += 1
        text = head + ANCHOR + "".join(body[:n]) + row + "".join(body[n:])
    else:
        text += "\n## Copied inputs\n\n" + ANCHOR + row
    prov.write_text(text, encoding="utf-8")
    print(f"copied {src} -> {shown} (md5 {digest}); row added to {prov.name}")
    return 0


def cmd_check(a) -> int:
    prov = a.prov.resolve()
    root = prov.parent
    found = rows(prov.read_text(encoding="utf-8"))
    bad = 0
    for f, source, _mtime, _date, digest in found:
        local = (root / f) if not Path(f).is_absolute() else Path(f)
        src = Path(source.split(" (")[0].strip("`"))
        if not local.exists():
            state, bad = "MISSING", bad + 1
        elif md5(local) != digest:
            state, bad = "LOCAL CHANGED", bad + 1
        elif not src.exists():
            state = "SOURCE GONE"
        elif md5(src) != digest:
            state = "SOURCE CHANGED"
        else:
            state = "ok"
        print(f"{state:<15} {f}")
    print(f"provenance check: {len(found)} copies, {bad} problems")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog=__doc__.split("\n\n", 1)[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("copy", help="copy a file in and record it")
    c.add_argument("src", type=Path)
    c.add_argument("dst", type=Path)
    c.add_argument("--note", help="short note after the source (e.g. 'summary of runs/ table 2')")
    k = sub.add_parser("check", help="compare every recorded copy with its md5 and source")
    for p in (c, k):
        p.add_argument("--prov", type=Path, default=Path("PROVENANCE.md"))
    a = ap.parse_args()
    return cmd_copy(a) if a.cmd == "copy" else cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())

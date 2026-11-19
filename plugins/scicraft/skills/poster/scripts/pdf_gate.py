#!/usr/bin/env python3
"""Printer gate for the poster file: page size, page count, every font embedded, file size,
and no forbidden string in the text layer (hidden text under a figure's paint counts too).

usage:
    python3 pdf_gate.py poster.pdf [--size 841x1189] [--tol 1] [--max-mb 50]
                        [--forbid "old name,working title"] [--forbid-file retired.txt]

  --size        expected page size in mm, W x H (default A0 portrait, 841 x 1189)
  --tol         allowed difference in mm (default 1)
  --max-mb      largest file the printer or upload accepts, in MB (default 50; ask the print shop)
  --forbid      comma-separated strings that must not occur in the text layer (case-insensitive):
                retired method names, superseded numbers, author names that must not appear
  --forbid-file the same, one string per line

What it reads: `pdfinfo` (pages, page size), `pdffonts` (the emb column), `pdftotext` (the text
layer of every page, including the text inside placed figure PDFs). Prints every check with
ok or FAIL and exits 1 on any FAIL. Needs Python 3.9+ and poppler on the PATH.
"""
import argparse
import os
import re
import subprocess
import sys

MM_PER_PT = 25.4 / 72


def run(*cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"{cmd[0]} failed: {p.stderr.strip()[:200]}")
    return p.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--size", default="841x1189")
    ap.add_argument("--tol", type=float, default=1.0)
    ap.add_argument("--max-mb", type=float, default=50.0)
    ap.add_argument("--forbid", default="")
    ap.add_argument("--forbid-file")
    a = ap.parse_args()

    fails = 0

    def report(ok, msg):
        nonlocal fails
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'}  {msg}")

    info = run("pdfinfo", a.pdf)
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
    report(pages == 1, f"{pages} page(s); a poster file has 1")
    w, h = (float(v) * MM_PER_PT for v in re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info).groups())
    ew, eh = map(float, a.size.lower().split("x"))
    report(abs(w - ew) <= a.tol and abs(h - eh) <= a.tol,
           f"page {w:.1f} x {h:.1f} mm, expected {ew:g} x {eh:g} mm (tolerance {a.tol:g} mm)")

    fonts = run("pdffonts", a.pdf).splitlines()[2:]
    unemb = []
    for ln in fonts:
        cols = ln.split()
        # columns: name type [encoding words...] emb sub uni object ID; emb is the 5th field from the end
        if len(cols) >= 7 and cols[-5] != "yes":
            unemb.append(cols[0])
    report(not unemb, f"{len(fonts)} fonts, not embedded: {', '.join(sorted(set(unemb))) or 'none'}")

    mb = os.path.getsize(a.pdf) / 1e6
    report(mb <= a.max_mb, f"{mb:.1f} MB (limit {a.max_mb:g} MB)")

    terms = [t.strip() for t in a.forbid.split(",") if t.strip()]
    if a.forbid_file:
        terms += [t.strip() for t in open(a.forbid_file, encoding="utf-8") if t.strip() and not t.startswith("#")]
    if terms:
        text = run("pdftotext", a.pdf, "-").lower()
        hits = [t for t in terms if t.lower() in text]
        report(not hits, f"text layer holds {', '.join(hits) if hits else 'none'} of {len(terms)} forbidden strings")
    else:
        print("skip  no --forbid strings given: the text layer was not scanned")
    print(f"{fails} failed  [{a.pdf}]")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

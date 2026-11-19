#!/usr/bin/env python3
"""Check the two built copies of a revised paper: the marked copy and the clean copy.

    python3 rev_pdf_check.py revised.pdf revised_clean.pdf
    python3 rev_pdf_check.py revised.pdf revised_clean.pdf --color 70,130,180 --allow 0,114,178

Checks:
  1. Both copies have the same pages and the same words at the same places (within --tol pt), so the clean copy is
     the marked copy without color and nothing moved when the switch was turned.
  2. The clean copy holds no text in the revision color.
  3. The marked copy holds text in exactly one revision color: it lists the pages with marked text and any other
     non-black text color, so a forgotten round color (orange, magenta) shows up. Colors that belong to the
     paper (rank tints, a method color) are passed with --allow.

Needs PyMuPDF (pip install pymupdf). Exit code 1 when the copies differ, the clean copy has marked text, or the
marked copy has a color outside --color and --allow.
"""
from __future__ import annotations

import argparse
import sys

try:
    import fitz
except ImportError:  # pragma: no cover
    sys.exit("rev_pdf_check.py needs PyMuPDF: pip install pymupdf")


def rgb(s: str) -> int:
    r, g, b = (int(x) for x in s.split(","))
    return (r << 16) | (g << 8) | b


def spans(page):
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                if sp["text"].strip():
                    yield sp


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("marked", help="PDF with the revision color on")
    ap.add_argument("clean", help="PDF built with the switch off")
    ap.add_argument("--color", default="70,130,180", help="revision color as R,G,B (default 70,130,180)")
    ap.add_argument("--allow", nargs="*", default=[], help="other text colors that belong to the paper, as R,G,B")
    ap.add_argument("--tol", type=float, default=0.5, help="largest allowed word shift in pt (default 0.5)")
    a = ap.parse_args()
    rev, allow = rgb(a.color), {rgb(c) for c in a.allow}
    M, C = fitz.open(a.marked), fitz.open(a.clean)
    bad = 0
    if len(M) != len(C):
        print(f"FAIL page count differs: marked {len(M)}, clean {len(C)}")
        bad += 1
    for pno in range(min(len(M), len(C))):
        wm, wc = M[pno].get_text("words"), C[pno].get_text("words")
        if [w[4] for w in wm] != [w[4] for w in wc]:
            print(f"FAIL page {pno + 1}: the words differ between the copies")
            bad += 1
        elif any(abs(x[0] - y[0]) > a.tol or abs(x[1] - y[1]) > a.tol for x, y in zip(wm, wc)):
            print(f"FAIL page {pno + 1}: words moved when the color was switched off")
            bad += 1
    marked_pages, other = {}, {}
    for pno, page in enumerate(M, 1):
        for sp in spans(page):
            if sp["color"] == rev:
                marked_pages[pno] = marked_pages.get(pno, 0) + len(sp["text"])
            elif sp["color"] != 0 and sp["color"] not in allow:
                other.setdefault(sp["color"], []).append((pno, sp["text"][:40]))
    for pno, page in enumerate(C, 1):
        n = sum(len(sp["text"]) for sp in spans(page) if sp["color"] == rev)
        if n:
            print(f"FAIL clean copy, page {pno}: {n} characters in the revision color")
            bad += 1
    print("marked text (characters) by page:", ", ".join(f"p{p} {n}" for p, n in sorted(marked_pages.items())) or "none")
    for col, where in other.items():
        r, g, b = col >> 16, (col >> 8) & 255, col & 255
        print(f"FAIL marked copy has text in {r},{g},{b} (not the revision color): first at page {where[0][0]}, {where[0][1]!r}; {len(where)} spans")
        bad += 1
    print("copies agree, one revision color" if not bad else f"{bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

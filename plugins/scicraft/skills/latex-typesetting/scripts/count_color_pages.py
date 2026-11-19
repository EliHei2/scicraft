#!/usr/bin/env python3
"""Count color and black-and-white pages of a PDF, as a print shop would.

A page is a color page when any of its pixels carries visible chroma. Each page is
rendered in RGB; a pixel is chromatic when max(R,G,B) - min(R,G,B) exceeds --chroma
(default 28 of 255), and a page counts as color when more than --min-pixels such
pixels remain (default 12; anti-aliased black text and gray figures stay neutral).

  count_color_pages.py main_print.pdf            60 dpi
  count_color_pages.py main_print.pdf --dpi 90

Cross-check the list: every color page should carry a figure or a table that is
meant to stay in color, and the front matter should be black and white.

Needs Python 3.9+, PyMuPDF (pip install pymupdf) and numpy.
"""
import argparse
import sys

try:
    import fitz  # PyMuPDF
    import numpy as np
except ImportError as e:
    sys.exit(f"count_color_pages.py needs PyMuPDF and numpy ({e})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--dpi", type=int, default=60)
    ap.add_argument("--chroma", type=int, default=28, help="max-min channel spread that counts as color (0-255)")
    ap.add_argument("--min-pixels", type=int, default=12, help="chromatic pixels above which a page is color")
    a = ap.parse_args()

    doc = fitz.open(a.pdf)
    color, mono = [], []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=a.dpi, colorspace=fitz.csRGB, alpha=False)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).astype(np.int16)
        n = int(((arr.max(axis=2) - arr.min(axis=2)) > a.chroma).sum())
        label = page.get_label() or str(i + 1)
        (color if n > a.min_pixels else mono).append((i + 1, label, n))
    print(f"{a.pdf}: {len(doc)} pages, {len(color)} color, {len(mono)} black-and-white")
    print("color pages (PDF page / printed label):")
    print(", ".join(f"{p}/{l}" for p, l, _ in color) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())

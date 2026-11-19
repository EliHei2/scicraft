#!/usr/bin/env python3
"""Make a PDF fit a size limit without touching its text, or make a light copy for reading.

    python3 shrink_pdf.py compress paper.pdf paper_upload.pdf --dpi 200 --quality 80
    python3 shrink_pdf.py light paper.pdf paper_light.pdf --heavy-mb 3 --dpi 170

compress  resamples embedded raster images to --dpi (images already below dpi + 20 are left alone) and recompresses;
          text and vector graphics are untouched. Values that worked: 200 dpi at quality 80 brought a paper with
          large raster figures under a 50 MB upload limit; 120 dpi at quality 76, or 100 at 72, for a copy sent
          by chat.
light     stores only the pages heavier than --heavy-mb as page images and copies every other page unchanged, for
          vector-heavy pages (dense scatter plots) that compress does not shrink.
Keep the full-quality master; these are copies. Check the result with pdffonts and by looking at the heavy pages.

Needs PyMuPDF (pip install pymupdf); compress needs PyMuPDF 1.24 or later (Document.rewrite_images).
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    import fitz
except ImportError:  # pragma: no cover
    sys.exit("shrink_pdf.py needs PyMuPDF: pip install pymupdf")


def compress(src: str, dst: str, dpi: int, q: int) -> None:
    doc = fitz.open(src)
    doc.rewrite_images(dpi_threshold=dpi + 20, dpi_target=dpi, quality=q, lossy=True, lossless=True,
                       bitonal=False, color=True, gray=True)
    doc.save(dst, garbage=4, deflate=True, use_objstms=1)


def light(src: str, dst: str, heavy_mb: float, dpi: int, q: int) -> list:
    s, out, heavy = fitz.open(src), fitz.open(), []
    for i, page in enumerate(s):
        one = fitz.open()
        one.insert_pdf(s, from_page=i, to_page=i)
        if len(one.tobytes(garbage=4, deflate=True)) > heavy_mb * 1e6:
            heavy.append(i + 1)
            pix = page.get_pixmap(dpi=dpi)
            new = out.new_page(width=page.rect.width, height=page.rect.height)
            new.insert_image(new.rect, stream=pix.tobytes("jpeg", jpg_quality=q))
        else:
            out.insert_pdf(s, from_page=i, to_page=i)
    out.save(dst, garbage=4, deflate=True)
    return heavy


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("mode", choices=("compress", "light"))
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--dpi", type=int, default=None, help="target dpi (compress 200, light 170)")
    ap.add_argument("--quality", type=int, default=None, help="JPEG quality (compress 80, light 84)")
    ap.add_argument("--heavy-mb", type=float, default=3.0, help="light: pages above this many MB become images (default 3)")
    ap.add_argument("--limit-mb", type=float, help="report whether the result is under this size")
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        ap.error("write to a new file; keep the master")
    if a.mode == "compress":
        compress(a.src, a.dst, a.dpi or 200, a.quality or 80)
        extra = ""
    else:
        heavy = light(a.src, a.dst, a.heavy_mb, a.dpi or 170, a.quality or 84)
        extra = f", pages stored as images: {heavy or 'none'}"
    mb_in, mb_out = os.path.getsize(a.src) / 1e6, os.path.getsize(a.dst) / 1e6
    print(f"{os.path.basename(a.dst)}: {mb_in:.1f} MB -> {mb_out:.1f} MB, {len(fitz.open(a.dst))} pages{extra}")
    if a.limit_mb is not None:
        print("under the limit" if mb_out <= a.limit_mb else f"OVER the {a.limit_mb} MB limit")
        return 0 if mb_out <= a.limit_mb else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

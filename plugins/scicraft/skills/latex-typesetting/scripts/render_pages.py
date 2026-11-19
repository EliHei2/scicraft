#!/usr/bin/env python3
"""Render PDF pages to PNG so a person (or an agent) can look at them.

  render_pages.py main.pdf out/ 3 7 xii            pages by printed label (or number), 150 dpi
  render_pages.py main.pdf out/ 5-9 --dpi 300      a range at higher resolution
  render_pages.py main.pdf out/ 4 --clip 0.0 0.0 0.5 0.3    zoom: fractions x0 y0 x1 y1 of the page
  render_pages.py main.pdf out/ --sheet            contact sheet(s) of all pages, 45 dpi
  render_pages.py main.pdf out/ --sheet --first 30 --last 50 --cols 6
  render_pages.py main.pdf --figs                  Figure / Table / Algorithm number -> page

A log can say 0 errors while a running head wraps to two lines, a box stops short of
the margin, a unit swallows the following space, or a figure floats past the
conclusions. Look at every page that a preamble or layout change can touch.

Needs Python 3.9+ and PyMuPDF (pip install pymupdf). Without PyMuPDF it falls back to
pdftoppm (poppler) for plain page renders by physical page number; --sheet, --clip,
--figs and printed labels need PyMuPDF.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def parse_pages(specs, doc):
    labels = {}
    if doc is not None:
        for i in range(doc.page_count):
            lab = doc[i].get_label()
            if lab:
                labels.setdefault(lab, i)
    n = doc.page_count if doc is not None else None
    out = []
    for s in specs:
        if s in labels:
            out.append(labels[s])
        elif re.fullmatch(r"\d+-\d+", s):
            a, b = map(int, s.split("-"))
            out += list(range(a - 1, b))
        elif s.isdigit():
            out.append(int(s) - 1)
        else:
            print(f"no page labeled {s}")
    return [i for i in out if n is None or 0 <= i < n]


def sheets(doc, out, first, last, cols, rows, dpi):
    pages = list(range(first - 1, min(last, doc.page_count)))
    per = cols * rows
    made = []
    for k in range(0, len(pages), per):
        chunk = pages[k:k + per]
        w, h = doc[chunk[0]].rect.width, doc[chunk[0]].rect.height
        gap = 8
        rows_here = -(-len(chunk) // cols)
        cols_here = min(cols, len(chunk))
        sheet = fitz.open()
        page = sheet.new_page(width=cols_here * (w + gap) + gap, height=rows_here * (h + gap + 14) + gap)
        for j, i in enumerate(chunk):
            r, c = divmod(j, cols)
            x0, y0 = gap + c * (w + gap), gap + r * (h + gap + 14)
            page.draw_rect(fitz.Rect(x0, y0, x0 + w, y0 + h), color=(0.6, 0.6, 0.6), width=0.5)
            page.show_pdf_page(fitz.Rect(x0, y0, x0 + w, y0 + h), doc, i)
            lab = doc[i].get_label() or str(i + 1)
            page.insert_text((x0, y0 + h + 11), f"{i + 1} ({lab})", fontsize=10)
        path = os.path.join(out, f"sheet_{chunk[0] + 1:03d}-{chunk[-1] + 1:03d}.png")
        page.get_pixmap(dpi=dpi).save(path)
        made.append(path)
    return made


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("outdir", nargs="?", help="folder for the PNGs")
    ap.add_argument("pages", nargs="*", help="printed labels, numbers, or ranges like 5-9")
    ap.add_argument("--dpi", type=int, default=None, help="150 for pages, 45 for sheets by default")
    ap.add_argument("--clip", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"),
                    help="render only this part of the page, as fractions of width and height")
    ap.add_argument("--sheet", action="store_true", help="contact sheets instead of single pages")
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=10**6)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--figs", action="store_true", help="print the page of every Figure / Table / Algorithm caption")
    args = ap.parse_args()

    if fitz is None and (args.sheet or args.clip or args.figs):
        sys.exit("--sheet, --clip and --figs need PyMuPDF (pip install pymupdf)")
    doc = fitz.open(args.pdf) if fitz else None

    if args.figs:
        seen = set()
        for i in range(doc.page_count):
            for m in re.finditer(r"(Figure|Table|Algorithm|Box) ([A-Z]?\d+(?:\.\d+)?):", doc[i].get_text()):
                key = (m.group(1), m.group(2))
                if key not in seen:
                    seen.add(key)
                    print(f"{m.group(1)} {m.group(2)}: page {i + 1} (label {doc[i].get_label() or i + 1})")
        return 0

    if not args.outdir:
        sys.exit("give an output folder")
    os.makedirs(args.outdir, exist_ok=True)

    if args.sheet:
        for p in sheets(doc, args.outdir, args.first, args.last, args.cols, args.rows, args.dpi or 45):
            print(p)
        return 0

    dpi = args.dpi or 150
    if doc is None:
        if not shutil.which("pdftoppm"):
            sys.exit("neither PyMuPDF nor pdftoppm is available")
        for i in parse_pages(args.pages, None):
            base = os.path.join(args.outdir, f"pg_{i + 1:03d}")
            subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(i + 1), "-l", str(i + 1), "-png", "-singlefile",
                            args.pdf, base], check=True)
            print(base + ".png")
        return 0

    for i in parse_pages(args.pages, doc):
        page = doc[i]
        clip = None
        if args.clip:
            r = page.rect
            x0, y0, x1, y1 = args.clip
            clip = fitz.Rect(r.width * x0, r.height * y0, r.width * x1, r.height * y1)
        lab = (page.get_label() or str(i + 1)).replace("/", "_")
        path = os.path.join(args.outdir, f"pg_{i + 1:03d}_{lab}{'_clip' if clip else ''}.png")
        page.get_pixmap(dpi=dpi, clip=clip).save(path)
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

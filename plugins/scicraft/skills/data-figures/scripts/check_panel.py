#!/usr/bin/env python3
"""Check rendered panel or figure PDFs against the house rules that a script can see.

For each PDF it reports:
  size      page size in mm; files given with --figure must also match --figure-width/--figure-height
  fonts     every font embedded, none Type 3 (Type 3 means pdf.fonttype 42 was not set), no DejaVu fallback
  floor     no text below --floor pt (default 5)
  tiers     distinct text sizes, excluding the panel-letter size; more than --max-tiers (default 4) fails, 4 warns
  ink       text that is not black: gray text fails; other colors are listed (allowed only on a hero label or a
            white label on a dark cell)
  clipped   text that runs off the page
  overlap   horizontal text runs whose boxes overlap each other (rotated labels: look at the PNG)
  banned    any word from --ban FILE (internal IDs, run names, hardware, tool names: one per line)

Usage:
    python3 check_panel.py panels/*.pdf --figure figure_2.pdf --figure-width 183 --ban banned_words.txt
    python3 check_panel.py --figure figure_2.pdf --figure-width 183 --figure-height 120 --letter-pt 8

Panels have their own sizes, so the width and height checks apply to --figure files only.

Exit 1 when any check fails. Needs PyMuPDF. Overlap is measured on text boxes only: a label lying on a data mark
is not seen, so look at the PNG at 2 to 3x zoom as well.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz
except ImportError:  # pragma: no cover
    sys.exit("check_panel.py needs PyMuPDF: pip install pymupdf")

MM_PT = 72.0 / 25.4


def spans(page):
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            for s in line["spans"]:
                if s["text"].strip():
                    s["flat"] = abs(line["dir"][1]) < 1e-3     # horizontal text; rotated runs skip the box test
                    yield s


def is_gray(rgb: int) -> bool:
    r, g, b = (rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255
    return max(r, g, b) - min(r, g, b) < 12 and 40 < r < 235


def check(pdf: Path, a, is_figure: bool):
    fails, warns = [], []
    doc = fitz.open(pdf)
    page = doc[0]
    w, h = page.rect.width / MM_PT, page.rect.height / MM_PT
    info = [f"{w:.1f} x {h:.1f} mm"]
    if is_figure and a.figure_width and abs(w - a.figure_width) > 0.3:
        fails.append(f"width {w:.1f} mm, expected {a.figure_width} mm")
    if is_figure and a.figure_height and abs(h - a.figure_height) > 0.3:
        fails.append(f"height {h:.1f} mm, expected {a.figure_height} mm")
    for xref, ext, ftype, base, *_ in page.get_fonts(full=True):
        if ftype == "Type3":
            fails.append(f"Type 3 font {base}: set pdf.fonttype 42 in the style module")
        if ext in ("", "n/a") and ftype != "Type3":
            fails.append(f"font {base} not embedded")
        if "DejaVu" in base and not a.allow_dejavu:
            fails.append(f"font {base}: matplotlib fell back to DejaVu; register the house font")
    sizes, boxes = {}, []
    banned = []
    if a.ban:
        banned = [t.strip() for t in Path(a.ban).read_text().splitlines() if t.strip() and not t.startswith("#")]
    ban_re = re.compile("|".join(rf"\b{re.escape(t)}\b" for t in banned), re.I) if banned else None
    for s in spans(page):
        size = round(s["size"], 1)
        txt = s["text"].strip()
        if size < a.floor - 0.05:
            fails.append(f"{size} pt text below the {a.floor} pt floor: '{txt[:30]}'")
        if abs(size - a.letter_pt) > 0.05:
            sizes.setdefault(size, txt)
        if is_gray(s["color"]):
            fails.append(f"gray text #{s['color']:06X}: '{txt[:30]}'")
        elif s["color"] not in (0, 0x111111, 0xFFFFFF):
            warns.append(f"colored text #{s['color']:06X}: '{txt[:30]}' (hero label only)")
        x0, y0, x1, y1 = s["bbox"]
        if x0 < -0.5 or y0 < -0.5 or x1 > page.rect.width + 0.5 or y1 > page.rect.height + 0.5:
            fails.append(f"text off the page: '{txt[:30]}'")
        if ban_re and ban_re.search(txt):
            fails.append(f"banned word in '{txt[:40]}'")
        if s["flat"]:
            boxes.append((fitz.Rect(s["bbox"]), txt))
    shrink = 0.25 * MM_PT          # ignore touching boxes and the ascender band of tight multi-line labels
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            r1, r2 = boxes[i][0], boxes[j][0]
            inter = fitz.Rect(r1) & fitz.Rect(r2)
            if (not inter.is_empty and inter.width > shrink
                    and inter.height > max(shrink, 0.4 * min(r1.height, r2.height))):
                fails.append(f"text overlaps: '{boxes[i][1][:20]}' and '{boxes[j][1][:20]}'")
    n = len(sizes)
    info.append(f"{n} text size(s) besides letters: {sorted(sizes)}")
    if n > a.max_tiers:
        fails.append(f"{n} text sizes; the house rule is 3 tiers (7/6/5 pt), 4 at most")
    elif n == a.max_tiers and n > 3:
        warns.append(f"{n} text sizes; aim for 3")
    return info, fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pdfs", nargs="*", type=Path, help="panel PDFs (any size)")
    ap.add_argument("--figure", action="append", default=[], type=Path,
                    help="a composed figure PDF; repeat for several. Only these are checked for size")
    ap.add_argument("--figure-width", type=float, help="expected width of each --figure in mm")
    ap.add_argument("--figure-height", type=float, help="expected height of each --figure in mm")
    ap.add_argument("--floor", type=float, default=5.0, help="smallest allowed text in pt (default 5)")
    ap.add_argument("--letter-pt", type=float, default=8.0, help="panel-letter size, excluded from the tier count")
    ap.add_argument("--max-tiers", type=int, default=4, help="text sizes allowed besides letters (default 4)")
    ap.add_argument("--ban", help="file of words that must never print, one per line")
    ap.add_argument("--allow-dejavu", action="store_true", help="accept DejaVu (math symbols in some fonts)")
    a = ap.parse_args()
    if not a.pdfs and not a.figure:
        ap.error("give panel PDFs and/or --figure PDF")
    if (a.figure_width or a.figure_height) and not a.figure:
        ap.error("--figure-width/--figure-height apply only to files given with --figure")
    bad = 0
    items = [(p, False) for p in a.pdfs] + [(p, True) for p in a.figure]
    for p, is_fig in items:
        if not p.is_file():
            print(f"FAIL {p}: not found")
            bad += 1
            continue
        info, fails, warns = check(p, a, is_fig)
        print(f"{'FAIL' if fails else 'ok  '} {p.name}: " + "; ".join(info))
        for f in dict.fromkeys(fails):
            print("     fail:", f)
        for w in dict.fromkeys(warns):
            print("     warn:", w)
        bad += bool(fails)
    print(f"\n{len(items)} file(s) checked, {bad} failed. Not checked: labels on data marks, meaning, color roles.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

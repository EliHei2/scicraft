#!/usr/bin/env python3
"""Dump and check the line breaks of a poster PDF: one-word last lines (runts) and hyphenated titles.

Reads the paragraphs (blocks) and lines poppler finds with `pdftotext -bbox-layout` and reports
  runt              a paragraph of two or more lines whose last line holds one word
  hyphenated title  a line that ends in a hyphenated break in type at or above --title-pt
and, with --list-hyphens, every other hyphenated line end (allowed, but look at them).

usage:
    python3 line_breaks.py build/poster_design.pdf --scale 0.841
                           [--title-pt 30] [--boxes build/poster_design.log --figure-boxes f1,f2]
                           [--dump] [--list-hyphens]

  --scale         print scale of this PDF (0.841 for a 1000 mm design page printed on A0)
  --title-pt      printed size from which a line counts as a title (default 30 pt: section
                  titles print at about 39 pt, abstract text at about 28 pt)
  --figure-boxes  BOX names (from --boxes LOG) of placed figures: their labels are skipped
  --dump          print the last line of every paragraph, to read them all once

poppler decides what a paragraph is, so a short label column can read as a paragraph of
one-word lines: read the findings before changing the source. Exit status 1 on a runt or a
hyphenated title. Needs Python 3.9+ and poppler's pdftotext and pdfinfo on the PATH.
"""
import argparse
import html
import re
import subprocess
import sys

PT_PER_CM = 72 / 2.54
H_PER_PT = 1.175          # Helvetica Neue word-box height / type size (poppler), as in layout_check.py
MATH = re.compile("[\u23de\u23df\ufe37\ufe38\u2211\u222b\u2016\U0001d400-\U0001d7ff]")
TOKEN = re.compile(r'<(block|line)\b|<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')


def page_height(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    return float(re.search(r"Page size:\s+[\d.]+ x ([\d.]+) pts", out).group(1))


def blocks(pdf):
    xml = subprocess.run(["pdftotext", "-bbox-layout", "-f", "1", "-l", "1", pdf, "-"],
                         capture_output=True, text=True, check=True).stdout
    out = []
    for m in TOKEN.finditer(xml):
        if m.group(1) == "block":
            out.append([])
        elif m.group(1) == "line":
            out[-1].append([])
        else:
            x0, y0, x1, y1 = map(float, m.groups()[1:5])
            out[-1][-1].append((html.unescape(m.group(6)), (x0, y0, x1, y1)))
    return [[ln for ln in b if ln] for b in out if any(b)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--h-per-pt", type=float, default=H_PER_PT,
                    help="word-box height / type size of the face (1.175 Helvetica Neue, about 1.0 Latin Modern Sans)")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--title-pt", type=float, default=30.0)
    ap.add_argument("--boxes")
    ap.add_argument("--figure-boxes", default="")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--list-hyphens", action="store_true")
    a = ap.parse_args()

    H = page_height(a.pdf)
    figs = []
    if a.figure_boxes:
        if not a.boxes:
            ap.error("--figure-boxes needs --boxes LOG")
        want = set(a.figure_boxes.split(","))
        log = open(a.boxes, encoding="utf-8", errors="replace").read()
        figs = [tuple(map(float, m[1:])) for m in re.findall(r"^BOX (\S+) (\S+) (\S+) (\S+) (\S+)$", log, re.M)
                if m[0] in want]

    def skipped(line):
        x0, y0, x1, y1 = line[0][1]
        cx, cy = (x0 + x1) / 2 / PT_PER_CM, (H - (y0 + y1) / 2) / PT_PER_CM
        return any(fx0 <= cx <= fx1 and fy0 <= cy <= fy1 for fx0, fy0, fx1, fy1 in figs)

    def size(word):
        x0, y0, x1, y1 = word[1]
        return (y1 - y0) / a.h_per_pt * a.scale

    def where(word):
        x0, y0 = word[1][:2]
        return f"@({x0 / PT_PER_CM:.1f},{(H - y0) / PT_PER_CM:.1f})cm"

    bad, hyph, n_par = [], [], 0
    for b in blocks(a.pdf):
        if skipped(b[0]):
            continue
        if len(b) >= 2:
            n_par += 1
            last = [w for w in b[-1] if re.search(r"\w", w[0])]
            text = " ".join(w[0] for w in b[-1])
            if a.dump:
                print(f"last line {where(b[-1][0])} ~{size(b[-1][0]):.0f} pt: {text}")
            if len(last) == 1 and not MATH.search(text):     # a brace label or a formula line is maths
                bad.append(f"runt             {where(b[-1][0])} '{text}' ends: "
                           f"{' '.join(w[0] for w in b[-2][-6:])} / {text}")
        for k, ln in enumerate(b[:-1]):
            w = ln[-1]
            nxt = b[k + 1][0][0]
            if w[0].endswith("-") and len(w[0]) > 1 and nxt[:1].islower():
                msg = f"{where(w)} ~{size(w):.0f} pt: {w[0]}{nxt}"
                if size(w) >= a.title_pt:
                    bad.append(f"hyphenated title {msg}")
                else:
                    hyph.append(msg)
    if a.list_hyphens:
        for h in hyph:
            print(f"hyphen (allowed) {h}")
    for m in bad:
        print(m)
    print(f"{n_par} paragraphs of two or more lines, {len(hyph)} hyphenated line ends in body type, "
          f"{len(bad)} findings  [{a.pdf}]")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
r"""Layout audit for a poster PDF and its standalone figures, from the word boxes poppler reports.

usage: python3 -I layout_check.py FILE.pdf [--graphics NOTEXT.pdf] [--size WxH] [--minpt 20]
                                 [--dpi 40] [--out PREFIX]

Run it on the file that is printed (the A0 sheet), so --minpt is the type size at print:
    python3 -I layout_check.py poster.pdf --minpt 14 --dpi 20 --out build/poster

  --graphics   the same page built with every text node invisible (a build switch of your own,
               such as \NoText); enables the text/graphics test. The poster template does not
               build such a variant.

  --size WxH   expected page size in cm (e.g. 64x27); fails if the PDF page differs by >0.05 cm,
               which is how a figure that draws outside its declared box is caught
  --minpt      smallest allowed type size at final scale (estimated from word-box height)
  --dpi        raster resolution for the text-over-graphics test
  --out        write PREFIX_marked.png with every finding outlined

Checks
  text/text      word boxes from different lines that intersect (after trimming the font's
                 ascender/descender padding)
  text/graphics  words whose box sits on drawn edges (lines, dots, frames) in a text-free render;
                 a word on a flat fill is fine, a word crossing a stroke is not
  size           words smaller than --minpt (tokens of <= 4 characters, i.e. sub/superscripts,
                 may go down to 0.7 x minpt)
Exit status 1 if anything is found. Findings are printed one per line, with the words involved.

Needs Python 3.9+, numpy, Pillow, and poppler's pdfinfo, pdftotext and pdftoppm on the PATH.
The size estimate assumes Helvetica Neue (word-box height = 1.175 x type size); for another face
measure one known size first (a section title of known size in `pdftotext -bbox-layout`) and pass
--h-per-pt (about 1.0 for Latin Modern Sans).
"""
import argparse
import html
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

PT_PER_CM = 72 / 2.54
H_PER_PT = 1.175          # Helvetica Neue word-box height / type size (poppler)
BRACES = set("\u23df\u23de\ufe38\ufe37")   # bottom and top curly brackets drawn by maths fonts


def page_size_pt(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", out)
    return float(m.group(1)), float(m.group(2))


def words(pdf):
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as t:
        tmp = t.name
    subprocess.run(["pdftotext", "-bbox-layout", "-f", "1", "-l", "1", pdf, tmp], check=True)
    txt = open(tmp, encoding="utf-8").read()
    os.unlink(tmp)
    out, line = [], -1
    for tok in re.finditer(r"<line |<word xMin=\"([\d.]+)\" yMin=\"([\d.]+)\" xMax=\"([\d.]+)\" "
                           r"yMax=\"([\d.]+)\">(.*?)</word>", txt):
        if tok.group(0).startswith("<line"):
            line += 1
            continue
        x0, y0, x1, y1 = map(float, tok.groups()[:4])
        out.append(dict(box=(x0, y0, x1, y1), text=html.unescape(tok.group(5)), line=line))
    return out


def trimmed(b):
    x0, y0, x1, y1 = b
    h = y1 - y0
    # poppler boxes span ascender..descender; trim to roughly cap-height..baseline-ish
    return (x0 + 0.02 * h, y0 + 0.20 * h, x1 - 0.02 * h, y1 - 0.12 * h)


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w > 0 and h > 0


def graphics_raster(pdf, dpi):
    return np.asarray(full_raster(pdf, dpi).convert("L"), dtype=np.int16)


def full_raster(pdf, dpi):
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "f")
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", "1", "-l", "1", pdf, base], check=True)
        name = [f for f in os.listdir(d) if f.endswith(".png")][0]
        return Image.open(os.path.join(d, name)).convert("RGB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--graphics")
    ap.add_argument("--size")
    ap.add_argument("--minpt", type=float, default=20)
    ap.add_argument("--dpi", type=int, default=40)
    ap.add_argument("--out")
    ap.add_argument("--h-per-pt", type=float, default=H_PER_PT,
                    help="word-box height / type size of the face (1.175 Helvetica Neue, about 1.0 Latin Modern Sans)")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="print scale of this PDF (0.841 for a 1000 mm design page printed on A0); "
                         "--minpt and reported sizes are then printed pt")
    ap.add_argument("--boxes", help="LaTeX log with BOX lines (box_check.py format), for --figure-boxes")
    ap.add_argument("--figure-boxes", default="",
                    help="comma-separated BOX names of placed figures: findings inside them are listed "
                         "for a look and do not fail the run (the paper's own labels are judged by eye)")
    a = ap.parse_args()
    figs = []
    if a.figure_boxes:
        if not a.boxes:
            ap.error("--figure-boxes needs --boxes LOG")
        want = set(a.figure_boxes.split(","))
        logtxt = open(a.boxes, encoding="utf-8", errors="replace").read()
        figs = [tuple(map(float, m[1:])) for m in re.findall(r"^BOX (\S+) (\S+) (\S+) (\S+) (\S+)$", logtxt, re.M)
                if m[0] in want]
        if len(figs) != len(want):
            print(f"warning: {len(want) - len(figs)} of the --figure-boxes names are not in {a.boxes}")

    bad = []
    W, H = page_size_pt(a.pdf)
    if a.size:
        ew, eh = (float(v) * PT_PER_CM for v in a.size.lower().split("x"))
        if abs(W - ew) > 0.05 * PT_PER_CM or abs(H - eh) > 0.05 * PT_PER_CM:
            bad.append(("size", None, None,
                        f"page is {W / PT_PER_CM:.2f} x {H / PT_PER_CM:.2f} cm, expected {a.size} cm "
                        f"(something is drawn outside the declared box, or the box is wrong)"))

    ws = words(a.pdf)

    def in_figure(i):
        if i is None or not figs:
            return False
        x0, y0, x1, y1 = ws[i]["box"]
        cx, cy = (x0 + x1) / 2 / PT_PER_CM, (H - (y0 + y1) / 2) / PT_PER_CM   # cm from the bottom-left
        return any(fx0 <= cx <= fx1 and fy0 <= cy <= fy1 for fx0, fy0, fx1, fy1 in figs)

    # text / text
    tb = [trimmed(w["box"]) for w in ws]
    order = sorted(range(len(ws)), key=lambda i: tb[i][0])
    for k, i in enumerate(order):
        for j in order[k + 1:]:
            if tb[j][0] >= tb[i][2]:
                break
            if ws[i]["line"] != ws[j]["line"] and inter(tb[i], tb[j]):
                if set(ws[i]["text"]) <= BRACES or set(ws[j]["text"]) <= BRACES:
                    continue                      # an under- or overbrace glyph overlaps its own label
                bad.append(("text/text", i, j, f"'{ws[i]['text']}'  x  '{ws[j]['text']}'"))

    # text / graphics
    g = graphics_raster(a.graphics, a.dpi) if a.graphics else None
    if g is not None:
        s = g.shape[1] / W
        gx = np.abs(np.diff(g, axis=1))
        gy = np.abs(np.diff(g, axis=0))
    for i, w in enumerate(ws if g is not None else []):
        x0, y0, x1, y1 = trimmed(w["box"])
        pad = 1.0
        c0, r0 = int((x0 - pad) * s), int((y0 - pad) * s)
        c1, r1 = int(np.ceil((x1 + pad) * s)), int(np.ceil((y1 + pad) * s))
        c0, r0 = max(c0, 0), max(r0, 0)
        c1, r1 = min(c1, g.shape[1] - 1), min(r1, g.shape[0] - 1)
        if c1 - c0 < 2 or r1 - r0 < 2:
            continue
        e = (gx[r0:r1, c0:c1 - 1] > 60).sum() + (gy[r0:r1 - 1, c0:c1] > 60).sum()
        if e > max(3, 0.004 * (c1 - c0) * (r1 - r0)):
            bad.append(("text/graphics", i, None, f"'{w['text']}' sits on drawn edges ({e} px)"))

    # size
    for i, w in enumerate(ws):
        x0, y0, x1, y1 = w["box"]
        pt = (y1 - y0) / a.h_per_pt * a.scale
        # short tokens are usually math sub/superscripts (pred, i, (l)): allowed down to 0.7 x minpt
        lim = a.minpt * (0.7 if len(w["text"]) <= 4 else 1.0)
        if pt < lim - 0.5:
            bad.append(("size", i, None, f"'{w['text']}' is ~{pt:.0f} pt (< {lim:.0f})"))

    look = [b for b in bad if in_figure(b[1]) or in_figure(b[2])]
    fail = [b for b in bad if b not in look]
    for label, group in (("", fail), ("in figure, look at it: ", look)):
        for kind, i, j, msg in group:
            where = ""
            if i is not None:
                x0, y0 = ws[i]["box"][:2]
                where = f"@({x0 / PT_PER_CM:.1f},{(H - y0) / PT_PER_CM:.1f})cm "
            print(f"{label}{kind:14s} {where}{msg}")
    print(f"{len(ws)} words checked, {len(fail)} findings"
          + (f", {len(look)} more inside placed figures" if figs else "") + f"  [{a.pdf}]")

    if a.out:
        img = full_raster(a.pdf, a.dpi)
        sc = img.size[0] / W
        d = ImageDraw.Draw(img)
        col = {"text/text": (230, 0, 0), "text/graphics": (255, 140, 0), "size": (160, 0, 200)}
        for kind, i, j, _ in bad:
            for k in (i, j):
                if k is None:
                    continue
                x0, y0, x1, y1 = ws[k]["box"]
                d.rectangle([x0 * sc - 2, y0 * sc - 2, x1 * sc + 2, y1 * sc + 2], outline=col[kind], width=2)
        img.save(f"{a.out}_marked.png")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

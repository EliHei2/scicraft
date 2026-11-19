#!/usr/bin/env python3
"""Render a source figure (one PDF page, or a PNG or JPEG) with a labelled coordinate grid in SOURCE units
(PDF points or pixels, origin top-left), so crop boxes and letter masks for compose_crops.py can be read off it.

Usage:
  python3 gridprev.py SRC OUT.png [--step 50] [--clip x0 y0 x1 y1] [--width 1500] [--page 0]

Magenta vertical lines carry x, blue horizontal lines carry y; every second line is darker. Zoom into a
region with --clip and a smaller --step to place a mask on a panel letter to a fraction of a point.

Requires Python 3.9+, PyMuPDF (fitz), Pillow.
"""
import argparse
import math

import fitz
from PIL import Image, ImageDraw, ImageFont

FONTS = ['/System/Library/Fonts/Supplemental/Arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', 'C:/Windows/Fonts/arial.ttf']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--step', type=float, default=50, help='grid step in source units (default 50)')
    ap.add_argument('--clip', type=float, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'), help='region to show')
    ap.add_argument('--width', type=int, default=1500, help='output width in px (default 1500)')
    ap.add_argument('--page', type=int, default=0, help='PDF page index (default 0)')
    a = ap.parse_args()
    step = a.step
    if a.src.lower().endswith('.pdf'):
        pg = fitz.open(a.src)[a.page]
        c = fitz.Rect(a.clip) if a.clip else pg.rect
        z = a.width / c.width
        pix = pg.get_pixmap(matrix=fitz.Matrix(z, z), clip=c, alpha=False)
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    else:
        full = Image.open(a.src).convert('RGB')
        c = fitz.Rect(a.clip) if a.clip else fitz.Rect(0, 0, full.width, full.height)
        im = full.crop([int(v) for v in c])
        z = a.width / im.width
        im = im.resize((a.width, int(im.height * z)), Image.LANCZOS)
    dr = ImageDraw.Draw(im)
    f = None
    for p in FONTS:
        try:
            f = ImageFont.truetype(p, 13)
            break
        except Exception:
            continue
    f = f or ImageFont.load_default()
    x = math.ceil(c.x0 / step) * step
    while x <= c.x1:
        X = (x - c.x0) * z
        dr.line([(X, 0), (X, im.height)], fill=(255, 0, 255) if x % (step * 2) == 0 else (255, 160, 255), width=1)
        dr.text((X + 2, 2), f'{x:g}', fill=(200, 0, 200), font=f)
        x += step
    y = math.ceil(c.y0 / step) * step
    while y <= c.y1:
        Y = (y - c.y0) * z
        dr.line([(0, Y), (im.width, Y)], fill=(0, 160, 255) if y % (step * 2) == 0 else (150, 210, 255), width=1)
        dr.text((2, Y + 2), f'{y:g}', fill=(0, 100, 220), font=f)
        y += step
    im.save(a.out)
    print(a.out, im.size, 'zoom', round(z, 3))


if __name__ == '__main__':
    main()

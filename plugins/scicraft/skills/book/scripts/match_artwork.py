#!/usr/bin/env python3
"""Test whether candidate figure sources are the same artwork as a reference raster (gray-level correlation).

A paper's vector figure files and the raster in its latest manuscript drift apart over revisions. Each candidate
(PDF page or image) is rendered in gray at the reference's pixel size, both are resized to a common thumbnail
width, and their Pearson correlation is printed. Above 0.95 means the same artwork; below it, the vector is an
older or a different version, and the raster from the latest manuscript wins.

    python3 match_artwork.py REFERENCE.png CANDIDATE.pdf [CANDIDATE2.pdf ...] [--page 0] [--width 600]
    python3 match_artwork.py --self-test

Prints one line per candidate: r, the verdict, and the row counts compared (a large mismatch means a different
aspect ratio, often a crop or a re-layout). Exit 0 when at least one candidate reaches --threshold.

Requires Python 3.9+, PyMuPDF (fitz), Pillow, numpy.
"""
import argparse
import os
import sys
import tempfile

try:
    import fitz  # PyMuPDF
    import numpy as np
    from PIL import Image, ImageDraw
except ImportError as e:
    sys.exit(f'match_artwork.py needs PyMuPDF, Pillow and numpy ({e})')


def gray(im, width):
    im = im.convert('L')
    h = max(1, int(im.height * width / im.width))
    return np.asarray(im.resize((width, h), Image.LANCZOS), float)


def render(path, size, page):
    if not path.lower().endswith('.pdf'):
        return Image.open(path)
    p = fitz.open(path)[page]
    z = size[0] / p.rect.width
    pix = p.get_pixmap(matrix=fitz.Matrix(z, z), colorspace=fitz.csGRAY, alpha=False)
    return Image.frombytes('L', (pix.width, pix.height), pix.samples)


def score(ref_path, cand, page, width):
    ref = Image.open(ref_path)
    a = gray(ref, width)
    b = gray(render(cand, ref.size, page), width)
    h = min(a.shape[0], b.shape[0])
    r = float(np.corrcoef(a[:h].ravel(), b[:h].ravel())[0, 1])
    return r, a.shape[0], b.shape[0]


def self_test():
    with tempfile.TemporaryDirectory() as d:
        im = Image.new('RGB', (400, 300), 'white')
        dr = ImageDraw.Draw(im)
        for i in range(8):
            dr.rectangle([30 + 40 * i, 250 - 25 * i, 55 + 40 * i, 250], fill=(40, 90, 200))
        dr.line([20, 20, 20, 260], fill='black', width=3)
        ref = os.path.join(d, 'ref.png')
        im.save(ref)
        same = os.path.join(d, 'same.pdf')
        doc = fitz.open()
        pg = doc.new_page(width=200, height=150)
        pg.insert_image(pg.rect, filename=ref)
        doc.save(same)
        other = os.path.join(d, 'other.pdf')
        doc = fitz.open()
        pg = doc.new_page(width=200, height=150)
        for i in range(8):
            pg.draw_rect(fitz.Rect(15 + 20 * i, 20 + 10 * i, 28 + 20 * i, 125), fill=(0.8, 0.2, 0.1), color=None)
        doc.save(other)
        r1, _, _ = score(ref, same, 0, 300)
        r2, _, _ = score(ref, other, 0, 300)
    ok = r1 > 0.95 > r2
    print(f'self-test {"passed" if ok else "FAILED"}: same artwork r={r1:.3f}, different r={r2:.3f}')
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('reference', nargs='?', help='raster from the latest manuscript (PNG, JPEG, TIFF)')
    ap.add_argument('candidates', nargs='*', help='vector PDFs or images to test')
    ap.add_argument('--page', type=int, default=0, help='PDF page index of each candidate (default 0)')
    ap.add_argument('--width', type=int, default=600, help='thumbnail width in px (default 600)')
    ap.add_argument('--threshold', type=float, default=0.95, help='same-artwork threshold (default 0.95)')
    ap.add_argument('--self-test', action='store_true', help='run on synthetic artwork and exit')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.reference or not a.candidates:
        ap.error('give REFERENCE and at least one CANDIDATE')
    best = -1.0
    for c in a.candidates:
        if not os.path.exists(c):
            print(f'{c}: missing')
            continue
        r, ra, rb = score(a.reference, c, a.page, a.width)
        best = max(best, r)
        verdict = 'same artwork' if r >= a.threshold else 'different or older version'
        print(f'{os.path.basename(c)}: r={r:.3f} ({verdict}); rows {ra}/{rb}')
    return 0 if best >= a.threshold else 1


if __name__ == '__main__':
    sys.exit(main())

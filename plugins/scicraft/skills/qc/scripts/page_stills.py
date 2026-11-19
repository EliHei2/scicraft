#!/usr/bin/env python3
"""Render pages of a PDF to PNG so they can be looked at: chosen pages, a contact sheet of many, or a figure map.

    python3 page_stills.py DOC.pdf OUTDIR --labels 7 xii 23      pages by their printed label (what the author cites)
    python3 page_stills.py DOC.pdf OUTDIR --pages 1,8-10 --dpi 110   pages by physical number, 1-based
    python3 page_stills.py DOC.pdf OUTDIR --sheet 1-40 --cols 8   all those pages on one contact sheet
    python3 page_stills.py DOC.pdf --figs                         figure, table and algorithm number -> page

Why: scripts find what can be measured; a caption that does not match its figure, a float stranded on a mostly
empty page, a label printed over a line, a wrapped figure whose caption runs into the text, a near-empty last page
are found by looking. Read the PNGs it writes. Working resolution: 100 to 150 dpi for a page, 50 to 70 dpi for a
sheet, a crop at two to three times that for fine labels (--dpi 300 on one page).

Needs PyMuPDF (pip install pymupdf). Exits 1 if the PDF cannot be opened or a requested page does not exist.
"""
import argparse
import os
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.exit('needs PyMuPDF: pip install pymupdf')


def parse_range(spec, n):
    out = []
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        a, _, b = part.partition('-')
        lo, hi = int(a), int(b or a)
        if lo < 1 or hi > n or lo > hi:
            sys.exit(f'page range {part} outside 1 to {n}')
        out += list(range(lo - 1, hi))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('pdf')
    ap.add_argument('outdir', nargs='?')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--labels', nargs='+', help='printed page labels, e.g. 7 xii')
    g.add_argument('--pages', help='physical pages, e.g. 1,8-10')
    g.add_argument('--sheet', help='physical pages for one contact sheet, e.g. 1-40')
    g.add_argument('--figs', action='store_true', help='print figure/table/algorithm number to page and exit')
    ap.add_argument('--dpi', type=int, default=110)
    ap.add_argument('--cols', type=int, default=8, help='columns of the contact sheet')
    a = ap.parse_args()

    try:
        doc = fitz.open(a.pdf)
    except Exception as e:  # noqa: BLE001
        sys.exit(f'cannot open {a.pdf}: {e}')
    n = doc.page_count

    if a.figs:
        for i in range(n):
            for m in re.finditer(r'(Figure|Fig\.|Table|Algorithm) ([A-Z]?\d+(?:\.\d+)?)[:.]', doc[i].get_text()):
                print(m.group(1), m.group(2), 'label', doc[i].get_label() or i + 1, 'page', i + 1)
        return
    if not a.outdir:
        sys.exit('OUTDIR is needed to render')
    os.makedirs(a.outdir, exist_ok=True)

    if a.sheet:
        idx = parse_range(a.sheet, n)
        r0 = doc[idx[0]].rect
        cw, ch, pad = r0.width, r0.height, r0.width * 0.04
        cols = max(1, min(a.cols, len(idx)))
        rows = (len(idx) + cols - 1) // cols
        sheet = fitz.open()
        pg = sheet.new_page(width=cols * (cw + pad) + pad, height=rows * (ch + pad * 2) + pad)
        for k, i in enumerate(idx):
            x, y = pad + (k % cols) * (cw + pad), pad + (k // cols) * (ch + pad * 2)
            box = fitz.Rect(x, y, x + cw, y + ch)
            pg.show_pdf_page(box, doc, i)
            pg.draw_rect(box, color=(0.6, 0.6, 0.6), width=max(0.5, pad * 0.05))   # page edge on a white sheet
            pg.insert_text((x, y + ch + pad * 1.2), str(doc[i].get_label() or i + 1), fontsize=pad * 1.1)
        out = os.path.join(a.outdir, f'sheet_{idx[0] + 1:03d}-{idx[-1] + 1:03d}.png')
        pg.get_pixmap(dpi=a.dpi).save(out)
        print(out, f'{len(idx)} pages')
        return

    if a.labels:
        labels = {doc[i].get_label(): i for i in range(n)}
        idx, missing = [], []
        for lab in a.labels:
            if lab in labels:
                idx.append(labels[lab])
            elif lab.isdigit() and not any(labels) and 1 <= int(lab) <= n:   # PDF without page labels
                idx.append(int(lab) - 1)
            else:
                missing.append(lab)
        if missing:
            print('no page with label', ' '.join(missing))
    else:
        idx, missing = parse_range(a.pages, n), []
    for i in idx:
        lab = doc[i].get_label() or str(i + 1)
        out = os.path.join(a.outdir, f'pg_{i + 1:03d}_{lab}.png')
        doc[i].get_pixmap(dpi=a.dpi).save(out)
        print(out)
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()

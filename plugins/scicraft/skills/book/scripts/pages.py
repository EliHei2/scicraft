#!/usr/bin/env python3
"""Look at a typeset PDF: render pages by label, map figures to pages, make a contact sheet, count pages.

  python3 pages.py book.pdf render OUTDIR 70 12 13 xii       render pages by printed label at 70 dpi
  python3 pages.py book.pdf figs                              "Figure 3.2 label 41 phys 57" per caption
  python3 pages.py book.pdf sheet 35 50 sheet.png             pages 35-50 (PDF numbers) on one image
        [--dpi 28] [--cols 6]
  python3 pages.py book.pdf count [--budget 200]             pages in all and before the bibliography
        [--heading "References|Bibliography"]

`count` finds the first page of the bibliography from the PDF outline, or else from the first lines of each
page counted back from the end, and reports the pages before it. A budget stated "excluding references" is
checked against that number after every build, because float changes move it by several pages; with --budget
the command exits 1 when it is exceeded.

Read the PNGs: a gate count cannot see a figure stranded at the end of a chapter, a wrapfigure caption printed
over body text, a near-empty last page or a blank verso.

Requires Python 3.9+, PyMuPDF (fitz), Pillow (sheet only).
"""
import argparse
import os
import re
import sys

import fitz


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pdf')
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('render')
    r.add_argument('outdir')
    r.add_argument('dpi', type=int)
    r.add_argument('labels', nargs='+')
    sub.add_parser('figs')
    s = sub.add_parser('sheet')
    s.add_argument('first', type=int)
    s.add_argument('last', type=int)
    s.add_argument('out')
    s.add_argument('--dpi', type=int, default=28)
    s.add_argument('--cols', type=int, default=6)
    c = sub.add_parser('count')
    c.add_argument('--heading', default='References|Bibliography', help='regex of the bibliography heading')
    c.add_argument('--budget', type=int, help='maximum pages before the bibliography')
    a = ap.parse_args()
    doc = fitz.open(a.pdf)
    if a.cmd == 'count':
        rx = re.compile(rf'^\s*(?:\d+\s+)?(?:{a.heading})\s*$', re.I)
        start = next((p for lvl, title, p in doc.get_toc() if rx.match(title)), None)
        how = 'outline'
        if start is None:
            how = 'page text'
            for i in range(doc.page_count - 1, -1, -1):
                head = [ln for ln in doc[i].get_text().splitlines() if ln.strip()][:3]
                if any(rx.match(ln) for ln in head):
                    start = i + 1
                    break
        if start is None:
            print(f'{doc.page_count} pages; no bibliography heading matching "{a.heading}" found')
            return 1
        before = start - 1
        label = doc[start - 1].get_label() or str(start)
        print(f'{doc.page_count} pages, {before} before the bibliography '
              f'(it starts on PDF page {start}, printed {label}; found from the {how})')
        if a.budget is not None and before > a.budget:
            print(f'FAILED: {before} pages without references exceed the budget of {a.budget}')
            return 1
        return 0
    if a.cmd == 'figs':
        for i in range(doc.page_count):
            for m in re.finditer(r'(Figure|Table|Algorithm) ([A-Z0-9]+\.\d+)[:.]', doc[i].get_text()):
                print(m.group(1), m.group(2), 'label', doc[i].get_label() or i + 1, 'phys', i + 1)
        return 0
    if a.cmd == 'render':
        labels = {doc[i].get_label() or str(i + 1): i for i in range(doc.page_count)}
        os.makedirs(a.outdir, exist_ok=True)
        missing = 0
        for lab in a.labels:
            i = labels.get(lab)
            if i is None:
                print('no page labelled', lab)
                missing += 1
                continue
            p = os.path.join(a.outdir, f'pg_{i + 1:03d}_{lab}.png')
            doc[i].get_pixmap(dpi=a.dpi).save(p)
            print(p)
        return 1 if missing else 0
    from PIL import Image
    pages = range(max(1, a.first) - 1, min(a.last, doc.page_count))
    ims = []
    for i in pages:
        pix = doc[i].get_pixmap(dpi=a.dpi, alpha=False)
        ims.append(Image.frombytes('RGB', (pix.width, pix.height), pix.samples))
    if not ims:
        sys.exit('FAILED: no pages in that range')
    w, h = max(im.width for im in ims), max(im.height for im in ims)
    rows = (len(ims) + a.cols - 1) // a.cols
    sheet = Image.new('RGB', (a.cols * (w + 6) + 6, rows * (h + 6) + 6), (128, 128, 128))
    for k, im in enumerate(ims):
        sheet.paste(im, (6 + (k % a.cols) * (w + 6), 6 + (k // a.cols) * (h + 6)))
    sheet.save(a.out)
    print(a.out, sheet.size, f'pages {pages.start + 1}-{pages.stop}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

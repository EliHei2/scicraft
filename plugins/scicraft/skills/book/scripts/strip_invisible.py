#!/usr/bin/env python3
"""Remove invisible text from a one-page PDF figure, keeping its rendering pixel-identical.

A cropped or recomposed figure often still carries text nobody sees: the source manuscript's running heads,
panels clipped away, earlier layers of a diagram covered by later ones. Similarity checkers, library
full-text indexes and screen readers read it. This script drops it.

Pass 1 drops whole BT...ET blocks, pass 2 blanks single text-showing operators, in every content stream (the
page and its form XObjects). A change is kept only if the page renders identically at 150 dpi; the result is
verified at 150 and 400 dpi against the input before it is written. compose_crops.py calls main() on every figure
it saves.

Usage:
  python3 strip_invisible.py IN.pdf OUT.pdf
Afterwards `pdftotext OUT.pdf -` must print only the labels a reader can see.

Requires Python 3.9+ and PyMuPDF (fitz).
"""
import argparse
import re
import sys

import fitz

BLOCK = re.compile(rb'(?<![A-Za-z])BT(?![A-Za-z]).*?(?<![A-Za-z])ET(?![A-Za-z])', re.S)
STR = rb'(?:\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>)'
OPS = re.compile(rb'(' + STR + rb')(\s*(?:Tj|\'|"))|(\[(?:' + STR + rb'|[^\]])*\])(\s*TJ)', re.S)


def render(doc, dpi=150):
    return doc[0].get_pixmap(dpi=dpi, alpha=False).samples


def streams(doc):
    page = doc[0]
    return [x for x in list(page.get_contents()) + sorted({x[0] for x in page.get_xobjects()})
            if doc.xref_is_stream(x) and doc.xref_stream(x)]


def sweep(doc, base, pattern, blank_for):
    n = 0
    for xref in streams(doc):
        s = doc.xref_stream(xref)
        cuts = []
        for m in pattern.finditer(s):
            a, b, blank = blank_for(m)
            doc.update_stream(xref, s[:a] + blank + s[b:])
            if render(doc) == base:
                cuts.append((a, b, blank))
            doc.update_stream(xref, s)
        if cuts:
            out, last = b'', 0
            for a, b, blank in cuts:
                out += s[last:a] + blank
                last = b
            doc.update_stream(xref, out + s[last:])
            n += len(cuts)
    return n


def main(src, dst):
    doc = fitz.open(src)
    base = render(doc)
    n1 = sweep(doc, base, BLOCK, lambda m: (m.start(), m.end(), b''))
    n2 = sweep(doc, base, OPS, lambda m: (m.span(1) + (b'()',)) if m.group(1) is not None else (m.span(3) + (b'[]',)))
    ref = fitz.open(src)
    for dpi in (150, 400):
        if render(doc, dpi) != render(ref, dpi):
            raise SystemExit(f'FAILED: {src}: render differs at {dpi} dpi; nothing written')
    doc.save(dst, garbage=4, deflate=True, clean=True)
    print(f'{src}: dropped {n1} invisible text blocks, blanked {n2} operators; '
          'render identical at 150 and 400 dpi')
    return n1 + n2


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src', help='one-page PDF figure')
    ap.add_argument('dst', help='output PDF (may not be the input file)')
    a = ap.parse_args()
    if a.src == a.dst:
        sys.exit('FAILED: write to a new file, then replace')
    main(a.src, a.dst)

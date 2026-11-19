#!/usr/bin/env python3
"""TeX labels for canvas figures, as glyph outlines: exact TeX at any size and colour, with no font or image to load.

    python3 tex_labels.py LABELS.json OUT.json [--used-in public/fx] [--border 1.0] [--preamble '\\usepackage{bm}']

LABELS.json maps a label id to TeX in text mode: {"enc": "online encoder $E_\\theta$", "loss": "$\\mathcal L$"}.
Every label is typeset by pdflatex on a page of its own whose size is the label's TeX box plus a border; each page is
read back through PyMuPDF as SVG with text as paths, so the script knows which glyph outline sits where and at what
size, plus any rules (fraction bars). pdftocairo was tried first and rescales small pages slightly, which put the
glyphs in the wrong places; PyMuPDF does not.

OUT.json, read by assets/tex.js in the page:
  glyphs   [d, ...]                      outline path data in em units, y up, shared by all labels
  labels   {id: {w, h, b, g, l?}}        width, height and baseline from the top, in bp at 10 pt;
                                         g = [glyph, size, x, y, ...] flat; l = [x1, y1, x2, y2, width, ...] rules
A label's TeX box (not its ink) sets w, h and b, so labels share a baseline and can be set in a row.

--used-in DIR reads the page code under DIR (.js and .html) for the ids it asks for (tex(ctx, 'id' ...),
texBox('id' ...), texSVG('id' ...), data-tex="id"), leaves out labels no code asks for, and exits 1 if the code asks
for a label LABELS.json does not have. Run it whenever a figure changes.

Needs pdflatex (with amsmath and amssymb) and PyMuPDF (`pip install pymupdf`).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

BP = 72 / 72.27                   # TeX points to PDF points, the unit of the SVG
SVG = '{http://www.w3.org/2000/svg}'
HREF = '{http://www.w3.org/1999/xlink}href'
NUM = re.compile(r'-?\d*\.\d+|-?\d+')
ASKED = re.compile(r"""(?:\btex\(\s*[\w.]+\s*,\s*|\btexBox\(\s*|\btexSVG\(\s*)['"]([^'"]+)['"]|data-tex=['"]([^'"]+)['"]""")


def rnd(d: str, nd=3) -> str:
    """Path data with its numbers rounded: the outlines are drawn at a few tens of pixels per em at most."""
    def short(m):
        v = f'{float(m.group()):.{nd}f}'.rstrip('0').rstrip('.')
        v = v.replace('0.', '.', 1) if v.startswith(('0.', '-0.')) else v
        return v if v not in ('', '-') else '0'
    return NUM.sub(short, d)


def typeset(tmp: Path, labels: dict, border: float, preamble: str) -> dict:
    """One page per label; the log carries each box (width, height, depth) in TeX points."""
    head = (r'\documentclass{article}\usepackage{amsmath,amssymb}' + preamble + r'\pagestyle{empty}\begin{document}' + '\n' +
            r'\newcommand\lab[2]{\setbox0\hbox{#2}\typeout{TEXLAB #1 \the\wd0,\the\ht0,\the\dp0}' +
            r'\pdfpagewidth=\dimexpr\wd0+2\dimexpr BORDERpt\relax\relax\pdfpageheight=\dimexpr\ht0+\dp0+2\dimexpr BORDERpt\relax\relax' +
            r'\pdfhorigin=BORDERpt\pdfvorigin=BORDERpt\shipout\box0}').replace('BORDER', str(border))
    body = '\n'.join(r'\lab{%d}{%s}' % (n, tex) for n, tex in enumerate(labels.values()))
    (tmp / 'labels.tex').write_text(head + '\n' + body + '\n' + r'\end{document}')
    run = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'labels.tex'], cwd=tmp, capture_output=True, text=True)
    if run.returncode:
        sys.exit('pdflatex failed:\n' + run.stdout[-3000:])
    dims = {int(m.group(1)): tuple(float(m.group(i)) for i in (2, 3, 4))
            for m in re.finditer(r'TEXLAB (\d+) ([\d.]+)pt,([\d.]+)pt,([\d.]+)pt', run.stdout)}
    if len(dims) != len(labels):
        sys.exit(f'pdflatex reported {len(dims)} boxes for {len(labels)} labels')
    return dims


def matrix(el):
    m = re.match(r'matrix\(([^)]*)\)', el.get('transform', ''))
    return tuple(float(v) for v in m.group(1).split(',')) if m else (1, 0, 0, 1, 0, 0)


def read_page(svg: str, table: dict, lid: str):
    """(glyph placements, rules) of one page as PyMuPDF writes it; glyph outlines are pooled in `table`."""
    root = ET.fromstring(svg)
    outline = {p.get('id'): rnd(p.get('d'), 3) for p in root.iter(SVG + 'path') if p.get('id', '').startswith('font_')}
    glyphs, rules = [], []
    for u in root.iter(SVG + 'use'):
        d = outline[u.get(HREF)[1:]]
        a, b, c, dd, e, f = matrix(u)
        if not (b == 0 and c == 0 and abs(a + dd) < 1e-6):
            sys.exit(f'{lid}: a glyph is rotated or skewed ({u.get("transform")}); only upright labels are supported')
        if d.strip():
            glyphs += [table.setdefault(d, len(table)), round(a, 4), round(e, 3), round(f, 3)]
    for p in root.iter(SVG + 'path'):
        if p.get('id', '').startswith('font_'):
            continue
        if not (p.get('fill') == 'none' and p.get('stroke')):
            sys.exit(f'{lid}: a filled shape that is not a glyph; only rules (fraction bars) are supported')
        a, b, c, dd, e, f = matrix(p)
        x = y = 0.0
        pts = []
        for cmd, args in re.findall(r'([MLHV])([^MLHV]*)', p.get('d')):
            v = [float(t) for t in NUM.findall(args)]
            if cmd in 'ML':
                x, y = v
            elif cmd == 'H':
                x = v[0]
            else:
                y = v[0]
            pts.append((a * x + c * y + e, b * x + dd * y + f))
        if len(pts) != 2:
            sys.exit(f'{lid}: a path with {len(pts)} points; only straight rules are supported')
        rules += [round(v, 3) for v in (*pts[0], *pts[1], float(p.get('stroke-width')) * abs(a))]
    return glyphs, rules


def asked_for(folder: Path) -> set:
    ids = set()
    for f in sorted(folder.rglob('*')):
        if f.suffix in ('.js', '.mjs', '.html') and f.is_file() and f.name != 'tex.js':      # not the module itself
            for m in ASKED.finditer(f.read_text(errors='replace')):
                ids.add(m.group(1) or m.group(2))
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='\n'.join(__doc__.split('\n')[1:]))
    ap.add_argument('labels', type=Path, help='JSON: {label id: TeX in text mode}')
    ap.add_argument('out', type=Path, help='JSON for the page')
    ap.add_argument('--used-in', type=Path, help='page code to read for the ids it asks for')
    ap.add_argument('--border', type=float, default=1.0, help='pt of clear space around each label (default 1)')
    ap.add_argument('--preamble', default='', help='extra preamble, e.g. \\usepackage{bm}')
    a = ap.parse_args()
    import fitz
    if not shutil.which('pdflatex'):
        sys.exit('pdflatex not found')
    labels = json.loads(a.labels.read_text())
    if a.used_in:
        asked = asked_for(a.used_in)
        missing = sorted(asked - set(labels))
        unused = sorted(set(labels) - asked)
        if unused:
            print(f'left out, no code asks for them: {", ".join(unused)}')
        labels = {k: v for k, v in labels.items() if k in asked}
        if missing:
            sys.exit(f'the page asks for labels that {a.labels.name} does not have: {", ".join(missing)}')
    if not labels:
        sys.exit('no labels to typeset')
    table, out = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        dims = typeset(tmp, labels, a.border, a.preamble)
        doc = fitz.open(tmp / 'labels.pdf')
        if len(doc) != len(labels):
            sys.exit(f'{len(doc)} pages for {len(labels)} labels')
        for n, lid in enumerate(labels):
            g, rules = read_page(doc[n].get_svg_image(text_as_path=True), table, lid)
            wd, ht, dp = dims[n]
            lab = {'w': round((wd + 2 * a.border) * BP, 3), 'h': round((ht + dp + 2 * a.border) * BP, 3),
                   'b': round((ht + a.border) * BP, 3), 'g': g}
            if abs(lab['w'] - doc[n].rect.width) > 0.01 or abs(lab['h'] - doc[n].rect.height) > 0.01:
                sys.exit(f'{lid}: page size and TeX box disagree')
            if not g:
                sys.exit(f'{lid}: typeset to nothing')
            if rules:
                lab['l'] = rules
            out[lid] = lab
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({'glyphs': list(table), 'labels': out}, separators=(',', ':')))
    print(f'{a.out}: {len(out)} labels, {len(table)} glyph outlines, {a.out.stat().st_size / 1e3:.1f} kB')


if __name__ == '__main__':
    main()

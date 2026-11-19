#!/usr/bin/env python3
"""Compose book figures from published panels: crop, mask the source's panel letters, place, re-letter.

Nothing here draws or re-plots. A figure is rows of panels at the full text measure. Inside a row every panel
is scaled to a common height, so panels align top and bottom and the row fills the measure exactly. Vector
sources stay vector (PyMuPDF show_pdf_page with a clip); raster sources (PNG, JPEG) are cropped at native
resolution.

Each panel is cropped from its source in the source's own units (PDF points or pixels, origin top-left; read
the boxes off a gridded preview made with gridprev.py), optionally trimmed to its ink, and the source's panel
letters are painted out with white rectangles given in source units (`masks`) or found automatically in
vector sources (`autoletters`). With compose(..., letters=True) new bold letters a, b, c are set above each
panel, in space reserved for them, so a letter never covers artwork.

On save, every figure is cleaned of hidden text: text more than 8 pt outside each crop is redacted from the
placed source page, and text that stays invisible inside it (clipped panels, covered layers) is removed by
strip_invisible.py with pixel-identical rendering verified at 150 and 400 dpi. A similarity checker or a
screen reader would otherwise read the source manuscript's running heads and hidden layers.

The audit printed for every figure (JSON, one line per figure): the scale of each panel relative to its
source, the smallest and median font size of the live text after scaling (vector panels), the effective
resolution of raster panels, and the number of letters masked. Panels whose smallest text prints below
--min-font (default 5.5 pt) are listed as warnings.

Figures are declared in a spec file (see assets/spec_template.py): a Python module that imports Panel, Stack,
compose (and the helpers redacted, same_scale, fit_row) from this module and defines FIGURES = {name: function}.

Usage:
  python3 compose_crops.py --spec figsrc/spec.py --out figures/                 # all figures in the spec
  python3 compose_crops.py --spec figsrc/spec.py --out figures/ fig_bench       # one figure
  python3 compose_crops.py --spec spec.py --out figures/ --measure 148 --report figure_audit.json --strict

Requires Python 3.9+, PyMuPDF (fitz) 1.24 or later, Pillow, numpy. strip_invisible.py must sit beside this file.
"""
import argparse
import importlib.util
import io
import json
import os
import statistics
import sys
import zlib

import fitz
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import strip_invisible  # noqa: E402

MM = 72 / 25.4        # points per mm
TARGET_DPI = 450      # embedded rasters are resampled to this effective resolution at print size
SLIM_FACTOR = 1.35    # ... when they exceed it by this factor
EDGE_MARGIN = 8.0     # pt: text further than this outside a crop is redacted (1 pt deleted visible edge labels)

CONFIG = dict(out=os.path.abspath('figures'), measure=150.0, letter_font=None, min_font=5.5)
_SLIM_CACHE = {}
_CLEAN_CACHE = {}

LETTER_FONT_CANDIDATES = [
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/Library/Fonts/Arial Bold.ttf',
    '/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'C:/Windows/Fonts/arialbd.ttf',
]


def configure(out=None, measure=None, letter_font=None, min_font=None):
    """Set the output folder, the text measure in mm, the panel-letter font file and the font warning level."""
    if out:
        CONFIG['out'] = os.path.abspath(out)
    if measure:
        CONFIG['measure'] = float(measure)
    if letter_font:
        CONFIG['letter_font'] = letter_font
    if min_font is not None:
        CONFIG['min_font'] = float(min_font)
    for d in (CONFIG['out'], _prev_dir(), _tmp_dir()):
        os.makedirs(d, exist_ok=True)


def _prev_dir():
    return os.path.join(CONFIG['out'], '_preview')


def _tmp_dir():
    return os.path.join(CONFIG['out'], '_tmp')


def _letter_font():
    """An embeddable bold sans for the new panel letters. The base-14 Helvetica-Bold is not embedded,
    and a book PDF must embed every font."""
    if CONFIG['letter_font'] and os.path.exists(CONFIG['letter_font']):
        return CONFIG['letter_font']
    for p in LETTER_FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def slim_doc(src, page, s):
    """A copy of the source PDF whose embedded images are resampled to TARGET_DPI at the
    printed scale s (output pt per source pt). Vector content and text are untouched."""
    key = (src, page, round(s, 3))
    if key in _SLIM_CACHE:
        return _SLIM_CACHE[key]
    doc = fitz.open(src)
    pg = doc[page]
    for it in pg.get_images(full=True):
        xref, smask, w = it[0], it[1], it[2]
        try:
            rects = pg.get_image_rects(xref)
        except Exception:
            rects = []
        if not rects:
            continue
        wpt = max(r.width for r in rects) * s
        if wpt <= 0:
            continue
        dpi = w / (wpt / 72)
        if dpi <= TARGET_DPI * SLIM_FACTOR:
            continue
        f = TARGET_DPI / dpi
        base = fitz.Pixmap(doc, xref)
        if base.n - base.alpha not in (1, 3):
            base = fitz.Pixmap(fitz.csRGB, base)
        mode = {1: 'L', 3: 'RGB'}[base.n - base.alpha] + ('A' if base.alpha else '')
        im = Image.frombytes(mode, (base.width, base.height), base.samples)
        size = (max(1, round(base.width * f)), max(1, round(base.height * f)))
        im = im.convert('RGB').resize(size, Image.LANCZOS)
        # The soft mask is resampled on its own and kept when it has any transparency: compositing it into
        # the color samples and flattening onto white painted over the dark backings some panels sit on.
        alpha = None
        if smask:
            try:
                m = fitz.Pixmap(doc, smask)
                if m.n - m.alpha != 1:
                    m = fitz.Pixmap(fitz.csGRAY, m)
                mi = Image.frombytes('L', (m.width, m.height), m.samples if m.n == 1 else bytes(m.samples[::m.n]))
            except Exception:
                continue   # leave this image untouched rather than risk changing it
            mi = mi.resize(size, Image.LANCZOS)
            if mi.getextrema()[0] < 255:
                alpha = mi
        # Rewrite the image object in place: JPEG when under 60 % of the lossless size, else Flate.
        jpg = io.BytesIO()
        im.save(jpg, format='JPEG', quality=90, subsampling=0)
        raw = im.tobytes()
        flate = zlib.compress(raw, 9)
        W, H = im.size
        for k in ('DecodeParms', 'Decode', 'Intent', 'Interpolate'):
            doc.xref_set_key(xref, k, 'null')
        doc.xref_set_key(xref, 'Width', str(W))
        doc.xref_set_key(xref, 'Height', str(H))
        doc.xref_set_key(xref, 'BitsPerComponent', '8')
        doc.xref_set_key(xref, 'ColorSpace', '/DeviceRGB')
        if len(jpg.getvalue()) < 0.6 * len(flate):
            doc.update_stream(xref, jpg.getvalue(), compress=False)
            doc.xref_set_key(xref, 'Filter', '/DCTDecode')
        else:
            doc.update_stream(xref, raw, compress=True)
        if alpha is None:
            doc.xref_set_key(xref, 'SMask', 'null')
        else:
            for k in ('DecodeParms', 'Decode', 'Matte'):
                doc.xref_set_key(smask, k, 'null')
            doc.xref_set_key(smask, 'Width', str(W))
            doc.xref_set_key(smask, 'Height', str(H))
            doc.xref_set_key(smask, 'BitsPerComponent', '8')
            doc.xref_set_key(smask, 'ColorSpace', '/DeviceGray')
            doc.update_stream(smask, alpha.tobytes(), compress=True)
    _SLIM_CACHE[key] = doc
    return doc


def text_clean_page(doc, page, clip, margin=EDGE_MARGIN):
    """A one-page copy of doc[page] without the text that lies more than margin pt outside clip.
    show_pdf_page embeds the whole source page and only clips it, so journal headers and neighboring
    panels would stay in the text layer, invisible but found by search, copy and similarity checkers."""
    key = (id(doc), page, tuple(round(v, 2) for v in clip))
    if key in _CLEAN_CACHE:
        return _CLEAN_CACHE[key], 0
    out = fitz.open()
    out.insert_pdf(doc, from_page=page, to_page=page)
    pg = out[0]
    R = pg.rect
    c = fitz.Rect(clip)
    bands = [fitz.Rect(R.x0, R.y0, R.x1, c.y0 - margin), fitz.Rect(R.x0, c.y1 + margin, R.x1, R.y1),
             fitz.Rect(R.x0, c.y0 - margin, c.x0 - margin, c.y1 + margin),
             fitz.Rect(c.x1 + margin, c.y0 - margin, R.x1, c.y1 + margin)]
    n = 0
    for b in bands:
        if b.is_empty or b.width <= 0 or b.height <= 0:
            continue
        pg.add_redact_annot(b, fill=False)
        n += 1
    if n:
        pg.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                            text=fitz.PDF_REDACT_TEXT_REMOVE)
    _CLEAN_CACHE[key] = out
    return out, 0


def _ink_bbox_raster(im, thresh=245, pad=0):
    a = np.asarray(im.convert('L'))
    ys, xs = np.where(a < thresh)
    if len(xs) == 0:
        return (0, 0, im.width, im.height)
    return (max(0, xs.min() - pad), max(0, ys.min() - pad),
            min(im.width, xs.max() + 1 + pad), min(im.height, ys.max() + 1 + pad))


class Panel:
    """A rectangular piece of a source figure.

    src: PDF or raster file. clip: (x0, y0, x1, y1) in source units. page: PDF page index.
    masks: rectangles (source units) painted white, for the source's panel letters.
    trim: shrink the clip to the ink. autoletters: find single bold letters a-l (>= 6 pt) in vector sources.
    dpi: the raster's print resolution in the source document (for the audit and fixed scales).
    pad: white margin kept around the ink (default 0.8 pt or 4 px). weight: height factor inside a row.
    scale: fixed scale (pt per source pt; for rasters mm per 100 px). letter: None = next new letter,
    False = never lettered (a color key placed as its own panel), a string = that letter.
    """

    def __init__(self, src, clip=None, page=0, masks=(), trim=True, autoletters=False,
                 dpi=None, pad=None, weight=1.0, scale=None, letter=None):
        self.letter = letter
        self.src = src
        self.page = page
        self.masks = list(masks)
        self.trim = trim
        self.autoletters = autoletters
        self.is_pdf = src.lower().endswith('.pdf')
        self.pad = pad if pad is not None else (0.8 if self.is_pdf else 4)
        self.weight = weight
        self.fixed = scale
        self.found_letters = []
        self.dpi = dpi
        if self.is_pdf:
            self.doc = fitz.open(src)
            pg = self.doc[page]
            self.clip = fitz.Rect(clip) if clip else pg.rect
            if self.autoletters:
                self._find_letters(pg)
            if trim:
                self._trim_pdf(pg)
        else:
            self.im = Image.open(src).convert('RGB')
            c = clip or (0, 0, self.im.width, self.im.height)
            self.clip = fitz.Rect(c)
            if trim:
                self._trim_png()

    def _trim_pdf(self, pg):
        z = 4.0
        pix = pg.get_pixmap(matrix=fitz.Matrix(z, z), clip=self.clip, alpha=False)
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        im = self._apply_masks_img(im, self.clip, z)   # a masked letter must not hold the margin open
        x0, y0, x1, y1 = _ink_bbox_raster(im)
        c = self.clip
        self.clip = fitz.Rect(c.x0 + x0 / z - self.pad, c.y0 + y0 / z - self.pad,
                              c.x0 + x1 / z + self.pad, c.y0 + y1 / z + self.pad)

    def _trim_png(self):
        c = [int(round(v)) for v in self.clip]
        im = self.im.crop(c)
        im = self._apply_masks_img(im, self.clip, 1.0)
        x0, y0, x1, y1 = _ink_bbox_raster(im, thresh=240)
        p = self.pad
        self.clip = fitz.Rect(max(0, c[0] + x0 - p), max(0, c[1] + y0 - p),
                              min(self.im.width, c[0] + x1 + p), min(self.im.height, c[1] + y1 + p))

    def _apply_masks_img(self, im, clip, z):
        dr = ImageDraw.Draw(im)
        for m in self.masks + self.found_letters:
            mx0, my0, mx1, my1 = m
            dr.rectangle([(mx0 - clip.x0) * z, (my0 - clip.y0) * z,
                          (mx1 - clip.x0) * z, (my1 - clip.y0) * z], fill=(255, 255, 255))
        return im

    def _find_letters(self, pg):
        """Single lower-case letters (a-l) set bold, in the clip: panel letters."""
        d = pg.get_text('dict', clip=self.clip)
        for b in d.get('blocks', []):
            for line in b.get('lines', []):
                for s in line.get('spans', []):
                    t = s['text'].strip().rstrip(')').rstrip('.')
                    bold = ('Bold' in s['font'] or 'bold' in s['font'] or s['flags'] & 16)
                    if len(t) == 1 and t in 'abcdefghijkl' and bold and s['size'] >= 6:
                        r = fitz.Rect(s['bbox'])
                        self.found_letters.append((r.x0 - 1, r.y0 - 1, r.x1 + 1, r.y1 + 1))

    @property
    def w(self):
        return self.clip.width

    @property
    def h(self):
        return self.clip.height

    def place(self, out_page, rect, s_slim=None):
        s = rect.width / self.w
        if self.is_pdf:
            # one slimmed copy per source page and figure, at the largest scale it is shown at
            src_doc, src_page = text_clean_page(slim_doc(self.src, self.page, s_slim or s), self.page, self.clip)
            out_page.show_pdf_page(rect, src_doc, src_page, clip=self.clip)
            for m in self.masks + self.found_letters:
                mr = fitz.Rect(m) & self.clip
                if mr.is_empty:
                    continue
                tr = fitz.Rect(rect.x0 + (mr.x0 - self.clip.x0) * s, rect.y0 + (mr.y0 - self.clip.y0) * s,
                               rect.x0 + (mr.x1 - self.clip.x0) * s, rect.y0 + (mr.y1 - self.clip.y0) * s)
                out_page.draw_rect(tr, color=None, fill=(1, 1, 1), overlay=True)
        else:
            c = [int(round(v)) for v in self.clip]
            im = self.im.crop(c)
            im = self._apply_masks_img(im, self.clip, 1.0)
            buf = io.BytesIO()
            im.save(buf, format='PNG', optimize=True)
            out_page.insert_image(rect, stream=buf.getvalue())
        return s

    def audit(self, s):
        """Font sizes after scaling (vector) or effective dpi (raster)."""
        if self.is_pdf:
            sizes = []
            d = self.doc[self.page].get_text('dict', clip=self.clip)
            for b in d.get('blocks', []):
                for line in b.get('lines', []):
                    for sp in line.get('spans', []):
                        if sp['text'].strip():
                            sizes.append(sp['size'] * s)
            if sizes:
                return dict(kind='vector', scale=round(s, 3), font_min=round(min(sizes), 2),
                            font_med=round(statistics.median(sizes), 2), n_text=len(sizes))
            return dict(kind='vector(no text)', scale=round(s, 3))
        width_mm = self.w * s / MM
        dpi = self.w / (width_mm / 25.4)
        res = dict(kind='raster', eff_dpi=round(dpi))
        if self.dpi:
            res['scale_vs_print'] = round(width_mm / (self.w / self.dpi * 25.4), 3)
        return res


class Stack:
    """A column of panels inside a row. Flexible stacks set their panels at a common
    width: in a row of height H the stack is (H - gaps) / sum(h_i/w_i) wide. A stack of
    fixed-scale panels (legends) keeps their sizes and is centered vertically in the row."""

    def __init__(self, panels, gap_mm=3.0):
        self.panels = panels
        self.gap = gap_mm * MM
        self.b = sum(p.h / p.w for p in panels)
        self.g = self.gap * (len(panels) - 1)
        self.fixed = all(getattr(p, 'fixed', None) for p in panels)

    def _fs(self, p):
        k = p.fixed if p.is_pdf else p.fixed * 72 / (p.dpi or 300)
        return p.w * k, p.h * k

    def width_for(self, H):
        if self.fixed:
            return max(self._fs(p)[0] for p in self.panels)
        return (H - self.g) / self.b

    def place(self, x, y, H, layout):
        w = self.width_for(H)
        if self.fixed:
            tot = sum(self._fs(p)[1] for p in self.panels) + self.g
            yy = y + max(0, (H - tot) / 2)
            for p in self.panels:
                pw, ph = self._fs(p)
                layout.append((p, fitz.Rect(x, yy, x + pw, yy + ph)))
                yy += ph + self.gap
            return w
        yy = y
        for p in self.panels:
            ph = w * p.h / p.w
            layout.append((p, fitz.Rect(x, yy, x + w, yy + ph)))
            yy += ph + self.gap
        return w


def redacted(src, name, rects, art=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED, pixels=False, page=0):
    """A one-page copy of src with what lies inside rects removed instead of painted over: characters
    overlapping a rect, vector paths wholly inside it (art=..._IF_COVERED, the default) or touching it
    (_IF_TOUCHED), and, with pixels=True, the pixels of embedded images under it, set to white (letters that
    are part of a raster). Use it when a neighboring panel's label or frame reaches into a crop."""
    os.makedirs(_tmp_dir(), exist_ok=True)
    out = os.path.join(_tmp_dir(), name)
    doc = fitz.open(src)
    if page:
        doc.select([page])
    pg = doc[0]
    for r in rects:
        pg.add_redact_annot(fitz.Rect(r), fill=(1, 1, 1) if pixels else False)
    pg.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS if pixels else fitz.PDF_REDACT_IMAGE_NONE,
                        graphics=art, text=fitz.PDF_REDACT_TEXT_REMOVE)
    doc.save(out, garbage=3, deflate=True)
    return out


def same_scale(*panels):
    """Weights that set the panels of one row at one scale: the tallest gets weight 1, the others their
    height relative to it, so they keep the source's relative sizes."""
    hmax = max(p.h for p in panels)
    for p in panels:
        p.weight = p.h / hmax


def fit_row(items, scale=None, width_mm=None, gap_mm=3.0, letter_pt=8.0):
    """Weights that set every panel of one row, stacked ones included, at one scale s (print pt per source
    unit; rasters must come from one source). s fills the width unless given. The Stack must be the tallest
    item. Returns the row height in mm, to pass as height_mm."""
    width_mm = width_mm or CONFIG['measure']
    LS = letter_pt * 1.2
    sg = max(3.0 * MM, LS + 1.5)

    def unit(p):
        return 1.0 if p.is_pdf else 72.0 / p.dpi

    def w1(p):
        return p.w * unit(p) if isinstance(p, Panel) else max(q.w * unit(q) for q in p.panels)
    if scale is None:
        free = width_mm * MM - gap_mm * MM * (len(items) - 1)
        scale = free / sum(w1(p) for p in items)
    hs = []
    for p in items:
        if isinstance(p, Panel):
            hs.append(scale * p.h * unit(p))
        else:
            w = w1(p) * scale
            hs.append(sum(w * q.h / q.w for q in p.panels) + sg * (len(p.panels) - 1))
    H = max(hs)
    for p, h in zip(items, hs):
        if isinstance(p, Panel):
            p.weight = h / H
    return H / MM


def compose(name, rows, width_mm=None, row_gap_mm=3.0, col_gap_mm=3.0, note='', letters=False, letter_pt=8.0):
    """rows: list of rows; a row is a list of Panel/Stack, or dict(panels=[...], gap=mm,
    height_mm=.., valign='top'|'center').
    letters=True sets new panel letters (a, b, c, ...) in an embedded bold sans above the top-left corner of
    every panel, in layout order (rows top to bottom, panels left to right, stacked panels top to bottom);
    room is reserved above each row and between stacked panels. The source's own letters must be masked."""
    os.makedirs(CONFIG['out'], exist_ok=True)
    os.makedirs(_prev_dir(), exist_ok=True)
    width_mm = width_mm or CONFIG['measure']
    W = width_mm * MM
    LS = letter_pt * 1.2 if letters else 0.0
    if letters:
        for row in rows:
            for q in (row['panels'] if isinstance(row, dict) else row):
                if isinstance(q, Stack):
                    q.gap = max(q.gap, LS + 1.5)
                    q.g = q.gap * (len(q.panels) - 1)
    layout = []
    y = 0.0

    def fixed_size(p):
        k = p.fixed if p.is_pdf else p.fixed * 72 / (p.dpi or 300)
        return p.w * k, p.h * k
    for row in rows:
        y += LS
        opts = {}
        if isinstance(row, dict):
            opts = row
            row = row['panels']
        gap = opts.get('gap', col_gap_mm) * MM
        flex = [p for p in row if not getattr(p, 'fixed', None)]
        Fw = sum(fixed_size(p)[0] for p in row if isinstance(p, Panel) and p.fixed) + \
            sum(p.width_for(0) for p in row if isinstance(p, Stack) and p.fixed)
        A = sum(p.w * p.weight / p.h for p in flex if isinstance(p, Panel))
        Bi = sum(1 / s.b for s in flex if isinstance(s, Stack))
        Gs = sum(s.g / s.b for s in flex if isinstance(s, Stack))
        if A + Bi > 0:
            H = (W - Fw - gap * (len(row) - 1) + Gs) / (A + Bi)
        else:   # a row of fixed panels only: its height is the tallest panel
            H = max(fixed_size(p)[1] if isinstance(p, Panel) else
                    sum(p._fs(q)[1] for q in p.panels) + p.g for p in row)
        if 'height_mm' in opts:  # a row may be capped and centered (never so far that text shrinks)
            H = min(H, opts['height_mm'] * MM)
        widths = []
        for p in row:
            if isinstance(p, Panel) and p.fixed:
                widths.append(fixed_size(p)[0])
            elif isinstance(p, Panel):
                widths.append(p.w * p.weight * H / p.h)
            else:
                widths.append(p.width_for(H))
        total_w = sum(widths) + gap * (len(row) - 1)
        x = (W - total_w) / 2
        valign = opts.get('valign', 'top')
        row_h = H
        for p, pw in zip(row, widths):
            if isinstance(p, Stack):
                p.place(x, y, H, layout)
            elif p.fixed:
                ph = fixed_size(p)[1]
                yy = y if valign == 'top' else y + (H - ph) / 2
                layout.append((p, fitz.Rect(x, yy, x + pw, yy + ph)))
                row_h = max(row_h, ph)
            else:
                ph = H * p.weight
                yy = y if valign == 'top' else y + (H - ph) / 2
                layout.append((p, fitz.Rect(x, yy, x + pw, yy + ph)))
            x += pw + gap
        y += row_h + row_gap_mm * MM
    Hout = y - row_gap_mm * MM
    doc = fitz.open()
    pg = doc.new_page(width=W, height=Hout)
    audits = []
    smax = {}
    for p, r in layout:
        if p.is_pdf:
            k = (p.src, p.page)
            smax[k] = max(smax.get(k, 0), r.width / p.w)
    for p, r in layout:
        s = p.place(pg, r, smax.get((p.src, p.page)))
        a = p.audit(s)
        a['src'] = os.path.basename(p.src)
        a['w_mm'] = round(r.width / MM, 1)
        a['letters_masked'] = len(p.found_letters) + len(p.masks)
        audits.append(a)
    if letters:
        font = _letter_font()
        if font is None:
            print(f'WARN {name}: no bold TrueType font found; letters use the base-14 Helvetica-Bold, '
                  'which is not embedded. Pass --letter-font.', file=sys.stderr)
        k = 0
        for p, r in layout:
            if p.letter is False:
                continue
            ch = p.letter if isinstance(p.letter, str) else 'abcdefghijklmnopqrstuvwxyz'[k]
            k += 1
            if font:
                pg.insert_text((r.x0, r.y0 - 0.25 * letter_pt), ch, fontname='LetterBold', fontfile=font,
                               fontsize=letter_pt, color=(0, 0, 0))
            else:
                pg.insert_text((r.x0, r.y0 - 0.25 * letter_pt), ch, fontname='hebo', fontsize=letter_pt,
                               color=(0, 0, 0))
    out = os.path.join(CONFIG['out'], name + '.pdf')
    doc.save(out, garbage=4, deflate=True)
    strip_invisible.main(out, out + '.tmp.pdf')
    os.replace(out + '.tmp.pdf', out)
    pix = fitz.open(out)[0].get_pixmap(dpi=150)
    pix.save(os.path.join(_prev_dir(), name + '.png'))
    small = [a for a in audits if a.get('font_min') is not None and a['font_min'] < CONFIG['min_font']]
    rep = dict(name=name, size_mm=[round(W / MM, 1), round(Hout / MM, 1)], panels=audits, note=note,
               small_text=len(small))
    print(json.dumps(rep))
    for a in audits:
        if a.get('scale_vs_print', 0) > 1.05:
            print(f"WARN {name}: {a['src']} is shown {a['scale_vs_print']}x larger than it printed in its source "
                  f"({a['eff_dpi']} dpi effective); look for the publisher's full-resolution or vector figure",
                  file=sys.stderr)
    for a in small:
        print(f"WARN {name}: {a['src']} prints text at {a['font_min']} pt (< {CONFIG['min_font']} pt); "
              'widen the row, split the figure into two upright floats, or crop fewer panels per row',
              file=sys.stderr)
    return rep


def load_spec(path):
    # The spec does `from compose_crops import ...`; when this file runs as a script it is __main__, so register it
    # under its module name, or the spec would import a second copy with its own CONFIG.
    sys.modules.setdefault('compose_crops', sys.modules[__name__])
    spec = importlib.util.spec_from_file_location('figure_spec', os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec.loader.exec_module(mod)
    if not hasattr(mod, 'FIGURES'):
        raise SystemExit(f'FAILED: {path} defines no FIGURES = {{name: function}}')
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('names', nargs='*', help='figures to build (default: all in the spec)')
    ap.add_argument('--spec', required=True, help='Python spec file defining FIGURES')
    ap.add_argument('--out', default='figures', help='output folder for name.pdf and _preview/name.png')
    ap.add_argument('--measure', type=float, default=150.0, help='text width in mm (default 150)')
    ap.add_argument('--letter-font', help='bold TTF for the new panel letters (default: Arial Bold or a clone)')
    ap.add_argument('--min-font', type=float, default=5.5, help='warn below this printed text size in pt')
    ap.add_argument('--report', help='write all audits to this JSON file')
    ap.add_argument('--strict', action='store_true', help='exit 1 when any panel prints text below --min-font')
    a = ap.parse_args()
    configure(out=a.out, measure=a.measure, letter_font=a.letter_font, min_font=a.min_font)
    mod = load_spec(a.spec)
    unknown = [n for n in a.names if n not in mod.FIGURES]
    if unknown:
        raise SystemExit(f'FAILED: not in the spec: {", ".join(unknown)}')
    reps = [f() for n, f in mod.FIGURES.items() if not a.names or n in a.names]
    if a.report:
        with open(a.report, 'w') as fh:
            json.dump(reps, fh, indent=1)
    n_small = sum(r['small_text'] for r in reps)
    print(f'composed {len(reps)} figure(s) into {CONFIG["out"]}; panels below {CONFIG["min_font"]} pt: {n_small}')
    return 1 if (a.strict and n_small) else 0


if __name__ == '__main__':
    sys.exit(main())

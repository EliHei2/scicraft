#!/usr/bin/env python3
"""Recolour a paper figure that must stay an image for a dark page: the white ground removed, the ink made light.

    python3 darken_figure.py IN.pdf OUT.png [--width 2400] [--page 1]
    python3 darken_figure.py IN.svg OUT.svg                       # an SVG written by `pdftocairo -svg`
    python3 darken_figure.py IN.pdf --extract-images DIR          # the embedded images, untouched, with their alpha

Use it for schematics only. A data picture inside a figure (a rendered sample, a micrograph, a heat map tile) is
never recoloured: take it out of the PDF with --extract-images and place the original. The first version of this
pass recoloured one pale data tile wrongly, which is why the extraction exists. Prefer drawing figures natively
from the records; this is the fallback for a schematic that cannot be redrawn.

One colour rule in OKLab, for vector and raster alike:
  * neutral and pastel colours (chroma < .09) have their lightness inverted between the page ground and a light ink
    (L' = INK_L - (INK_L - BG_L) * L, INK_L .93), chroma times 1.15, hue kept: black text turns light, white turns
    into the ground, pastel boxes turn into deep tints of the same hue;
  * saturated colours keep their hue; one darker than L .55 is lifted to .55 + (.55 - L) * .5 so it reads;
  * pure white becomes exactly the ground, and the PNG is transparent there;
  * --override OLD=NEW maps a named colour (the method's own colour in the paper) to its page colour.
Raster: page 1 is rendered with alpha (PyMuPDF samples are premultiplied, so they are un-premultiplied first). An
embedded image whose border ring is dark or see-through is kept exactly; an opaque image on a light ground is
recoloured like the page. Vector: every rgb(x%,y%,z%) is recoloured, except inside <mask>, and a white fill on a
glyph group (text set on a coloured box) stays white.

After running it, look at every figure on the page ground. Then decide which tiles must be extracted originals.

Needs numpy; PyMuPDF (`pip install pymupdf`) for PDF input; Pillow for PNG output. Exit 1 on bad input.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np

INK_L = .93


def _lin(c):
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def _gam(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= .0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - .055)


def oklab(rgb):
    r, g, b = np.moveaxis(_lin(np.asarray(rgb, np.float64)), -1, 0)
    l = np.cbrt(.4122214708 * r + .5363325363 * g + .0514459929 * b)
    m = np.cbrt(.2119034982 * r + .6806995451 * g + .1073969566 * b)
    s = np.cbrt(.0883024619 * r + .2817188376 * g + .6299787005 * b)
    return np.stack([.2104542553 * l + .7936177850 * m - .0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + .4505937099 * s,
                     .0259040371 * l + .7827717662 * m - .8086757660 * s], -1)


def from_oklab(lab):
    L, a, b = np.moveaxis(lab, -1, 0)
    l = (L + .3963377774 * a + .2158037573 * b) ** 3
    m = (L - .1055613458 * a - .0638541728 * b) ** 3
    s = (L - .0894841775 * a - 1.2914855480 * b) ** 3
    return _gam(np.stack([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s,
                          -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                          -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], -1))


class Palette:
    def __init__(self, ground: str, ink_l: float, overrides: dict):
        self.ground = np.array([int(ground[i:i + 2], 16) for i in (0, 2, 4)], np.float64) / 255
        self.bg_l = float(oklab(self.ground)[0])
        self.ink_l = ink_l
        self.overrides = overrides                      # {(r, g, b) 0-255: (r, g, b) 0-255}

    def remap(self, rgb):
        """sRGB in [0, 1], any leading shape -> the dark-ground colour, same shape."""
        lab = oklab(rgb)
        L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
        soft = np.hypot(a, b) < .09
        L2 = np.where(soft, self.ink_l - (self.ink_l - self.bg_l) * L, np.where(L < .55, .55 + (.55 - L) * .5, L))
        k = np.where(soft, 1.15, 1.0)                   # pastels keep their hue visible once they are deep tints
        out = from_oklab(np.stack([L2, a * k, b * k], -1))
        white = np.all(np.asarray(rgb) > .995, -1)      # pure white is exactly the ground, so a figure's page vanishes
        out[white] = self.ground
        return out


# ------------------------------------------------------------------------------------------------- vector
_RGB = re.compile(r'rgb\(\s*([\d.]+)%\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*\)')


def darken_svg(text: str, pal: Palette) -> str:
    cache = {}

    def col(m, keep_white=False):
        rgb = tuple(float(v) / 100 for v in m.groups())
        key = (rgb, keep_white)
        if key not in cache:
            q = tuple(int(round(v * 255)) for v in rgb)
            if q in pal.overrides:
                cache[key] = '#%02x%02x%02x' % pal.overrides[q]
            elif keep_white and min(q) >= 250:
                cache[key] = '#ffffff'
            else:
                cache[key] = '#%02x%02x%02x' % tuple(int(round(v * 255)) for v in pal.remap(np.array(rgb)))
        return cache[key]

    out, depth, last = [], 0, 0
    tags = list(re.finditer(r'<[^>]+>', text))
    for i, t in enumerate(tags):
        out.append(text[last:t.start()])
        s = t.group(0)
        if s.startswith('<mask'):
            depth += 1
        elif s.startswith('</mask'):
            depth -= 1
        if depth == 0 and 'rgb(' in s:
            glyphs = s.startswith('<g') and i + 1 < len(tags) and tags[i + 1].group(0).startswith('<use xlink:href="#glyph')
            s = _RGB.sub(lambda m: col(m, keep_white=glyphs), s)
        out.append(s)
        last = t.end()
    out.append(text[last:])
    return ''.join(out)


# ------------------------------------------------------------------------------------------------- raster
def darken_pdf(pdf: Path, width: int, page_no: int, pal: Palette):
    """Render one page of a PDF at `width` px and recolour it; returns an RGBA uint8 array and the kept-image count."""
    import fitz
    doc = fitz.open(str(pdf))
    page = doc[page_no - 1]
    zoom = width / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)          # transparent page, premultiplied samples
    px = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 4).astype(np.float64) / 255
    a0 = px[..., 3]
    img = np.where(a0[..., None] > 0, px[..., :3] / np.maximum(a0, 1e-9)[..., None], 1.0).clip(0, 1)
    keep = np.zeros(img.shape[:2], bool)
    kept = 0
    for info in page.get_image_info():
        x0, y0, x1, y1 = (int(round(v * zoom)) for v in info['bbox'])
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, img.shape[1]), min(y1, img.shape[0])
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        box, ba = img[y0:y1, x0:x1], a0[y0:y1, x0:x1]
        ring = np.concatenate([v.reshape(-1, 3) for v in (box[:2], box[-2:], box[:, :2], box[:, -2:])])
        ra = np.concatenate([v.reshape(-1) for v in (ba[:2], ba[-2:], ba[:, :2], ba[:, -2:])])
        # a data tile (dark ground, or see-through and made to sit on any ground) is kept exactly, with whatever the
        # figure draws over it; an opaque image on a light ground is recoloured like the page
        if (ra > .5).mean() < .5 or np.median(ring[ra > .5].mean(1)) < .6:
            keep[y0:y1, x0:x1] = True
            kept += 1
    out = img.copy()
    flat = out.reshape(-1, 3)
    sel = ~keep.reshape(-1) & (a0.reshape(-1) > 0)
    q = np.round(flat[sel] * 255).astype(np.int32)                             # colours repeat: remap the distinct ones
    code = (q[:, 0] << 16) | (q[:, 1] << 8) | q[:, 2]
    uniq, inv = np.unique(code, return_inverse=True)
    u = np.stack([(uniq >> 16) & 255, (uniq >> 8) & 255, uniq & 255], 1)
    mapped = pal.remap(u / 255)
    for src, dst in pal.overrides.items():
        hit = np.all(np.abs(u - np.array(src)) <= 6, 1)
        mapped[hit] = np.array(dst) / 255
    flat[sel] = mapped[inv.reshape(-1)]
    out = flat.reshape(img.shape)
    alpha = a0 * np.where(keep, 1.0, np.clip(np.abs(out - pal.ground).max(-1) * 255 / 5, 0, 1))
    return np.dstack([np.round(out * 255), np.round(alpha * 255)]).astype(np.uint8), kept


def extract_images(pdf: Path, page_no: int, out: Path) -> int:
    """Every image placed on the page, as stored in the PDF, with its soft mask (SMask) as alpha."""
    import fitz
    doc = fitz.open(str(pdf))
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for k, item in enumerate(doc[page_no - 1].get_images(full=True)):
        xref, smask = item[0], item[1]
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:                                               # CMYK to RGB
            pix = fitz.Pixmap(fitz.csRGB, pix)
        if smask:
            pix = fitz.Pixmap(pix, fitz.Pixmap(doc, smask))
        f = out / f'image_{k + 1:02d}_xref{xref}.png'
        pix.save(str(f))
        print(f'{f}  {pix.width} x {pix.height}{", with alpha" if pix.alpha else ""}')
        n += 1
    return n


def hexpair(s: str):
    a, b = s.split('=')
    rgb = lambda h: tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))  # noqa: E731
    return rgb(a), rgb(b)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='\n'.join(__doc__.split('\n')[1:]))
    ap.add_argument('src', type=Path, help='a PDF (one figure per page) or an SVG from pdftocairo -svg')
    ap.add_argument('out', type=Path, nargs='?', help='PNG for PDF input, SVG for SVG input')
    ap.add_argument('--width', type=int, default=2400, help='raster width in px (default 2400: twice a 1200 px slot)')
    ap.add_argument('--page', type=int, default=1, help='page of the PDF (default 1)')
    ap.add_argument('--ground', default='141416', help='page ground as hex (default 141416)')
    ap.add_argument('--ink-l', type=float, default=INK_L, help=f'OKLab lightness of the ink (default {INK_L})')
    ap.add_argument('--override', action='append', default=[], metavar='OLD=NEW',
                    help='map one colour to another, e.g. 0A3D66=8EC9FF (repeatable)')
    ap.add_argument('--extract-images', type=Path, metavar='DIR', help='write the embedded images of the page, untouched')
    a = ap.parse_args()
    if not a.src.exists():
        sys.exit(f'no such file: {a.src}')
    pal = Palette(a.ground.lstrip('#'), a.ink_l, dict(hexpair(o) for o in a.override))
    if a.extract_images:
        n = extract_images(a.src, a.page, a.extract_images)
        print(f'{n} embedded image(s) written to {a.extract_images}')
        if not a.out:
            return
    if not a.out:
        sys.exit('give an output file, or --extract-images DIR')
    if a.src.suffix.lower() == '.svg':
        a.out.write_text(darken_svg(a.src.read_text(), pal))
        print(f'{a.out}: recoloured SVG')
    elif a.src.suffix.lower() == '.pdf':
        from PIL import Image
        rgba, kept = darken_pdf(a.src, a.width, a.page, pal)
        Image.fromarray(rgba, 'RGBA').save(a.out)
        clear = float((rgba[..., 3] == 0).mean())
        print(f'{a.out}: {rgba.shape[1]} x {rgba.shape[0]} px, {clear:.0%} transparent, {kept} embedded image(s) kept as they are')
    else:
        sys.exit('input must be .pdf or .svg')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Compose a figure from true-size vector panel PDFs at exact mm, then stamp the panel letters last.

The layout file is the one geometry source for the mock-up and the composed figure:

    {"width_mm": 183, "height_mm": 120, "letter_pt": 8, "out": "figure_2",
     "panels": [{"pdf": "panels/a_heatmap.pdf", "x": 0, "y": 0, "w": 92, "h": 44, "letter": "a"},
                {"pdf": "panels/b_scatter.pdf", "x": 93.5, "y": 0, "w": 46, "h": 44, "letter": "b",
                 "lx": 93.8, "ly": 4.2}]}

x, y are the panel's top-left in mm; w, h its box (needed for --mockup, checked against the PDF otherwise).
Letters default to (x + 0.3, y + 4.2) mm, the baseline of a panel title drawn with figstyle.title().
Paths are relative to the layout file.

Usage:
    python3 compose.py layout.json                 # out.pdf + out.png (600 dpi) + out.svg (live text)
    python3 compose.py layout.json --mockup        # labeled boxes only: settle the grid before drawing data
    python3 compose.py layout.json --png-dpi 320 --no-svg

Panels are placed at native size (keep_proportion, never stretched). The PDF and PNG keep a transparent ground. A panel whose PDF size differs from its
box by more than --tol mm, a panel that runs off the page, or a missing panel is reported, and the run exits 1.
Needs PyMuPDF (`pip install pymupdf`); fontTools is used to pull Helvetica Neue Bold out of the macOS .ttc.
Adapted from the author's rebuttal composer and figure-utility composer helpers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.exit("compose.py needs PyMuPDF: pip install pymupdf")

MM_PT = 72.0 / 25.4
INK = (0.067, 0.067, 0.067)
TTC = ("/System/Library/Fonts/HelveticaNeue.ttc", "/Library/Fonts/HelveticaNeue.ttc")
CACHE = Path.home() / ".cache" / "figstyle" / "HelveticaNeue-Bold.ttf"


def rect(x, y, w, h) -> "fitz.Rect":
    return fitz.Rect(x * MM_PT, y * MM_PT, (x + w) * MM_PT, (y + h) * MM_PT)


def bold_face(user_font: str | None) -> str | None:
    """A bold font file for the letters: --letter-font, else Helvetica Neue Bold extracted from the .ttc."""
    if user_font:
        return user_font
    if CACHE.is_file():
        return str(CACHE)
    try:
        from fontTools.ttLib import TTCollection
        for p in TTC:
            if Path(p).is_file():
                face = next(f for f in TTCollection(p).fonts if f["name"].getDebugName(6) == "HelveticaNeue-Bold")
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                face.save(str(CACHE))
                return str(CACHE)
    except Exception:
        pass
    return None


def letters(page, items, size: float, font_file: str | None) -> None:
    """Letters last, so an opaque panel never paints over them. Without a bold file, use the built-in Helvetica-Bold."""
    name = "hebo"
    if font_file:
        page.insert_font(fontname="LB", fontfile=font_file)
        name = "LB"
    for p in items:
        if p.get("letter"):
            lx, ly = p.get("lx", p["x"] + 0.3), p.get("ly", p["y"] + 4.2)
            page.insert_text((lx * MM_PT, ly * MM_PT), p["letter"], fontname=name, fontsize=size, color=INK)


_FAMILY = {"HelveticaNeue": ("Helvetica Neue", None), "HelveticaNeue-Bold": ("Helvetica Neue", "bold"),
           "HelveticaNeue-Light": ("Helvetica Neue", "300"), "HelveticaNeue-Medium": ("Helvetica Neue", "500"),
           "Helvetica": ("Helvetica", None), "Helvetica-Bold": ("Helvetica", "bold"), "ArialMT": ("Arial", None),
           "Arial-BoldMT": ("Arial", "bold"), "DejaVuSans": ("DejaVu Sans", None), "cmss10": ("cmss10", None)}
_TAG = re.compile(r"<text\b[^>]*>")
_FONT = re.compile(r'\sfont-family="(?:[A-Z]{6}\+)?([^"]+)"')
_WEIGHT = re.compile(r'\sfont-weight="([^"]*)"')
_XLIST = re.compile(r'(<tspan\b[^>]*?\bx=")(-?[0-9.]+(?:e-?[0-9]+)?)(?:\s+-?[0-9.]+(?:e-?[0-9]+)?)+(")')


def _tag(m):
    tag = m.group(0)
    f = _FONT.search(tag)
    if not f:
        return tag
    fam, weight = _FAMILY.get(f.group(1), (f.group(1), None))
    w = _WEIGHT.search(tag)
    weight = weight or (w.group(1) if w else None)
    tag = _WEIGHT.sub("", _FONT.sub(f' font-family="{fam}"', tag))
    return tag[:-1] + (f' font-weight="{weight}"' if weight else "") + ">"


def pdf_to_svg(pdf: Path, svg: Path) -> int:
    """SVG with live text: subset prefixes dropped, installed family and weight named, one start x per run so a
    resized run reflows in Illustrator or Inkscape. pdftocairo -svg outlines every glyph; do not use it."""
    s = fitz.open(str(pdf))[0].get_svg_image(text_as_path=False)
    s = _XLIST.sub(r"\1\2\3", _TAG.sub(_tag, s))
    svg.write_text(s)
    return s.count("<text")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("layout", type=Path, help="layout JSON (see the module docstring)")
    ap.add_argument("--out", help="output stem, relative to the layout file (default: the layout's 'out')")
    ap.add_argument("--mockup", action="store_true", help="draw labeled boxes instead of panels")
    ap.add_argument("--png-dpi", type=int, default=600)
    ap.add_argument("--no-svg", action="store_true")
    ap.add_argument("--letter-font", help="bold font file for the panel letters (match the host document)")
    ap.add_argument("--tol", type=float, default=0.2, help="mm a panel PDF may differ from its box (default 0.2)")
    a = ap.parse_args()
    L = json.loads(a.layout.read_text())
    base = a.layout.resolve().parent
    W, H = float(L["width_mm"]), float(L["height_mm"])
    size = float(L.get("letter_pt", 8.0))
    stem = base / ((a.out or L.get("out", "figure")) + ("_mockup" if a.mockup else ""))
    doc = fitz.open()
    page = doc.new_page(width=W * MM_PT, height=H * MM_PT)
    problems = []
    for p in L["panels"]:
        x, y = float(p["x"]), float(p["y"])
        if a.mockup:
            w, h = float(p["w"]), float(p["h"])
            page.draw_rect(rect(x, y, w, h), color=(0.227, 0.227, 0.227), fill=(0.91, 0.933, 0.965), width=0.6)
            label = f"{p.get('letter', '')}  {Path(p['pdf']).stem}  {w:g} x {h:g} mm"
            page.insert_text(((x + 1.5) * MM_PT, (y + h / 2) * MM_PT), label, fontname="helv", fontsize=7, color=INK)
        else:
            src = base / p["pdf"]
            if not src.is_file():
                problems.append(f"missing panel: {p['pdf']}")
                continue
            r = fitz.open(src)[0].rect
            w, h = r.width / MM_PT, r.height / MM_PT
            if "w" in p and (abs(w - p["w"]) > a.tol or abs(h - p["h"]) > a.tol):
                problems.append(f"{p['pdf']} is {w:.2f} x {h:.2f} mm, its box is {p['w']} x {p['h']} mm: "
                                "draw the panel at its box size, never rescale here")
            page.show_pdf_page(rect(x, y, w, h), fitz.open(src), 0, keep_proportion=True)
        if x < -1e-6 or y < -1e-6 or x + w > W + a.tol or y + h > H + a.tol:
            problems.append(f"{p['pdf']} runs off the {W} x {H} mm page")
    letters(page, L["panels"], size, bold_face(a.letter_font))
    stem.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(stem.with_suffix(".pdf")), garbage=4, deflate=True)
    # transparent ground (prints as white); the mock-up stays opaque
    page.get_pixmap(dpi=a.png_dpi, alpha=not a.mockup).save(str(stem.with_suffix(".png")))
    msg = f"wrote {stem}.pdf and .png ({W} x {H} mm, letters {size} pt)"
    if not a.no_svg and not a.mockup:
        n = pdf_to_svg(stem.with_suffix(".pdf"), stem.with_suffix(".svg"))
        msg += f" and .svg ({n} live text elements)"
    print(msg)
    for pr in problems:
        print("PROBLEM", pr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

"""Repaint one label in a raster figure that has no source, and prove nothing else changed.

Use it when a published figure exists only as a raster composite inside a manuscript file and
a label must change (a metric renamed across the paper). The script erases each given label box
to white, draws the new text into it (horizontal or rotated 90 degrees for a
y-axis label), writes PNG and PDF under a new name, and counts changed pixels. It exits 1 if a
box holds colored pixels (it covers data, not only a gray label) or if any changed pixel lies
outside the boxes.

Input: a byte copy of the document's image (never the only copy). Boxes are measured once from
the image and passed as arguments, so the repaint is reproducible.

    python repaint_label.py figure_3.png --out figure_3_relabel \
        --box 40,500,58,700 --box 560,500,578,700 \
        --text "Held-out" --text "Validation loss" --match-text "Validation loss" \
        --pitch-px 24 \
        --rotate 90 --font /path/to/font.ttf --width-mm 183

    python repaint_label.py --self-test

Needs numpy and Pillow. Runs on Python 3.9 or later.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SUPERSAMPLE = 8


def load_font(path: str | None, size_px: int) -> ImageFont.ImageFont:
    if path:
        return ImageFont.truetype(path, max(1, size_px), index=0)
    try:
        return ImageFont.truetype("DejaVuSans.ttf", max(1, size_px))
    except OSError:
        return ImageFont.load_default()


def font_px_for(text: str, length_px: int, font_path: str | None) -> float:
    """Font size at which `text` spans `length_px` of ink along its reading direction."""
    probe = load_font(font_path, 1000)
    x0, _, x1, _ = probe.getbbox(text)
    if x1 <= x0:
        return float(length_px)
    return 1000.0 * length_px / (x1 - x0)


def coverage(text: str, font_px: float, font_path: str | None, rotate: int) -> np.ndarray:
    """Antialiased coverage (0..1) of `text`, cropped to its ink, optionally rotated."""
    font = load_font(font_path, int(round(font_px * SUPERSAMPLE)))
    x0, y0, x1, y1 = font.getbbox(text)
    canvas = Image.new("L", (x1 - x0 + 8, y1 - y0 + 8), 0)
    ImageDraw.Draw(canvas).text((4 - x0, 4 - y0), text, fill=255, font=font)
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)
    if rotate:
        canvas = canvas.rotate(rotate, expand=True)
    w, h = canvas.size
    canvas = canvas.resize((max(1, round(w / SUPERSAMPLE)), max(1, round(h / SUPERSAMPLE))),
                           Image.LANCZOS)
    return np.asarray(canvas, dtype=float) / 255.0


def repaint(src: np.ndarray, boxes, lines, font_path, rotate, pitch_px, pad, ink=None,
            match_text=None):
    """Return (repainted image, font size). Lines stack across the reading direction."""
    out = src.copy()
    x0, y0, x1, y1 = boxes[0]
    span = (y1 - y0 + 1) if rotate else (x1 - x0 + 1)
    font_px = font_px_for(match_text or max(lines, key=len), span, font_path)
    if ink is None:
        ink = src[y0:y1 + 1, x0:x1 + 1].reshape(-1, src.shape[2]).min(axis=0).astype(float)
    bg = np.array([255, 255, 255], dtype=float)
    covs = [coverage(t, font_px, font_path, rotate) for t in lines]
    n = len(lines)
    for bx0, by0, bx1, by1 in boxes:
        out[by0 - pad:by1 + pad + 1, bx0 - pad:bx1 + pad + 1] = bg.astype(np.uint8)
        cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
        for i, cov in enumerate(covs):
            h, w = cov.shape
            shift = (i - (n - 1)) * pitch_px  # last line sits where the old label was
            if rotate:
                left = int(round(cx - w / 2.0 + shift))
                top = int(round(cy - h / 2.0))
            else:
                left = int(round(cx - w / 2.0))
                top = int(round(cy - h / 2.0 + shift))
            top, left = max(0, top), max(0, left)
            h = min(h, out.shape[0] - top)
            w = min(w, out.shape[1] - left)
            c = cov[:h, :w, None]
            region = out[top:top + h, left:left + w].astype(float)
            out[top:top + h, left:left + w] = np.round(region * (1 - c) + ink * c).astype(np.uint8)
    return out, font_px


def outside_count(src, out, boxes, margin):
    """Changed pixels total and changed pixels outside the (padded) boxes."""
    changed = np.any(src != out, axis=2)
    allowed = np.zeros_like(changed)
    for x0, y0, x1, y1 in boxes:
        allowed[max(0, y0 - margin):y1 + margin + 1, max(0, x0 - margin):x1 + margin + 1] = True
    return int(changed.sum()), int((changed & ~allowed).sum())


def colored_in_boxes(src, boxes, min_chroma=60):
    """Pixels inside the boxes whose chroma marks them as data, not gray label ink."""
    n = 0
    for x0, y0, x1, y1 in boxes:
        reg = src[y0:y1 + 1, x0:x1 + 1].astype(int)
        n += int(((reg.max(axis=2) - reg.min(axis=2)) >= min_chroma).sum())
    return n


def write_outputs(out: np.ndarray, stem: Path, width_mm: float) -> None:
    img = Image.fromarray(out)
    img.save(stem.with_suffix(".png"), optimize=True)
    dpi = out.shape[1] / (width_mm / 25.4)
    img.convert("RGB").save(stem.with_suffix(".pdf"), resolution=dpi)


def parse_box(s: str):
    parts = [int(v) for v in s.split(",")]
    if len(parts) != 4 or parts[2] < parts[0] or parts[3] < parts[1]:
        raise argparse.ArgumentTypeError("box must be x0,y0,x1,y1 with x1>=x0 and y1>=y0")
    return tuple(parts)


def self_test() -> int:
    rng = np.random.default_rng(0)
    img = np.full((300, 400, 3), 255, dtype=np.uint8)
    img[200:290, 100:390] = rng.integers(0, 255, (90, 290, 3), dtype=np.uint8)  # "data"
    pil = Image.fromarray(img)
    d = ImageDraw.Draw(pil)
    d.text((20, 60), "Old label", fill=(30, 30, 30), font=load_font(None, 14))
    img = np.asarray(pil).copy()
    ys, xs = np.where(np.any(img[40:100, 10:150] < 200, axis=2))
    box = (10 + xs.min(), 40 + ys.min(), 10 + xs.max(), 40 + ys.max())
    out, _ = repaint(img, [box], ["New label"], None, 0, 0, 2, match_text="Old label")
    total, outside = outside_count(img, out, [box], margin=4)
    assert total > 0, "nothing was repainted"
    assert outside == 0, f"{outside} pixels changed outside the box"
    assert np.array_equal(img[200:290, 100:390], out[200:290, 100:390]), "data region changed"
    with tempfile.TemporaryDirectory() as tmp:
        stem = Path(tmp) / "t"
        write_outputs(out, stem, 89.0)
        assert stem.with_suffix(".png").exists() and stem.with_suffix(".pdf").exists()
    print(f"self-test passed: {total} pixels changed, 0 outside the box, data region identical")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("image", nargs="?", help="byte copy of the figure image (PNG)")
    ap.add_argument("--out", help="output stem; writes <stem>.png and <stem>.pdf")
    ap.add_argument("--box", action="append", type=parse_box, default=[],
                    help="x0,y0,x1,y1 ink box of one old label, in pixels; repeat per label")
    ap.add_argument("--text", action="append", default=[],
                    help="one line of the new label; repeat for two lines")
    ap.add_argument("--match-text", help="old label text; sets the font size so its ink spans "
                    "the box (default: the longest new line)")
    ap.add_argument("--font", help="TrueType or .ttc font file matching the figure")
    ap.add_argument("--rotate", type=int, choices=(0, 90), default=0,
                    help="90 for a y-axis label read bottom to top")
    ap.add_argument("--pitch-px", type=float, default=0.0,
                    help="line pitch in pixels for a multi-line label")
    ap.add_argument("--pad", type=int, default=3, help="extra pixels erased around each box")
    ap.add_argument("--margin", type=int, default=None,
                    help="tolerance for changed pixels around a box (default: pad + pitch)")
    ap.add_argument("--width-mm", type=float, default=183.0,
                    help="printed width of the figure for the PDF page")
    ap.add_argument("--allow-color", action="store_true",
                    help="allow colored pixels inside a box (a colored label)")
    ap.add_argument("--self-test", action="store_true", help="run on a synthetic image")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not (a.image and a.out and a.box and a.text):
        ap.error("image, --out, at least one --box and one --text are required")
    src = np.asarray(Image.open(a.image).convert("RGB"), dtype=np.uint8)
    colored = colored_in_boxes(src, a.box)
    if colored and not a.allow_color:
        print(f"FAIL: {colored} colored pixels inside the label boxes; a box covers data, not "
              "only the label. Re-measure the boxes, or pass --allow-color for a colored label.")
        return 1
    out, font_px = repaint(src, a.box, a.text, a.font, a.rotate, a.pitch_px, a.pad,
                           match_text=a.match_text)
    margin = a.margin if a.margin is not None else a.pad + int(np.ceil(a.pitch_px * (len(a.text) - 1)))
    total, outside = outside_count(src, out, a.box, margin)
    stem = Path(a.out)
    stem.parent.mkdir(parents=True, exist_ok=True)
    write_outputs(out, stem, a.width_mm)
    print(f"font {font_px:.1f} px; {total} pixels changed; {outside} outside the boxes "
          f"(margin {margin} px)")
    print(f"wrote {stem.with_suffix('.png')} and {stem.with_suffix('.pdf')}")
    if outside:
        print("FAIL: pixels changed outside the label boxes; check the boxes and the pitch")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

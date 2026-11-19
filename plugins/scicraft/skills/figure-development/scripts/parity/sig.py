"""Output signatures for render-parity checks.

Two signals per output file:
  * exact sha256 of the bytes, which detects a truly identical re-render;
  * a small grayscale "perceptual" grid (the page rasterized, downscaled), a
    continuous distance that survives non-deterministic PDF/PNG metadata
    (embedded dates, font-subset ids), so "visually identical" reads as a
    near-zero distance instead of a false diff.

PDF page geometry (width and height in points) is recorded exactly, because a
composer places panels at fixed mm and depends on the page size being unchanged.

Dependencies: numpy, Pillow; PyMuPDF (`pip install pymupdf`) for PDF outputs.
Imported by render_all.py and compare.py; not run on its own.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image

PERCEPTUAL_PX = 96  # edge of the downscaled grayscale grid
PDF_RASTER_DPI = 110  # rasterization dpi for the perceptual PDF signal


def _pymupdf():
    try:
        import pymupdf  # PyMuPDF >= 1.24
    except ImportError:  # older releases only ship the `fitz` name
        import fitz as pymupdf
    return pymupdf


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _to_grid(img: Image.Image) -> np.ndarray:
    g = img.convert("L").resize((PERCEPTUAL_PX, PERCEPTUAL_PX), Image.BILINEAR)
    return np.asarray(g, dtype=np.uint8)


def perceptual_png(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return _to_grid(im)


def perceptual_pdf(path: Path) -> tuple[np.ndarray, float, float]:
    """Rasterize page 0 and return (grid, page_w_pt, page_h_pt)."""
    mu = _pymupdf()
    with mu.open(path) as doc:
        page = doc[0]
        w_pt, h_pt = float(page.rect.width), float(page.rect.height)
        m = mu.Matrix(PDF_RASTER_DPI / 72.0, PDF_RASTER_DPI / 72.0)
        pix = page.get_pixmap(matrix=m, colorspace=mu.csGRAY, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    return _to_grid(Image.fromarray(arr)), w_pt, h_pt


def mad(a: np.ndarray, b: np.ndarray) -> float:
    """Mean absolute grayscale difference in [0, 1]; inf if shapes differ."""
    if a.shape != b.shape:
        return float("inf")
    return float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16)))) / 255.0

#!/usr/bin/env python3
"""Draw the layout mockup of a figure from its geometry file, before any data panel exists.

The geometry file is the single source of truth that panel scripts and the composer
both read, so the two never drift. Format (see assets/geometry.example.json):

    {
      "canvas_mm": [183, 120],          # 89 mm single column, 183 mm double column
      "letter_band_mm": 4.5,            # band above each row that holds the panel letters
      "letter_pt": 8,
      "boxes": [
        {"letter": "a", "name": "benchmark table", "x": 0, "y": 4.5, "w": 120, "h": 50},
        {"letter": "b", "name": "scaling curve",   "x": 124, "y": 4.5, "w": 59, "h": 50}
      ]
    }

x and y are the top-left corner in mm from the canvas top-left. Each box is drawn as a
labelled rectangle with its size, each letter at the box's top-left inside the letter band.
The script then checks the geometry and prints one line per problem:
  * a box that runs off the canvas;
  * two boxes that overlap;
  * boxes in one row (same y) with different heights (a patchwork row).
It also prints each box's size, which is the figure size the panel script must use.

    python mockup_layout.py geometry.json --out figures/figure_3/_mockup_layout

Writes <out>.pdf and <out>.png. Exit 1 if a check failed. Dependencies: matplotlib.
Adapted from the per-figure layout mockups of a paper-figures repository.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

MM_PER_INCH = 25.4
TOL = 0.05  # mm


def problems(geo: dict) -> list[str]:
    W, H = geo["canvas_mm"]
    out = []
    boxes = geo["boxes"]
    for b in boxes:
        if b["x"] < -TOL or b["y"] < -TOL or b["x"] + b["w"] > W + TOL or b["y"] + b["h"] > H + TOL:
            out.append(f"box {b['letter']} ({b['name']}) runs off the {W} x {H} mm canvas")
    for a, b in itertools.combinations(boxes, 2):
        ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
        oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
        if ox > TOL and oy > TOL:
            out.append(f"boxes {a['letter']} and {b['letter']} overlap by {ox:.1f} x {oy:.1f} mm")
    rows: dict[float, list[dict]] = {}
    for b in boxes:
        rows.setdefault(round(b["y"], 1), []).append(b)
    for y, row in rows.items():
        hs = {round(b["h"], 1) for b in row if not b.get("spans_rows")}
        if len(hs) > 1:
            out.append(f"row at y = {y} mm mixes heights {sorted(hs)} (set \"spans_rows\": true on a tall panel that spans rows)")
    return out


def draw(geo: dict, out: Path) -> None:
    W, H = geo["canvas_mm"]
    band = geo.get("letter_band_mm", 4.5)
    fig = plt.figure(figsize=(W / MM_PER_INCH, H / MM_PER_INCH))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, ls="--", lw=0.4, ec="#999999"))
    for b in geo["boxes"]:
        y0 = H - b["y"] - b["h"]
        ax.add_patch(Rectangle((b["x"], y0), b["w"], b["h"], facecolor="#e8eef6", edgecolor="#3a3a3a", linewidth=0.6))
        ax.text(b["x"] + b["w"] / 2, y0 + b["h"] / 2, f"{b['name']}\n{b['w']:.1f} x {b['h']:.1f} mm",
                ha="center", va="center", fontsize=6, color="#222222")
        ax.text(b["x"], H - b["y"] + band - 0.5, b["letter"], ha="left", va="top",
                fontsize=geo.get("letter_pt", 8), fontweight="bold", color="#000000")
    out.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(out.with_suffix(f".{ext}"), dpi=200)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Draw and check a figure's layout mockup from a geometry JSON file.")
    ap.add_argument("geometry", type=Path, help="geometry JSON")
    ap.add_argument("--out", type=Path, default=Path("_mockup_layout"), help="output stem (no extension)")
    a = ap.parse_args()
    geo = json.loads(a.geometry.read_text())
    draw(geo, a.out)
    print(f"wrote {a.out.with_suffix('.pdf')} and .png  (canvas {geo['canvas_mm'][0]} x {geo['canvas_mm'][1]} mm)")
    for b in geo["boxes"]:
        print(f"  {b['letter']}: {b['name']:<28} figsize {b['w']:.1f} x {b['h']:.1f} mm at ({b['x']:.1f}, {b['y']:.1f})")
    bad = problems(geo)
    for p in bad:
        print(f"PROBLEM  {p}")
    print("geometry checks passed" if not bad else f"{len(bad)} problem(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

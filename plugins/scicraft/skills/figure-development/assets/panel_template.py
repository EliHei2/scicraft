#!/usr/bin/env python3
"""Figure [N] panel [x]: [what is plotted, with the metric's definition and its direction].

Copy this file to code/figure_[N]/panel_[x]_[name].py and keep it thin: read one frozen
table, assert what the caption will claim about the rows being drawn, draw at the true
printed size, write a pdf + png pair under one stem. Long plotting code and aggregation
belong in code/figure_[N]/_prep/; styling belongs to the paper's style module (see the
data-figures skill). This example draws an ablation: median score per variant across
seeds, with the 25th to 75th percentile as the whisker.

Input: a long TSV with columns variant, seed, score (one row per variant x seed).
Values read from: [data/figure_N/<file>.tsv]   Adapted from: [upstream script, or "new"]

    python panel_template.py --data ablation.tsv --out figures/figure_N/panels --name panel_b_ablation

Dependencies: matplotlib, numpy.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

MM = 1 / 25.4
W_MM, H_MM = 60.0, 40.0           # true printed size, read from the mockup geometry
AX_MM = (12.0, 4.0, 45.0, 26.0)   # axes box: left, top, width, height in mm


def load(path: Path) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = defaultdict(dict)
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            rows[r["variant"]][r["seed"]] = float(r["score"])
    return rows


def check(rows: dict[str, dict[str, float]]) -> None:
    """The invariants the caption relies on. A failed assert stops the render."""
    seeds = {v: set(s) for v, s in rows.items()}
    first = next(iter(seeds.values()))
    assert all(s == first for s in seeds.values()), f"variants cover different seeds: {seeds}"
    assert len(first) >= 3, f"only {len(first)} seeds; an interquartile range needs at least 3"


def panel(data: Path, out: Path, name: str) -> None:
    rows = load(data)
    check(rows)
    order = list(rows)                       # keep the table's order; the full model row first
    vals = [np.array(list(rows[v].values())) for v in order]
    med = [float(np.median(v)) for v in vals]
    q1 = [float(np.percentile(v, 25)) for v in vals]
    q3 = [float(np.percentile(v, 75)) for v in vals]

    fig = plt.figure(figsize=(W_MM * MM, H_MM * MM))
    l, t, w, h = AX_MM
    ax = fig.add_axes([l / W_MM, 1 - (t + h) / H_MM, w / W_MM, h / H_MM])
    x = np.arange(len(order))
    ax.bar(x, med, width=0.3, color="#0072B2")
    ax.errorbar(x, med, yerr=[np.subtract(med, q1), np.subtract(q3, med)], fmt="none", ecolor="#111111", lw=0.6, capsize=1.5)
    ax.axhline(med[0], ls="--", lw=0.5, color="#111111")   # reference: the full model's median
    ax.set_xticks(x, order, rotation=30, ha="right", fontsize=5)
    ax.set_ylabel("[metric] (higher is better)", fontsize=6)
    ax.tick_params(labelsize=5, length=1.8, width=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_ylim(0, None)                     # bars start at 0 on a linear axis

    out.mkdir(parents=True, exist_ok=True)
    for ext, kw in (("pdf", {}), ("png", {"dpi": 600})):
        fig.savefig(out / f"{name}.{ext}", bbox_inches=None, pad_inches=0, **kw)   # page size == figure size
    plt.close(fig)
    print(f"wrote {out / name}.pdf and .png ({W_MM} x {H_MM} mm)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render one panel at its true printed size.")
    ap.add_argument("--data", type=Path, required=True, help="long TSV: variant, seed, score")
    ap.add_argument("--out", type=Path, required=True, help="output folder")
    ap.add_argument("--name", default="panel_x", help="output stem")
    a = ap.parse_args()
    panel(a.data, a.out, a.name)

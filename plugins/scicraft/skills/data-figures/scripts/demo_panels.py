#!/usr/bin/env python3
"""Render two demo panels from synthetic numbers with the house style, and write the layout that composes them.

Panel a: a benchmark rank heatmap (models x tasks, RANK5 steps, rank printed in every cell, mean rank and first
places, tasks bracketed by group). Panel b: a trade-off scatter (score against throughput, same marker size for
every model, hero drawn last, labels placed by the compass placer). Panel c: a rank plot (S.rank_plot) over the
tasks every model completed; the task one model did not complete is dropped for every model. The numbers are
random and seeded: they exercise the style, they are not results.

Usage:
    python3 demo_panels.py --out /tmp/demo                # writes panels/*.{pdf,png,svg} and layout.json
    python3 compose.py /tmp/demo/layout.json              # then compose
    python3 check_panel.py /tmp/demo/panels/*.pdf --figure /tmp/demo/demo_figure.pdf

Needs matplotlib, numpy; adjustText optional. Imports figstyle from ../assets (or from --style-dir).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def load_style(style_dir: Path):
    sys.path.insert(0, str(style_dir))
    import figstyle  # noqa: E402
    return figstyle


def synthetic(seed: int = 7):
    rng = np.random.default_rng(seed)
    models = ["Ours", "Strongest rival", "Model C", "Model D", "Model E", "Model F", "Tuned trees", "Linear"]
    tasks = ["cls 1", "cls 2", "cls 3", "reg 1", "reg 2", "reg 3"]
    skill = np.array([0.80, 0.74, 0.70, 0.66, 0.65, 0.60, 0.72, 0.50])
    score = np.clip(skill[:, None] + rng.normal(0, 0.05, (len(models), len(tasks))), 0, 1)
    score[5, 4] = np.nan                                # one model did not complete one task
    ranks = np.full_like(score, np.nan)
    for j in range(len(tasks)):
        ok = ~np.isnan(score[:, j])
        order = (-score[ok, j]).argsort().argsort() + 1
        ranks[ok, j] = order
        assert sorted(order.tolist()) == list(range(1, ok.sum() + 1))   # a valid ranking at every column
    throughput = np.exp(rng.normal(np.log([40, 12, 30, 55, 70, 90, 140, 400]), 0.1))
    return models, tasks, score, ranks, throughput


# Shared geometry (mm from the panel top): both panels put their plot area between these two lines, so the grids
# of a and b align in the composed figure.
GRID_TOP, ROW_H, N_ROWS = 12.6, 2.9, 8
GRID_BOTTOM = GRID_TOP + ROW_H * N_ROWS
PANEL_H = 44.0
TITLE_X = 3.8                                           # figstyle.title() x; the label column starts here


def text_width_mm(S, s: str, prop) -> float:
    """Printed width of a string in mm, measured with the renderer (sizes columns to their content)."""
    fig = S.fig_mm(50, 10)
    t = fig.text(0, 0, s, fontproperties=prop)
    fig.canvas.draw()
    w = t.get_window_extent(fig.canvas.get_renderer()).width / fig.dpi * 25.4
    __import__("matplotlib.pyplot").pyplot.close(fig)
    return w


def heatmap(S, models, tasks, ranks, out: Path) -> tuple[float, float]:
    from matplotlib.font_manager import FontProperties
    COL_W, SUM_GAP, SUM_W, TOP = 6.6, 1.0, 6.4, GRID_TOP
    bold = S.bold_font(S.TICK_PT)
    label_w = max(text_width_mm(S, m, bold if m == "Ours" else FontProperties(size=S.TICK_PT)) for m in models)
    LABEL_X = TITLE_X + label_w                         # no dead margin left of the row labels
    GRID_X = LABEL_X + 0.6
    W = round(GRID_X + len(tasks) * COL_W + SUM_GAP + 2 * SUM_W + 0.5, 1)   # and none on the right
    H = PANEL_H
    fig = S.fig_mm(W, H)
    c = S.canvas_mm(fig)

    def bracket(x0, x1, y, text, half_gap):
        mid = (x0 + x1) / 2
        for a, b in ((x0, mid - half_gap), (mid + half_gap, x1)):
            c.plot([a, b], [y, y], color=S.INK, lw=.35, solid_capstyle="butt")
        for x in (x0, x1):
            c.plot([x, x], [y - .55, y + .55], color=S.INK, lw=.35, solid_capstyle="butt")
        c.text(mid, y, text, ha="center", va="center_baseline", fontsize=S.TICK_PT)

    bracket(GRID_X + .9, GRID_X + 3 * COL_W - .9, 7.0, "classification", 6.0)
    bracket(GRID_X + 3 * COL_W + .9, GRID_X + 6 * COL_W - .9, 7.0, "regression", 4.6)
    for j, t in enumerate(tasks):
        c.text(GRID_X + (j + .5) * COL_W, TOP - .6, t, ha="center", va="bottom", fontsize=S.TICK_PT)
    sx = GRID_X + len(tasks) * COL_W + SUM_GAP
    for k, name in enumerate(("mean\nrank", "first\nplaces")):
        c.text(sx + (k + .5) * SUM_W, TOP - .6, name, ha="center", va="bottom", fontsize=S.TICK_PT, linespacing=.95)
    mean = np.nanmean(ranks, axis=1)
    order = np.argsort(mean)
    for i, m in enumerate(order):
        y = TOP + i * ROW_H
        hero = models[m] == "Ours"
        style = dict(fontproperties=bold, color=S.HERO) if hero else dict(fontsize=S.TICK_PT)
        c.text(LABEL_X, y + ROW_H / 2, models[m], ha="right", va="center_baseline", **style)
        for j in range(len(tasks)):
            r = ranks[m, j]
            face = S.BAND if np.isnan(r) else S.rank_color(r)
            c.add_patch(__import__("matplotlib").patches.Rectangle((GRID_X + j * COL_W, y), COL_W, ROW_H,
                                                                   facecolor=face, edgecolor=S.GUIDE, lw=.3))
            c.text(GRID_X + (j + .5) * COL_W, y + ROW_H / 2, "n/a" if np.isnan(r) else f"{r:g}", ha="center",
                   va="center_baseline", fontsize=S.TICK_PT, color=S.text_color_for(face))
        c.text(sx + .5 * SUM_W, y + ROW_H / 2, f"{mean[m]:.2f}", ha="center", va="center_baseline", **style)
        c.text(sx + 1.5 * SUM_W, y + ROW_H / 2, str(int(np.nansum(ranks[m] == 1))), ha="center",
               va="center_baseline", **style)
    assert len(models) == N_ROWS and GRID_BOTTOM < H
    S.title(fig, "Rank per task")
    S.save_panel(fig, out, "a_rank_heatmap")
    return W, H


def scatter(S, models, score, throughput, out: Path) -> tuple[float, float]:
    W, H = 56.0, PANEL_H                                # 8 labeled points: give room before shrinking
    fig = S.fig_mm(W, H)
    ax = S.axes_mm(fig, 9.5, GRID_TOP, 44.0, GRID_BOTTOM - GRID_TOP)   # plot area on panel a's grid lines
    mean = np.nanmedian(score, axis=1)                # median with its IQR; a mean can sit outside the IQR
    q1, q3 = np.nanpercentile(score, 25, axis=1), np.nanpercentile(score, 75, axis=1)
    colors = {m: S.HERO if m == "Ours" else S.RIVAL if m == "Strongest rival" else S.OTHER for m in models}
    labels = {m: m for m in models}
    xs = {m: float(np.log10(t)) for m, t in zip(models, throughput)}
    ys = {m: float(v) for m, v in zip(models, mean)}
    yerr = {m: (ys[m] - a, b - ys[m]) for m, a, b in zip(models, q1, q3)}
    S.tradeoff_scatter(ax, models, xs, ys, colors=colors, labels=labels, hero="Ours", x_step=0.5, y_step=0.1, pad_frac=0.16,
                       yerr=yerr)
    ax.set_xticks([1, 1.5, 2, 2.5])
    ax.set_xticklabels(["10", "30", "100", "300"])
    ax.set_xlabel("throughput (samples/s, log)")
    S.label_dir(ax, "median score", "up")              # the arrow points up on the page
    S.title(fig, "Score against speed")
    S.save_panel(fig, out, "b_tradeoff")
    return W, H


def rank_panel(S, models, score, out: Path) -> tuple[float, float]:
    W, H = 44.0, PANEL_H
    full = ~np.isnan(score).any(axis=0)                 # parity: a task missing for one model is dropped for all
    ranks = S.rank_columns(score[:, full])
    fig = S.fig_mm(W, H)
    ax = S.axes_mm(fig, 8.0, GRID_TOP, 34.0, GRID_BOTTOM - GRID_TOP)   # on panel a's grid lines
    short = {m: ("Rival" if m == "Strongest rival" else "Trees" if m == "Tuned trees" else m) for m in models}
    colors = {short[m]: S.HERO if m == "Ours" else S.RIVAL if m == "Strongest rival" else S.OTHER for m in models}
    S.rank_plot(ax, ranks, [short[m] for m in models], colors=colors, hero="Ours")
    ax.set_ylabel("rank over tasks")
    S.title(fig, f"Rank on {int(full.sum())} complete tasks")
    S.save_panel(fig, out, "c_rank_plot")
    return W, H


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, required=True, help="output folder (panels/ and layout.json go here)")
    ap.add_argument("--style-dir", type=Path, default=Path(__file__).resolve().parents[1] / "assets",
                    help="folder holding figstyle.py (default: the skill's assets/)")
    ap.add_argument("--font", default=None, help="helvetica (default), cm-sans, cm-serif or serif")
    a = ap.parse_args()
    S = load_style(a.style_dir)
    S.apply(font=a.font)
    models, tasks, score, ranks, thr = synthetic()
    panels = a.out / "panels"
    wa, ha = heatmap(S, models, tasks, ranks, panels)
    wb, hb = scatter(S, models, score, thr, panels)
    wc, hc = rank_panel(S, models, score, panels)
    gap = 3.0
    layout = {
        "width_mm": round(wa + wb + wc + 2 * gap, 2), "height_mm": max(ha, hb, hc), "letter_pt": S.LETTER_PT,
        "out": "demo_figure",
        "panels": [
            {"pdf": "panels/a_rank_heatmap.pdf", "x": 0, "y": 0, "w": wa, "h": ha, "letter": "a"},
            {"pdf": "panels/b_tradeoff.pdf", "x": wa + gap, "y": 0, "w": wb, "h": hb, "letter": "b"},
            {"pdf": "panels/c_rank_plot.pdf", "x": round(wa + wb + 2 * gap, 2), "y": 0, "w": wc, "h": hc,
             "letter": "c"},
        ],
    }
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "layout.json").write_text(json.dumps(layout, indent=2))
    print(f"wrote {panels}/a_rank_heatmap.*, b_tradeoff.*, c_rank_plot.* and {a.out / 'layout.json'}")
    print("body font:", S.resolved_font())
    return 0


if __name__ == "__main__":
    sys.exit(main())

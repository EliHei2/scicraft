"""[Figure N] panel [x]: [what is plotted, with the metric's definition and its direction].

Values read from [frozen table, e.g. data/figN/ablation_seeds.csv: columns variant, seed, score].
Bars: median over [units, e.g. seeds]; whiskers: 25th to 75th percentile of the same units. Bars start at 0.
Adapted from: [upstream script this panel reproduces, or "new"]

Copy to code/figure_N/panel_<letter>_<name>.py, keep it under about 150 lines, move data preparation to _prep/.
Run with no arguments to render the built-in demo records (synthetic, seeded) and see the shape.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))   # [point this at the folder that holds figstyle.py]
import figstyle as S  # noqa: E402

W_MM, H_MM = 44.0, 40.0                     # true printed size: read it off the mock-up, never rescale later
AX = (9.0, 7.0, 33.0, 21.0)                 # axes box: x, y from top, w, h in mm (shared with sibling panels)
TITLE = "[Score by ablation]"               # one short line; drop it when the y label already says it
YLABEL, BETTER = "[score]", "up"            # the quantity with its unit, and which way is better
HERO = "[full model]"                       # display name of the reference row, drawn first
OUT = Path(os.environ.get("PANEL_OUT", "figures/figN/panels"))
NAME = "[x_ablation]"
DISPLAY = {}                                # internal id -> manuscript name; only these names may print


def load(path: Path | None) -> dict[str, list[float]]:
    if path is None:                        # demo records: 5 seeds per variant
        rng = np.random.default_rng(0)
        base = {"[full model]": .81, "[no pretraining]": .72, "[no attention]": .76, "[half data]": .78}
        return {k: list(np.clip(v + rng.normal(0, .015, 5), 0, 1)) for k, v in base.items()}
    rows = defaultdict(list)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows[DISPLAY.get(r["variant"], r["variant"])].append(float(r["score"]))
    return dict(rows)


def panel(path: Path | None = None) -> Path:
    S.apply()
    data = load(path)
    assert HERO in data, f"reference row {HERO!r} missing"
    n = {k: len(v) for k, v in data.items()}
    assert len(set(n.values())) == 1, f"unequal units per variant {n}: report it, never drop runs to match"
    names = [HERO] + sorted((k for k in data if k != HERO), key=lambda k: -np.median(data[k]))
    med = np.array([np.median(data[k]) for k in names])
    q1 = np.array([np.percentile(data[k], 25) for k in names])
    q3 = np.array([np.percentile(data[k], 75) for k in names])
    colors = [S.lighten(S.HERO, .15)] + [S.lighten(S.OTHER, .2)] * (len(names) - 1)
    fig = S.fig_mm(W_MM, H_MM)
    ax = S.axes_mm(fig, *AX)
    S.method_bars(ax, med, colors, ymax=1.0, yticks=[0, .5, 1.0], xlabels=names, err_lo=q1, err_hi=q3,
                  hero_value=med[0], rotation=30)
    ax.set_yticklabels(["0", ".5", "1"])
    S.label_dir(ax, YLABEL, BETTER)        # the arrow points the better way on the page
    if TITLE:
        S.title(fig, TITLE)
    return S.save_panel(fig, OUT, NAME)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render this panel at true size (.pdf, .png, .svg).")
    ap.add_argument("--data", type=Path, help="CSV with columns variant, seed, score (default: demo records)")
    stem = panel(ap.parse_args().data)
    print(f"wrote {stem}.pdf/.png/.svg")

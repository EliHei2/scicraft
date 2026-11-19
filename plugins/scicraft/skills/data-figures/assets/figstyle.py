"""House style for matplotlib data panels drawn at true printed size. One import, no inline rcParams elsewhere.

Copy this file into the project (for example `assets/figstyle.py`) and import it from every panel script:

    import figstyle as S
    S.apply()                                  # or S.apply(font="cm-sans") for a LaTeX-default host
    fig = S.fig_mm(89, 55)
    ax = S.axes_mm(fig, 12, 6, 70, 40)         # x, y from the TOP-left, w, h, all in mm
    S.despine(ax)
    ...
    S.save_panel(fig, "figures/fig1/panels", "b_ablation")   # .pdf + .png + live-text .svg

Requires matplotlib >= 3.5 and numpy. Optional: fontTools (bold face out of a .ttc collection), adjustText >= 1.0
(label repulsion; `repel_labels` falls back to a dependency-free compass placer without it).

Merged from the author's paper style module, its figure-utility package (mm geometry, save, color, labels,
bars, scatter) and the newer reply-style module of a later rebuttal. Field-specific names were removed; palette
roles carry generic names.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import matplotlib

if os.environ.get("MPLBACKEND") is None:
    matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, ListedColormap  # noqa: E402

MM = 1 / 25.4                      # inches per mm
MM_PT = 72.0 / 25.4                # PDF points per mm

# ---------------------------------------------------------------------------------------------------------------
# Page widths (mm). Draw every panel at its final size; never rescale in the composer.
WIDTH_MM = {
    "nature-single": 89.0, "nature-double": 183.0,
    "iclr-text": 139.7, "neurips-text": 139.7, "icml-column": 82.5, "icml-text": 171.5,   # 5.5 in, 3.25 in, 6.75 in
    "a4-text": 165.1,              # 6.5 in: A4 with 2.2 cm margins
}

# Text tiers (pt at print size). Exactly three plus the panel letter. 5 pt is the floor for any text.
TITLE_PT, LABEL_PT, TICK_PT = 7.0, 6.0, 5.0
LETTER_PT = 8.0                    # one size per paper for data, schematic and TikZ figures; a venue rule wins; at most 10.5
FLOOR_PT = 5.0
CELL_MIN_PT = 3.3                  # in-cell heatmap values may shrink to this, never lower

# ---------------------------------------------------------------------------------------------------------------
# Color roles. Assign by role, never by method count. Variants of the hero share its hue.
HERO = "#0072B2"         # the method the paper is about (Okabe-Ito blue)
HERO_ALT = "#0A3D66"     # a second read-out or variant of the hero: same hue, darker, diamond marker
HERO_PRIOR = "#8DBEDD"   # an earlier version of the hero: same hue, lighter, open marker
RIVAL = "#E69F00"        # the strongest comparator (Okabe-Ito orange)
OTHER = "#A8A8AD"        # every other comparator: context, never a competitor color
BASELINE = "#6E6E73"     # untrained twin, random or trivial baseline
CLAIM = "#0072B2"        # pre-registered claim holds (filled mark)
AGAINST = "#D55E00"      # finding against the claim (filled mark)
NOCLAIM = "#C7C7CC"      # no claim (open mark)
FAIL = "#D6321E"         # the one saturated red: a run that did not complete; nothing else may use it
BAND = "#EFEFF1"         # seed-to-seed noise band
GUIDE = "#D1D1D6"        # faint guide lines, heatmap grid
GRID = "#E6E8EB"         # optional faint y-grid on bar panels (lw 0.38)
LEADER = "#9AA1AA"       # label leader lines and scatter error bars
INK = "#111111"          # spines and ticks
TEXT = "#000000"         # all figure text; a hero label, or a metric's y label when metrics are compared, may take its series color
MISSING_FACE, MISSING_EDGE, MISSING_HATCH = "#DDDDDD", "#888888", "//"
UNLABELLED = "#9A9AA0"   # recessive gray for unlabeled items; never the ground color
# Category colors of one paper, in one place. Fill CATEGORY with canonical label -> hex and ALIASES with every
# spelling found in the data -> canonical label; every panel and supplement calls category_color().
CATEGORY: dict[str, str] = {}
ALIASES: dict[str, str] = {}
UNKNOWN = "#666666"      # an unknown label shows as this gray on the render instead of borrowing a hue

# Okabe-Ito, for categorical series beyond hero and rival (color-blind safe). Keep other categorical systems
# (datasets, platforms, cell types) in hues disjoint from these.
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
# Grouping metadata (datasets, platforms): a cool pastel family, used on icons, brackets and labels only.
METADATA_PASTEL = ["#9FD5C0", "#AFC6E9", "#C9B7E6", "#E9B1C0", "#F1C48A"]

# Sequential ramps. Rank heatmaps use RANK5 (best = darkest); ordered sweeps use a single-hue ramp.
RANK5 = ListedColormap(["#F1F6FF", "#C7DCFF", "#8FB9FF", "#4D97FF", "#003FBD"], name="rank5_blue")
MUTED5 = ListedColormap(["#E8F0F7", "#CFDEEB", "#A6BFD7", "#7099BD", "#4A7CA8"], name="muted5_blue")
SWEEP_BLUE = ["#C7DCEC", "#A4C4DD", "#7EA8CC", "#5790BE", "#356D9C", "#1B4773"]
SWEEP_LEMON = ["#F7EDA8", "#8C7800"]       # endpoints; a second sweep family that stays clear of RIVAL orange

# Diverging map with a wide white plateau: blue (depleted, worse) to red (enriched, better or the reverse, say
# which in the caption). Use with TwoSlopeNorm(vmin=data min, vcenter=meaningful baseline, vmax=data max), and only
# with the values printed in the cells.
DIVERGING = LinearSegmentedColormap.from_list("diverging_plateau", [
    (0.00, "#0A84FF"), (0.30, "#7DB9FF"), (0.43, "#D6E8FF"), (0.50, "#FFFFFF"),
    (0.57, "#FFD9D6"), (0.70, "#FF8C84"), (1.00, "#FF3B30")], N=256)
# Alternative for a schematic matrix drawn without values, or when red already means something else in the figure.
DELTA = LinearSegmentedColormap.from_list("delta_blue_orange", ["#2166AC", "#F7F7F7", "#D55E00"], N=256)

# ---------------------------------------------------------------------------------------------------------------
# Fonts. The font follows the host document.
FONT_STACKS = {
    "helvetica": ["Helvetica Neue", "Helvetica", "Arial", "Liberation Sans", "Nimbus Sans", "DejaVu Sans"],
    "cm-sans": ["cmss10"],         # matches LaTeX \sffamily (Computer Modern Sans); ships with matplotlib
    "cm-serif": ["cmr10"],         # matches a default LaTeX serif body
    "serif": ["TeX Gyre Pagella", "Palatino", "Palatino Linotype", "Book Antiqua", "DejaVu Serif"],
}
_TTC = ("/System/Library/Fonts/HelveticaNeue.ttc", "/Library/Fonts/HelveticaNeue.ttc")
_CACHE = Path(os.environ.get("FIGSTYLE_CACHE", Path.home() / ".cache" / "figstyle"))
_MODE = {"font": "helvetica"}


def _register_system_fonts() -> None:
    """matplotlib silently falls back to DejaVu Sans unless the macOS Helvetica Neue collection is registered."""
    for p in _TTC:
        if Path(p).is_file():
            try:
                fm.fontManager.addfont(p)
            except Exception:
                pass
            break


_register_system_fonts()


def bold_font(size: float | None = None) -> fm.FontProperties:
    """A real bold face. matplotlib indexes only the FIRST face of a .ttc, so fontweight="bold" on Helvetica Neue
    silently renders regular. This extracts HelveticaNeue-Bold once (fontTools) into a cached .ttf. Elsewhere it
    returns the bold weight of the active stack."""
    if _MODE["font"] == "helvetica":
        ttf = _CACHE / "HelveticaNeue-Bold.ttf"
        if not ttf.is_file():
            try:
                from fontTools.ttLib import TTCollection
                for p in _TTC:
                    if Path(p).is_file():
                        face = next(f for f in TTCollection(p).fonts if f["name"].getDebugName(6) == "HelveticaNeue-Bold")
                        ttf.parent.mkdir(parents=True, exist_ok=True)
                        face.save(str(ttf))
                        break
            except Exception:
                pass
        if ttf.is_file():
            return fm.FontProperties(fname=str(ttf), size=size)
    if _MODE["font"] in ("cm-sans", "cm-serif"):
        return fm.FontProperties(family="cmb10" if _MODE["font"] == "cm-serif" else "cmss10", weight="bold", size=size)
    return fm.FontProperties(family=FONT_STACKS[_MODE["font"]], weight="bold", size=size)


def bold_font_file() -> str | None:
    """Path of the bold face file, for the composer's panel letters (None if only a family name is known)."""
    try:
        return fm.findfont(bold_font(), fallback_to_default=False)
    except Exception:
        return None


def resolved_font() -> str:
    """The family matplotlib will actually use for body text. Check it once per machine."""
    return fm.FontProperties(family=plt.rcParams["font.family"]).get_name() if plt.rcParams["font.family"] else "?"


def apply(font: str | None = None, scale: float = 1.0, letter_pt: float | None = None) -> None:
    """Set the house rcParams. `font` in FONT_STACKS (default from $FIGSTYLE_FONT, else "helvetica").
    `scale` multiplies all three tiers together (a figure once took x1.1); ratios stay fixed and 5 pt stays the floor."""
    global TITLE_PT, LABEL_PT, TICK_PT, LETTER_PT
    font = font or os.environ.get("FIGSTYLE_FONT", "helvetica")
    if font not in FONT_STACKS:
        raise ValueError(f"font must be one of {sorted(FONT_STACKS)}")
    _MODE["font"] = font
    TITLE_PT, LABEL_PT, TICK_PT = (max(FLOOR_PT, v * scale) for v in (7.0, 6.0, 5.0))
    if letter_pt:
        LETTER_PT = letter_pt
    stack = FONT_STACKS[font]
    serif = font in ("cm-serif", "serif")
    rc = {
        "font.family": "serif" if serif else "sans-serif",
        ("font.serif" if serif else "font.sans-serif"): stack,
        "font.weight": "light" if font == "helvetica" else "normal",
        "font.size": TICK_PT, "axes.labelsize": LABEL_PT, "axes.titlesize": TITLE_PT,
        "xtick.labelsize": TICK_PT, "ytick.labelsize": TICK_PT, "legend.fontsize": TICK_PT,
        "axes.labelweight": "light" if font == "helvetica" else "normal", "axes.titleweight": "normal",
        "text.color": TEXT, "axes.labelcolor": TEXT, "xtick.color": INK, "ytick.color": INK,
        "xtick.labelcolor": TEXT, "ytick.labelcolor": TEXT, "axes.edgecolor": INK,
        "axes.linewidth": 0.5, "xtick.major.width": 0.4, "ytick.major.width": 0.4,
        "xtick.major.size": 1.8, "ytick.major.size": 1.8, "xtick.major.pad": 1.4, "ytick.major.pad": 1.4,
        "xtick.direction": "out", "ytick.direction": "out", "xtick.minor.visible": False, "ytick.minor.visible": False,
        "axes.labelpad": 1.8, "axes.titlepad": 3.0, "lines.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
        "figure.facecolor": "none", "axes.facecolor": "none", "savefig.transparent": True,   # prints as white; never dark
        "legend.frameon": False, "legend.handletextpad": 0.4, "legend.borderaxespad": 0.2,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",   # embedded TrueType, live SVG text
        "figure.dpi": 150, "savefig.dpi": 600, "savefig.bbox": None, "savefig.pad_inches": 0.0,
        "axes.unicode_minus": True,
    }
    if font == "helvetica":
        rc.update({"mathtext.fontset": "custom", "mathtext.rm": "Helvetica Neue", "mathtext.it": "Helvetica Neue:italic",
                   "mathtext.bf": "Helvetica Neue:bold", "mathtext.default": "regular"})
    elif font in ("cm-sans", "cm-serif"):
        # cm fonts lack U+2212 and map U+00B5 to a grave accent: draw minus and mu through mathtext.
        rc.update({"mathtext.fontset": "cm", "axes.formatter.use_mathtext": True, "mathtext.default": "regular"})
        if font == "cm-sans":
            rc.update({"mathtext.fontset": "custom", "mathtext.rm": "cmss10", "mathtext.it": "cmss10:italic",
                       "mathtext.bf": "cmss10:bold", "mathtext.sf": "cmss10"})
    else:
        rc.update({"mathtext.fontset": "dejavuserif"})
    plt.rcParams.update(rc)


# ---------------------------------------------------------------------------------------------------------------
# Geometry in mm.

def fig_mm(w_mm: float, h_mm: float):
    """A figure whose page will be exactly w x h mm (save_panel never crops)."""
    fig = plt.figure(figsize=(w_mm * MM, h_mm * MM))
    fig.patch.set_facecolor("none")              # transparent ground; heatmap cells carry their own fill
    return fig


def axes_mm(fig, x_mm: float, y_top_mm: float, w_mm: float, h_mm: float):
    """Axes at an absolute mm box measured from the figure's TOP-left corner."""
    fw, fh = (v / MM for v in fig.get_size_inches())
    return fig.add_axes([x_mm / fw, 1.0 - (y_top_mm + h_mm) / fh, w_mm / fw, h_mm / fh])


def canvas_mm(fig):
    """One invisible axes over the whole figure in mm, y pointing down: draw tables and matrices cell by cell."""
    w, h = (v / MM for v in fig.get_size_inches())
    c = fig.add_axes([0, 0, 1, 1])
    c.set_xlim(0, w)
    c.set_ylim(h, 0)
    c.set_axis_off()
    return c


def text_mm(fig, x_mm: float, y_mm: float, s: str, **kw):
    """Figure text at mm from the top-left. fig.text counts y from the BOTTOM as a fraction; mixing the two throws
    an annotation to the opposite edge."""
    w, h = (v / MM for v in fig.get_size_inches())
    kw.setdefault("va", "baseline")
    return fig.text(x_mm / w, 1 - y_mm / h, s, **kw)


def title(fig, s: str, x_mm: float = 3.8, y_mm: float = 4.2):
    """Panel title: one short line, left-aligned, on the same baseline as the composer's letter (letter at x 0.3 mm)."""
    return text_mm(fig, x_mm, y_mm, s, fontsize=TITLE_PT, ha="left")


def despine(ax, left: bool = True, bottom: bool = True, weight: str = "compact") -> None:
    """Top and right gone; left and bottom #111111; ticks outward; no grid.
    compact (panels up to about 60 mm): spine 0.5, tick width 0.4, length 1.8. large: 0.9, 0.9, 3.4."""
    lw, tw, tl = (0.5, 0.4, 1.8) if weight == "compact" else (0.9, 0.9, 3.4)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK)
        ax.spines[s].set_linewidth(lw)
    ax.tick_params(axis="both", colors=INK, labelcolor=TEXT, width=tw, length=tl, direction="out")
    ax.set_facecolor("none")
    ax.grid(False)


def zero(ax, axis: str = "y", color: str = INK, lw: float = 0.4) -> None:
    """A thin zero line for signed quantities (forest plots, deltas)."""
    (ax.axhline if axis == "y" else ax.axvline)(0, color=color, lw=lw, zorder=1.5)


def nice_ticks(lo: float, hi: float, step: float) -> list[float]:
    """Round ticks (multiples of `step`) inside [lo, hi]; at most 3 when more would crowd."""
    first = math.ceil(lo / step - 1e-9) * step
    ticks, v = [], first
    while v <= hi + 1e-9:
        ticks.append(round(v, 6))
        v += step
    if len(ticks) > 4:
        ticks = [ticks[0], ticks[len(ticks) // 2], ticks[-1]]
    return ticks or [round((lo + hi) / 2, 3)]


def nice_axis(lo: float, hi: float, n_max: int = 4) -> list[float]:
    """Ticks that cover [lo, hi] with a step from {1, 2, 2.5, 5} x 10^k: the smallest step that needs at most `n_max`
    ticks. A hard-coded step ladder that stopped at 500 once drew 0 to 10,000 for a bar of about 1,700."""
    span = max(hi - lo, 1e-12)
    for k in range(int(math.floor(math.log10(span))) - 2, int(math.ceil(math.log10(span))) + 2):
        for m in (1.0, 2.0, 2.5, 5.0):
            step = m * 10.0 ** k
            first, last = math.floor(lo / step + 1e-9), math.ceil(hi / step - 1e-9)
            if last - first + 1 <= n_max:
                return [round(i * step, 10) for i in range(first, last + 1)]
    return [lo, hi]


def ticks_span(ax, axis: str = "y", ticks=None) -> None:
    """The axis line starts and ends on a tick: limits and spine bounds equal the first and last tick."""
    a = ax.yaxis if axis == "y" else ax.xaxis
    t = list(ticks) if ticks is not None else [v for v in a.get_ticklocs()]
    a.set_ticks(t)
    (ax.set_ylim if axis == "y" else ax.set_xlim)(t[0], t[-1])
    ax.spines["left" if axis == "y" else "bottom"].set_bounds(t[0], t[-1])


def log_decades(ax, lo: float, hi: float, axis: str = "y") -> None:
    """Log axis snapped to the bounding decades, so the spine starts and ends on a tick. Positive values only."""
    a, b = 10.0 ** math.floor(math.log10(lo)), 10.0 ** math.ceil(math.log10(hi))
    (ax.set_yscale if axis == "y" else ax.set_xscale)("log")
    ticks = [10.0 ** k for k in range(int(round(math.log10(a))), int(round(math.log10(b))) + 1)]
    ticks_span(ax, axis, ticks)


def num(x: float, d: int = 3, sign: bool = False, lead_zero: bool = False) -> str:
    """House number style: .642 (leading zero dropped unless lead_zero), true minus U+2212, optional + sign."""
    s = f"{abs(x):.{d}f}"
    if not lead_zero and s.startswith("0."):
        s = s[1:]
    pre = "−" if x < 0 and float(f"{abs(x):.{d}f}") != 0 else ("+" if sign and x >= 0 else "")
    return pre + s


ARROW_UP, ARROW_DOWN = r"$\uparrow$", r"$\downarrow$"   # Helvetica Neue has no U+2191/U+2193 glyph
ARROW_RIGHT, ARROW_LEFT = r"$\rightarrow$", r"$\leftarrow$"


def label_dir(ax, text: str, better: str, axis: str = "y", **kw):
    """Axis label with a mark that shows the better direction ON THE PAGE. better: "up", "down" (y axis) or
    "right", "left" (x axis). A y label is rotated 90 degrees, so an up arrow typed into it points LEFT on the page;
    here the arrow is chosen in the label's own reading direction (page-up = text-right). Look at the result."""
    if axis == "y":
        mark = {"up": ARROW_RIGHT, "down": ARROW_LEFT}[better]
        return ax.set_ylabel(f"{text} {mark}", **kw)
    mark = {"right": ARROW_RIGHT, "left": ARROW_LEFT}[better]
    return ax.set_xlabel(f"{text} {mark}", **kw)


# ---------------------------------------------------------------------------------------------------------------
# Color helpers.

def lighten(color, factor: float = 0.45) -> tuple[float, float, float]:
    """Blend toward white by `factor` (0 unchanged, 1 white). Bars use a lightened series color."""
    r, g, b = mcolors.to_rgb(color)
    return (r + (1 - r) * factor, g + (1 - g) * factor, b + (1 - b) * factor)


def text_color_for(color, threshold: float = 0.62, dark: str = TEXT, light: str = "#FFFFFF") -> str:
    """White or black text on a filled cell (BT.601 luminance). Re-pick the threshold after any cmap change."""
    r, g, b = mcolors.to_rgb(color)
    return light if 0.299 * r + 0.587 * g + 0.114 * b < threshold else dark


def category_color(label) -> str:
    """Color of a category label: ALIASES resolves the spelling, CATEGORY gives the hex. An empty label is
    UNLABELLED; a label found in neither table is UNKNOWN, so a typo shows on the render."""
    if label is None or str(label).strip() == "":
        return UNLABELLED
    key = ALIASES.get(str(label), str(label))
    return CATEGORY.get(key, UNKNOWN)


def rank_color(rank: float, cuts=(1, 2, 3, 7)) -> str:
    """RANK5 step for a rank (1 = best = darkest). Ties take the next whole place: 3.5 falls in 4 to 7."""
    r = math.ceil(rank)
    c = RANK5.colors
    return c[4] if r <= cuts[0] else c[3] if r <= cuts[1] else c[2] if r <= cuts[2] else c[1] if r <= cuts[3] else c[0]


# ---------------------------------------------------------------------------------------------------------------
# Labels.

def compass_place(fig, ax, order, xs, ys, disp, colors, hero=None, label_fs=None, radius_pt: float = 4.5,
                  ink: str = TEXT, obstacles=(), clear_pt: float = 0.8):
    """Dependency-free label placer: each label's NEAREST EDGE sits `radius_pt` from its marker, in the best of 12
    directions. No leader lines. `order` is the placement order, hero first. Returns the text objects.

    Hard obstacles (a label may touch none of them, with `clear_pt` of air): every marker, every label already
    placed, and every rectangle in `obstacles` given in data units as (x0, y0, x1, y1), for example each error bar
    as (x, lo, x, hi), and the axes frame. A mild preference for placing labels above breaks ties. If no direction
    is free, the least bad one wins: give the panel more room and look."""
    label_fs = label_fs or TICK_PT
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    axbb = ax.get_window_extent()
    px_pt = fig.dpi / 72.0
    R, pad = radius_pt * px_pt, clear_pt * px_pt
    mark_r = 2.2 * px_pt                                  # half the size of a 16-pt^2 marker plus its white edge
    pt = {m: ax.transData.transform((xs[m], ys[m])) for m in order}
    hard = [(x - mark_r, y - mark_r, x + mark_r, y + mark_r) for x, y in pt.values()]
    for x0, y0, x1, y1 in obstacles:
        (ax0, ay0), (ax1, ay1) = ax.transData.transform((x0, y0)), ax.transData.transform((x1, y1))
        hard.append((min(ax0, ax1) - 0.6 * px_pt, min(ay0, ay1), max(ax0, ax1) + 0.6 * px_pt, max(ay0, ay1)))
    dirs = [(math.cos(t), math.sin(t)) for t in (i * math.pi / 6.0 for i in range(12))]
    inv = ax.transData.inverted()
    out = []
    for m in order:
        is_hero = m == hero
        t = ax.text(xs[m], ys[m], disp[m], fontsize=label_fs, color=colors[m] if is_hero else ink,
                    fontproperties=bold_font(label_fs) if is_hero else None,
                    ha="center", va="center", zorder=12, clip_on=False)
        bb = t.get_window_extent(rend)
        hw, hh = bb.width / 2.0, bb.height / 2.0
        px, py = pt[m]
        own = (px - mark_r, py - mark_r, px + mark_r, py + mark_r)
        best, best_cost = None, 1e18
        for ux, uy in dirs:
            s = min(hw / abs(ux) if abs(ux) > 1e-6 else 1e9, hh / abs(uy) if abs(uy) > 1e-6 else 1e9)
            cx, cy = px + ux * (R + s), py + uy * (R + s)
            x0, y0, x1, y1 = cx - hw - pad, cy - hh - pad, cx + hw + pad, cy + hh + pad
            out_px = (max(0.0, axbb.x0 - x0) + max(0.0, x1 - axbb.x1)
                      + max(0.0, axbb.y0 - y0) + max(0.0, y1 - axbb.y1))
            cost = (1000 + 6 * out_px) if out_px > 0 else 0.0
            for o in hard:
                if o is not own and min(x1, o[2]) > max(x0, o[0]) and min(y1, o[3]) > max(y0, o[1]):
                    cost += 1000
            cost += (1.0 - uy) * 0.4
            if cost < best_cost:
                best_cost, best = cost, (cx, cy, x0 + pad, y0 + pad, x1 - pad, y1 - pad)
        cx, cy, *box = best
        t.set_position(inv.transform((cx, cy)))
        hard.append(tuple(box))                           # placed labels are obstacles for the next ones
        out.append(t)
    return out


def repel_labels(ax, xs, ys, labels, colors=None, hero=None, avoid_x=None, avoid_y=None, label_fs=None):
    """ggrepel-style labels with adjustText (recipe that stopped labels landing on dots). Texts start at their
    points with a white 1.6 pt halo; ALL highlighted points are obstacles; each label is pulled to its own point;
    leaders are thin. Falls back to compass_place when adjustText is missing. Check the result at 2 to 3x zoom."""
    label_fs = label_fs or TICK_PT
    colors = colors or {}
    try:
        from adjustText import adjust_text
    except Exception:
        keys = list(labels)
        order = ([hero] if hero in labels else []) + [k for k in keys if k != hero]
        return compass_place(ax.figure, ax, order, xs, ys, labels, {k: colors.get(k, TEXT) for k in keys},
                             hero=hero, label_fs=label_fs)
    keys = list(labels)
    texts = [ax.text(xs[k], ys[k], labels[k], fontsize=label_fs,
                     color=colors.get(k, TEXT) if k == hero else TEXT,
                     fontproperties=bold_font(label_fs) if k == hero else None, ha="center", va="center", zorder=12,
                     path_effects=[pe.withStroke(linewidth=1.6, foreground="white")]) for k in keys]
    px = np.array([xs[k] for k in keys], float) if avoid_x is None else np.asarray(avoid_x, float)
    py = np.array([ys[k] for k in keys], float) if avoid_y is None else np.asarray(avoid_y, float)
    adjust_text(texts, x=px, y=py, target_x=[xs[k] for k in keys], target_y=[ys[k] for k in keys], ax=ax,
                force_text=(0.5, 0.9), force_static=(0.4, 0.7), force_pull=(0.005, 0.005), expand=(1.5, 1.8),
                prevent_crossings=True, ensure_inside_axes=True, min_arrow_len=3, iter_lim=600,
                arrowprops=dict(arrowstyle="-", color=LEADER, lw=0.3, alpha=0.75, shrinkA=1, shrinkB=2))
    return texts


def legend_mm(fig, entries, x_mm: float, y_mm: float, ncol: int = 1, col_w_mm: float = 18.0, row_h_mm: float = 2.6,
              marker: str = "o", ms: float = 2.6):
    """A shared legend outside every plot area: circle markers, black 5 pt text, entries [(label, color), ...]
    laid out in `ncol` columns from (x_mm, y_mm) at the top-left. Order entries as the marks are ordered."""
    w, h = (v / MM for v in fig.get_size_inches())
    c = fig.add_axes([0, 0, 1, 1], zorder=-1)
    c.set_xlim(0, w)
    c.set_ylim(h, 0)
    c.set_axis_off()
    for i, (lab, col) in enumerate(entries):
        cx, cy = x_mm + (i % ncol) * col_w_mm, y_mm + (i // ncol) * row_h_mm
        c.plot([cx + 0.8], [cy], marker=marker, ms=ms, mfc=col, mec=col, mew=0, ls="none")
        c.text(cx + 2.0, cy, lab, fontsize=TICK_PT, ha="left", va="center_baseline", color=TEXT)
    return c


# ---------------------------------------------------------------------------------------------------------------
# Chart forms that were rebuilt more than once.

def method_bars(ax, values, colors, *, ymax, yticks, xlabels, ymin: float = 0.0, err_lo=None, err_hi=None,
                hero_value=None, bar_width: float = 0.34, rotation: float = 90, grid: bool = False,
                value_fmt=None) -> None:
    """Thin vertical bars, one per method, hero first, bars from `ymin` (0 on a linear axis). `err_lo`/`err_hi` are
    the 25th and 75th percentiles (absolute values, NaN where absent). `hero_value` draws a dashed reference from
    the hero bar across the others. No x ticks; names label the bars; the y spine ends on its last tick."""
    x = np.arange(len(values))
    vals = np.asarray(values, float)
    ax.bar(x, vals - ymin, bottom=ymin, width=bar_width, color=colors, edgecolor="none", zorder=3)
    if hero_value is not None and np.isfinite(hero_value):
        ax.plot([-bar_width / 2, len(vals) - 1 + bar_width / 2], [hero_value] * 2, color=LEADER, lw=0.6,
                ls=(0, (2.4, 1.8)), zorder=5)
    if err_lo is not None and err_hi is not None:
        lo, hi = np.asarray(err_lo, float), np.asarray(err_hi, float)
        ok = np.isfinite(lo) & np.isfinite(hi)
        ax.errorbar(x[ok], vals[ok], yerr=[vals[ok] - lo[ok], hi[ok] - vals[ok]], fmt="none", elinewidth=0.5,
                    ecolor=INK, capsize=1.3, capthick=0.5, zorder=6)
    if value_fmt:
        for xi, v in zip(x, vals):
            ax.text(xi, v + (ymax - ymin) * 0.02, value_fmt(v), ha="center", va="bottom", fontsize=TICK_PT)
    ax.set_xlim(-0.6, len(vals) - 0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, rotation=rotation, ha="center" if rotation in (0, 90) else "right",
                       rotation_mode="anchor" if rotation not in (0, 90) else "default")
    if grid:
        ax.grid(axis="y", color=GRID, lw=0.38, zorder=0)
        ax.set_axisbelow(True)
    despine(ax, bottom=False)
    ax.tick_params(axis="x", length=0, pad=1.3)
    t = [float(v) for v in yticks]
    if t[0] != ymin:
        t = [ymin] + [v for v in t if v > ymin]
    if t[-1] < np.nanmax(np.r_[vals, err_hi if err_hi is not None else vals]):
        raise ValueError("last y tick is below the largest bar or whisker; add a tick so nothing is cut")
    ticks_span(ax, "y", t)


def rank_columns(scores, higher_better: bool = True) -> np.ndarray:
    """Per-column ranks (rows = methods, columns = datasets), 1 = best, ties share the average place, NaN stays NaN."""
    v = np.asarray(scores, float)
    out = np.full_like(v, np.nan)
    for j in range(v.shape[1]):
        ok = np.isfinite(v[:, j])
        col = -v[ok, j] if higher_better else v[ok, j]
        order = np.argsort(col, kind="mergesort")
        r = np.empty(ok.sum())
        i = 0
        while i < len(order):
            k = i
            while k + 1 < len(order) and abs(col[order[k + 1]] - col[order[i]]) <= 1e-12:
                k += 1
            r[order[i:k + 1]] = (i + k) / 2.0 + 1.0
            i = k + 1
        out[ok, j] = r
    return out


def rank_plot(ax, ranks, methods, colors=None, hero=None, jitter: float = 0.22, dot_s: float = 6.0,
              tick_half: float = 0.30, tick_lw: float = 1.0, rotation: float = 30) -> list[str]:
    """Rank plot: methods on x sorted by mean rank (best left), rank on y with 1 at the top, one small dot per dataset
    with deterministic index-based jitter (reruns are identical), and a short horizontal tick at the mean rank (the
    big mean marker was retired: "small lines instead of big blob for the median"). Every method gets the same dot
    size and tick width; the hero is told apart by color, z-order and a bold label. `ranks` is (methods x datasets).
    Asserts that every dataset ranks every method exactly once: drop a dataset for every method when one value is
    missing. Returns the method order drawn."""
    r = np.asarray(ranks, float)
    n_m, n_d = r.shape
    assert n_m == len(methods), "one row of ranks per method"
    assert np.isfinite(r).all(), "a dataset lacks a rank for some method: drop it for every method and say so"
    for j in range(n_d):
        assert abs(r[:, j].sum() - n_m * (n_m + 1) / 2) < 1e-6 and r[:, j].min() >= 1, f"dataset {j}: not a ranking"
    colors = colors or {}
    mean = r.mean(axis=1)
    order = sorted(range(n_m), key=lambda i: (mean[i], methods[i]))
    offs = jitter * (np.arange(n_d) / (n_d - 1) - 0.5) if n_d > 1 else np.zeros(1)
    for x, i in enumerate(order):
        m = methods[i]
        c = colors.get(m, OTHER)
        z = 6 if m == hero else 4
        ax.scatter(x + offs, r[i], s=dot_s, color=c, edgecolors="none", alpha=0.55, zorder=z)
        ax.plot([x - tick_half, x + tick_half], [mean[i]] * 2, color=c, lw=tick_lw, solid_capstyle="butt", zorder=z + 1)
    ax.set_xlim(-0.6, n_m - 0.4)
    ax.set_ylim(n_m + 0.6, 0.4)
    ax.set_yticks(range(1, n_m + 1))
    ax.set_xticks(range(n_m))
    names = [methods[i] for i in order]
    ax.set_xticklabels(names, rotation=rotation, ha="right" if rotation else "center", rotation_mode="anchor")
    despine(ax, bottom=False)                           # before the hero styling: despine resets label colors
    ax.tick_params(axis="x", length=0, pad=1.3)
    for t, m in zip(ax.get_xticklabels(), names):
        if m == hero:
            t.set_fontproperties(bold_font(TICK_PT))
            t.set_color(colors.get(m, HERO))
    ax.spines["left"].set_bounds(1, n_m)
    return names


def tradeoff_scatter(ax, order, xs, ys, *, colors, labels, x_step, y_step, hero=None, xerr=None, yerr=None,
                     s: float = 16, pad_frac: float = 0.10, diagonal: bool = True, label: str = "compass") -> None:
    """One point per method; every method drawn at the SAME size (the author rejected a larger hero mark: "let the
    results speak"); the hero is drawn last and its label is bold in its color. A faint dashed diagonal points to
    the better corner (top-right: flip an axis whose low end is good). Error bars, if given, are IQR half-widths
    as (lo, hi) deltas per method. label: "compass" (default; deterministic, fixed 4.5 pt gap, no leaders; the final
    choice for small scatters), "repel" (adjustText; for dense clouds such as volcano plots) or "" for none."""
    x = np.array([xs[m] for m in order], float)
    y = np.array([ys[m] for m in order], float)
    if xerr:                                    # limits include the whiskers, so none is cut by an axis
        x = np.r_[x, [xs[m] - xerr[m][0] for m in xerr], [xs[m] + xerr[m][1] for m in xerr]]
    if yerr:
        y = np.r_[y, [ys[m] - yerr[m][0] for m in yerr], [ys[m] + yerr[m][1] for m in yerr]]
    xp, yp = pad_frac * (np.nanmax(x) - np.nanmin(x) + 1e-9), pad_frac * (np.nanmax(y) - np.nanmin(y) + 1e-9)
    xmin, xmax, ymin, ymax = np.nanmin(x) - xp, np.nanmax(x) + xp, np.nanmin(y) - yp, np.nanmax(y) + yp
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    if diagonal:
        ax.plot([xmin, xmax], [ymin, ymax], color=INK, lw=0.5, ls=(0, (2, 1.6)), alpha=0.25, zorder=1)
    for m in sorted(order, key=lambda k: k == hero):
        for e in (xerr or {}, yerr or {}):
            if m in e and min(e[m]) < 0:
                raise ValueError(f"{m}: the point lies outside its interval; plot the median with an IQR")
        xe = None if not xerr or m not in xerr else np.array(xerr[m], float).reshape(2, 1)
        ye = None if not yerr or m not in yerr else np.array(yerr[m], float).reshape(2, 1)
        if xe is not None or ye is not None:
            ax.errorbar([xs[m]], [ys[m]], xerr=xe, yerr=ye, fmt="none", ecolor=LEADER, elinewidth=0.5,
                        capsize=1.0, capthick=0.4, zorder=4)
        ax.scatter([xs[m]], [ys[m]], s=s, c=[colors[m]], edgecolors="white", linewidths=0.4,
                   zorder=10 if m == hero else 6)
    if label == "repel":
        repel_labels(ax, xs, ys, labels, colors=colors, hero=hero)
    elif label:
        compass_place(ax.figure, ax, ([hero] if hero in order else []) + [m for m in order if m != hero], xs, ys,
                      labels, colors, hero=hero,
                      obstacles=[(xs[m], ys[m] - e[0], xs[m], ys[m] + e[1]) for m, e in (yerr or {}).items()]
                      + [(xs[m] - e[0], ys[m], xs[m] + e[1], ys[m]) for m, e in (xerr or {}).items()])
    ax.set_xticks(nice_ticks(xmin, xmax, x_step))
    ax.set_yticks(nice_ticks(ymin, ymax, y_step))
    despine(ax)


# ---------------------------------------------------------------------------------------------------------------
# Output.

def save_panel(fig, out_dir, name: str, png_dpi: int = 600, svg: bool = True, close: bool = True,
               transparent: bool = True) -> Path:
    """Write name.pdf, name.png (600 dpi) and, by default, name.svg with live text, all at the figure's exact size.
    Never bbox_inches="tight": the composer places panels at fixed mm and needs page size == figure size.
    The ground is transparent by default (prints as white); never save a paper panel on a dark ground."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / name
    kw = dict(bbox_inches=None, pad_inches=0, transparent=transparent)
    fig.savefig(stem.with_suffix(".pdf"), **kw)
    fig.savefig(stem.with_suffix(".png"), dpi=png_dpi, **kw)
    if svg:
        fig.savefig(stem.with_suffix(".svg"), **kw)
    if close:
        plt.close(fig)
    return stem


def _selftest() -> None:
    """Checks of the pure helpers; run `python3 figstyle.py`."""
    assert nice_axis(0, 1700) == [0, 1000, 2000], nice_axis(0, 1700)
    assert nice_axis(0, 0.83) == [0, 0.5, 1.0], nice_axis(0, 0.83)
    assert nice_axis(0, 43) == [0, 20, 40, 60], nice_axis(0, 43)
    r = rank_columns([[0.9, 0.5], [0.7, 0.5], [0.8, 0.1]])
    assert r[:, 0].tolist() == [1, 3, 2] and r[:, 1].tolist() == [1.5, 1.5, 3], r
    assert num(-0.0642, 3) == "−.064" and num(0.642) == ".642"
    CATEGORY["alpha"], ALIASES["Alpha "] = "#0072B2", "alpha"
    assert category_color("Alpha ") == "#0072B2" and category_color("") == UNLABELLED and category_color("typo") == UNKNOWN
    CATEGORY.clear(), ALIASES.clear()


if __name__ == "__main__":
    _selftest()
    apply()
    print("self-test passed;", "figstyle imports; body font resolves to:", resolved_font(), "| bold face file:", bold_font_file())

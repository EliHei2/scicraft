#!/usr/bin/env python3
"""Render an embedding field as RGB maps from a pooled bundle: a zoom ladder or a row of pooling levels.

Stage 2 of the pipeline (pool_lattice.py makes the bundle). Two figures, two color jobs:

  --mode zoom    nested windows over ONE place, coarse to fine. ONE mapping for every panel: the axes are fitted
                 once on the basis level's pooled sites over the WHOLE sample, and the 5/95 stretch is the
                 envelope of every drawn level's whole-sample distribution in that basis. A color then means the
                 same state at every zoom, and zooming in reads as zooming in. Each panel is cropped from that fit.
  --mode levels  one tile per pooling level. Each level gets its OWN basis and stretch, fitted on that level's
                 pooled sites over the whole sample, because the point of the row is that the readout (and with it
                 the color space) changes with the pooling scale. Colors compare within a tile, not across.

Rules built in (each one cost a wrong figure in the source project):
  * PCA after pooling, on normalized (vMF) site directions; every level pooled from the items.
  * fit once on the whole sample, then crop; never refit per crop or per view.
  * axes ranked by spatial autocorrelation (Moran's I on a kNN graph) unless --axes variance: the top-variance
    axis of a per-item field is item identity, which is spatially white and paints noise.
  * stretch at the 5th/95th percentiles (1/99.5 left 85% of units in the muddy middle of each axis); sites below
    --fill of the median occupied count are edge bins: masked, and excluded from the fit and the percentiles.
  * a value floor (0.30) so the darkest color does not read as the ground.
  * the strip over each panel states the unit: the bin size, the pooled width, or the units drawn.
  * every parameter and every number that is not printed goes to the JSON sidecar.
  * outputs are never overwritten: an existing stem stops the run; give the variant a new name.

Usage:
  field_rgb.py --bundle b.npz --table t.npz --mode zoom --windows 0 2000 600 150 --levels p0 p1 p2 item \
      --labels "whole sample" region niche items --out figs/field_zoom_v1
  field_rgb.py --bundle b.npz --mode levels --levels p0 p1 p2 p3 --out figs/field_levels_v1

Dependencies: numpy, scipy, matplotlib (pandas for .parquet/.csv tables).
Adapted from the source project's zoom-grid, ladder figure, cohort sheet and figure-1 tile scripts.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import hsv_to_rgb, rgb_to_hsv  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from scipy.ndimage import uniform_filter  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emb_io import read_table, sha256, unit  # noqa: E402

MM = 25.4
TITLE, AXIS, TICK = 7.0, 6.0, 5.0                     # the only three text tiers (pt, at printed size)
INK, GROUND, ON_TILE = "#000000", "#141416", "#F5F5F7"
LV = [0.5, 1, 2, 5, 10, 15, 20, 25, 50, 75, 80, 85, 90, 95, 98, 99, 99.5]   # quantile curve stored per level


def short(n: float) -> str:
    """Compact count: 1.00B, 12.0M, 400k, 8,000."""
    if n >= 1e9:
        return f"{n / 1e9:.2f}B"
    return f"{n / 1e6:.1f}M" if n >= 1e6 else (f"{n / 1e3:.0f}k" if n >= 1e4 else f"{int(n):,}")


def moran_rank(P: np.ndarray, xy: np.ndarray, seed: int, k: int = 8, n: int = 6000) -> list[float]:
    """Moran's I of each column of P on a k-NN graph of xy (subsampled). Used to RANK axes, never as evidence."""
    smp = np.random.default_rng(seed).choice(len(P), min(n, len(P)), replace=False)
    nb = cKDTree(xy[smp]).query(xy[smp], k=k + 1)[1][:, 1:]
    out = []
    for j in range(P.shape[1]):
        v = P[smp, j] - P[smp, j].mean()
        dd = float((v * v).sum())
        out.append(float((v[:, None] * v[nb]).sum() / (k * dd)) if dd > 0 else 0.0)
    return out


def fit_basis(dirs: np.ndarray, xy: np.ndarray | None, axes: str, seed: int, n_cand: int = 8) -> dict:
    """PCA of normalized pooled directions -> mean, 3 loadings, explained variance, Moran's I of the chosen axes."""
    mu = dirs.mean(0)
    _, sv, vt = np.linalg.svd(dirs - mu, full_matrices=False)
    evr = sv ** 2 / (sv ** 2).sum()
    cand = vt[:n_cand]
    if axes == "moran" and xy is not None and len(dirs) >= 30:
        mi = moran_rank((dirs - mu) @ cand.T, xy, seed)
        sel = list(np.argsort(mi)[::-1][:3])
    else:
        mi = moran_rank((dirs - mu) @ cand.T, xy, seed) if xy is not None and len(dirs) >= 30 else [float("nan")] * len(cand)
        sel = [0, 1, 2]
    return {"mu": mu, "W": cand[sel].T, "axes_rule": axes, "pc_index": [int(s) for s in sel],
            "evr": [round(float(evr[s]), 4) for s in sel], "moran_I": [round(float(mi[s]), 3) for s in sel]}


def to_rgb(P: np.ndarray, lo: np.ndarray, hi: np.ndarray, sat: float, vfloor: float) -> np.ndarray:
    """(..., 3) basis coordinates -> stretched, saturation-lifted RGB with a value floor."""
    c = np.clip((P - lo) / (hi - lo + 1e-12), 0, 1)
    h = rgb_to_hsv(c)
    h[..., 1] = np.clip(h[..., 1] * sat, 0, 1)
    h[..., 2] = vfloor + (1.0 - vfloor) * h[..., 2]
    return hsv_to_rgb(h)


def kbox(pitch: float, width: float) -> int:
    """Sites across a re-pooling box, forced odd: an even box shifts the map half a site against its neighbors."""
    k = max(1, int(round(width / pitch)))
    return k + 1 if k > 1 and k % 2 == 0 else k


def smooth(ij: np.ndarray, ssum: np.ndarray, cnt: np.ndarray, k: int) -> np.ndarray:
    """Re-pool each site over a k x k box of neighbors, count-weighted (pooling scale k*pitch, drawn at pitch)."""
    if k <= 1:
        return ssum
    acc = np.zeros((ij[:, 0].max() + 1, ij[:, 1].max() + 1, ssum.shape[1]), np.float32)
    cn = np.zeros(acc.shape[:2], np.float32)
    acc[ij[:, 0], ij[:, 1]], cn[ij[:, 0], ij[:, 1]] = ssum, cnt
    acc = uniform_filter(acc, size=(k, k, 1), mode="constant")
    cn = uniform_filter(cn, size=k, mode="constant")
    return acc[ij[:, 0], ij[:, 1]] / np.maximum(cn[ij[:, 0], ij[:, 1]], 1e-6)[:, None]


def dot_pt(xy: np.ndarray, span: float, tile_mm: float, fill: float = 1.05) -> float:
    """Marker area (pt^2) from the real spacing of the points inside the drawn window, not from a fixed size."""
    if not len(xy):
        return 0.35 ** 2
    b = max(span / 40.0, 1e-9)
    ij = np.floor((xy - xy.min(0)) / b).astype(np.int64)
    occ = len(np.unique(ij[:, 0] * 1_000_003 + ij[:, 1])) * b ** 2
    pw = tile_mm / MM * 72.0
    return float(np.clip(fill * np.sqrt(occ / len(xy)) / span * pw, 0.32, 0.11 * pw)) ** 2


def scalebar(ax, win, units: str) -> float:
    """A 1/2/5 x decade bar near a fifth of the panel, white with a dark stroke, bottom right."""
    x0, x1, y0, y1 = win
    span = x1 - x0
    dec = 10.0 ** np.floor(np.log10(max(span / 5.0, 1e-9)))
    L = float(min((1.0, 2.0, 5.0, 10.0), key=lambda m: abs(m * dec - span / 5.0)) * dec)
    xb, yb = x1 - 0.06 * span - L, y0 + 0.06 * span             # y grows upward: y0 is the bottom edge
    ax.plot([xb, xb + L], [yb, yb], color=ON_TILE, lw=1.5, solid_capstyle="butt", zorder=8,
            path_effects=[pe.withStroke(linewidth=2.6, foreground=GROUND)])
    txt = f"{L / 1000:g} mm" if (units == "um" and L >= 1000) else f"{L:g} {'µm' if units == 'um' else units}"
    ax.text(xb + L / 2, yb + 0.025 * span, txt, ha="center", va="bottom", fontsize=TICK, color=ON_TILE, zorder=8,
            path_effects=[pe.withStroke(linewidth=1.7, foreground=GROUND)])
    return L


def nest(pts: np.ndarray, score: np.ndarray, parent, span: float, mixed: bool, occ_frac: float = 0.7):
    """One child window of width span inside parent, stride span/4. Placed on label entropy (mixed) or on the
    spread of field scores; either way only among windows holding >= occ_frac of the fullest one's points."""
    step = span / 4.0
    cand = []
    for x0 in np.arange(parent[0], max(parent[1] - span, parent[0]) + 1e-9, step):
        inx = (pts[:, 0] >= x0) & (pts[:, 0] < x0 + span)
        for y0 in np.arange(parent[2], max(parent[3] - span, parent[2]) + 1e-9, step):
            m = inx & (pts[:, 1] >= y0) & (pts[:, 1] < y0 + span)
            n = int(m.sum())
            v = 0.0
            if n >= 8:
                if mixed:
                    q = np.bincount(score[m]) / n
                    q = q[q > 0]
                    v = float(-(q * np.log(q)).sum())
                else:
                    v = float(score[m].std(0).sum())
            cand.append((n, v, (x0, x0 + span, y0, y0 + span)))
    nmax = max(c[0] for c in cand)
    full = [c for c in cand if c[0] >= occ_frac * nmax]
    return max(full, key=lambda c: c[1])[2]


def style() -> None:
    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
                         "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none", "text.color": INK})
    warnings.filterwarnings("ignore", message="findfont")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render a pooled embedding field as a zoom ladder (one shared "
                                            "mapping) or a row of pooling levels (one basis per level).")
    p.add_argument("--bundle", required=True, type=Path, help="npz from pool_lattice.py")
    p.add_argument("--table", type=Path, default=None, help="the item table (needed for 'item' panels, "
                   "item counts and --place-key)")
    p.add_argument("--mode", choices=("zoom", "levels"), default="zoom")
    p.add_argument("--levels", nargs="+", required=True, help="per panel: p0, p1, ... (lattice), unit, item")
    p.add_argument("--windows", nargs="*", type=float, default=None,
                   help="zoom: nested window widths, 0 = whole sample (one per panel)")
    p.add_argument("--labels", nargs="*", default=None, help="column titles, one per panel")
    p.add_argument("--smooth", nargs="*", type=float, default=None,
                   help="per panel: re-pool lattice sites over this width at render (0 = none)")
    p.add_argument("--basis-level", default=None, help="zoom: level the shared axes are fitted on "
                   "(default: the first lattice level)")
    p.add_argument("--axes", choices=("moran", "variance"), default="moran")
    p.add_argument("--lvl", type=float, default=5.0, help="stretch percentile: lvl and 100-lvl (default 5)")
    p.add_argument("--fill", type=float, default=0.10, help="edge mask: sites under this fraction of the median "
                   "occupied count are masked and left out of the fit")
    p.add_argument("--min-count", type=int, default=3)
    p.add_argument("--value-floor", type=float, default=0.30)
    p.add_argument("--sat", type=float, default=1.15)
    p.add_argument("--stretch", choices=("shared", "panel"), default="shared",
                   help="zoom: 'panel' re-takes the percentiles inside each panel (axes stay shared; shades are "
                        "then not comparable between panels)")
    p.add_argument("--center", nargs=2, type=float, default=None, help="zoom: center of the nested windows")
    p.add_argument("--place-key", default=None, help="zoom: categorical key in the table; windows are placed "
                   "where its labels mix most (an independent annotation)")
    p.add_argument("--item-noun", default="items")
    p.add_argument("--unit-noun", default="units")
    p.add_argument("--no-counts", action="store_true", help="drop counts from the strips (use when the table "
                   "is a subsample: its counts would report the subsample)")
    p.add_argument("--name", default="", help="sample name, set vertically at the left")
    p.add_argument("--width-mm", type=float, default=183.0)
    p.add_argument("--emb-prefix", default="emb_")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", required=True, type=Path, help="output stem; .png .pdf .json are written beside it")
    a = p.parse_args(argv)

    outs = [a.out.with_suffix(s) for s in (".png", ".pdf", ".json")]
    hit = [str(o) for o in outs if o.exists()]
    if hit:
        raise SystemExit(f"refusing to overwrite {hit}: a figure the author has seen keeps its name. "
                         f"Write the variant under a new stem (for example {a.out.name}_v2).")
    npan = len(a.levels)
    labels = a.labels or a.levels
    smooths = a.smooth or [0.0] * npan
    if len(labels) != npan or len(smooths) != npan:
        p.error("--labels and --smooth need one value per panel")
    B = dict(np.load(a.bundle, allow_pickle=False))
    pitches = list(B["pitches"])
    units = str(B["units"])
    lat = [lv for lv in a.levels if lv.startswith("p")]
    for lv in a.levels:
        if lv.startswith("p") and f"{lv}_sum" not in B:
            raise SystemExit(f"level {lv} not in bundle (has {len(pitches)} lattice levels)")
        if lv == "unit" and "u_sum" not in B:
            raise SystemExit("bundle has no unit level (pool with --unit-key)")
        if lv == "unit" and "u_ctr" not in B:
            raise SystemExit("unit level has no coordinates")
    need_table = "item" in a.levels or a.place_key or (a.table is not None)
    T = read_table(a.table, a.emb_prefix, [a.place_key] if a.place_key else []) if need_table and a.table else None
    if ("item" in a.levels or a.place_key) and T is None:
        p.error("'item' panels and --place-key need --table")

    def level_pop(lv: str):
        """(centers, normalized directions, counts, kept mask) of a level over the whole sample."""
        if lv == "unit":
            c = B["u_cnt"]
            return B["u_ctr"], unit(B["u_sum"]), c, c >= a.min_count
        c = B[f"{lv}_cnt"]
        thr = max(a.min_count, a.fill * float(np.median(c[c > 0])))
        return B[f"{lv}_ctr"], unit(B[f"{lv}_sum"]), c, c >= thr

    rng = np.random.default_rng(a.seed)
    item_dirs = item_xy = None
    if T is not None:
        item_xy, item_dirs = T["xy"], unit(T["emb"])
    side = {"figure": a.mode, "bundle": a.bundle.name, "bundle_sha256": sha256(a.bundle),
            "table": a.table.name if a.table else None, "table_sha256": sha256(a.table) if a.table else None,
            "command": " ".join(sys.argv), "seed": a.seed, "stretch_percentiles": [a.lvl, 100 - a.lvl],
            "fill_mask_fraction": a.fill, "value_floor": a.value_floor, "saturation": a.sat,
            "fit_population": "whole sample, edge-masked sites; crops are colored from this fit", "panels": []}

    def stretch_of(P: np.ndarray):
        return np.percentile(P, a.lvl, 0), np.percentile(P, 100 - a.lvl, 0)

    def item_sample(n: int = 500_000) -> np.ndarray:
        return item_dirs if len(item_dirs) <= n else item_dirs[rng.choice(len(item_dirs), n, replace=False)]

    # ---- color maps --------------------------------------------------------------------------------------
    maps: dict[str, dict] = {}
    if a.mode == "zoom":
        bl = a.basis_level or (lat[0] if lat else "unit" if "unit" in a.levels else None)
        if bl is None:
            raise SystemExit("zoom needs a lattice or unit level to fit the shared axes on")
        ctr, dirs, cnt, keep = level_pop(bl)
        basis = fit_basis(dirs[keep], ctr[keep], a.axes, a.seed)
        env_lo, env_hi, per = [], [], {}
        for lv in dict.fromkeys(a.levels):
            if lv == "item":
                P = (item_sample() - basis["mu"]) @ basis["W"]
            else:
                c2, d2, _, k2 = level_pop(lv)
                P = (d2[k2] - basis["mu"]) @ basis["W"]
            lo, hi = stretch_of(P)
            per[lv] = {"lo": lo, "hi": hi, "q": np.percentile(P, LV, 0)}
            env_lo.append(lo)
            env_hi.append(hi)
        lo, hi = np.minimum.reduce(env_lo), np.maximum.reduce(env_hi)
        for lv in a.levels:
            maps[lv] = {**basis, "lo": lo, "hi": hi}
        side["basis"] = {"level": bl, "pitch": (pitches[int(bl[1:])] if bl.startswith("p") else "unit"),
                         "axes_rule": basis["axes_rule"], "pc_index": basis["pc_index"], "evr": basis["evr"],
                         "moran_I": basis["moran_I"], "n_sites_fit": int(keep.sum()),
                         "shared_across_panels": True,
                         "stretch": "envelope of each drawn level's %g/%g percentiles in the shared basis"
                                    % (a.lvl, 100 - a.lvl),
                         "lo": [round(float(v), 4) for v in lo], "hi": [round(float(v), 4) for v in hi],
                         "quantile_levels": LV,
                         "quantiles": {k: np.round(v["q"], 4).tolist() for k, v in per.items()}}
    else:
        side["basis"] = {"shared_across_panels": False, "per_level": {}}
        for lv in dict.fromkeys(a.levels):
            if lv == "item":
                d = item_sample()
                b = fit_basis(d, None, "variance", a.seed)
                P = (d - b["mu"]) @ b["W"]
                nfit = len(d)
            else:
                ctr, dirs, cnt, keep = level_pop(lv)
                b = fit_basis(dirs[keep], ctr[keep], a.axes, a.seed)
                P = (dirs[keep] - b["mu"]) @ b["W"]
                nfit = int(keep.sum())
            lo, hi = stretch_of(P)
            maps[lv] = {**b, "lo": lo, "hi": hi}
            side["basis"]["per_level"][lv] = {"axes_rule": b["axes_rule"], "pc_index": b["pc_index"],
                                              "evr": b["evr"], "moran_I": b["moran_I"], "n_fit": nfit,
                                              "lo": np.round(lo, 4).tolist(), "hi": np.round(hi, 4).tolist(),
                                              "quantile_levels": LV, "quantiles": np.round(
                                                  np.percentile(P, LV, 0), 4).tolist()}

    # ---- windows ------------------------------------------------------------------------------------------
    ext = B["extent"] if "extent" in B else None
    if ext is None:
        raise SystemExit("bundle has no coordinates; use project_items.py for tables without space")
    sq = float(max(ext[2] - ext[0], ext[3] - ext[1])) / 2.0
    c0 = ((ext[0] + ext[2]) / 2.0, (ext[1] + ext[3]) / 2.0)
    whole = (c0[0] - sq, c0[0] + sq, c0[1] - sq, c0[1] + sq)
    if a.mode == "levels":
        wins = [whole] * npan
        placed = "whole sample in every tile"
    else:
        widths = a.windows if a.windows is not None else [0.0] * npan
        if len(widths) != npan:
            p.error("--windows needs one width per panel")
        wins = []
        if a.place_key:
            pts, lab = item_xy, np.unique(T[a.place_key], return_inverse=True)[1]
            if len(pts) > 200_000:
                s = rng.choice(len(pts), 200_000, replace=False)
                pts, lab = pts[s], lab[s]
            placed = f"annotation: windows where '{a.place_key}' labels mix most"
        else:
            ctr, dirs, _, keep = level_pop(lat[0] if lat else "unit")
            pts, lab = ctr[keep], (dirs[keep] - maps[a.levels[0]]["mu"]) @ maps[a.levels[0]]["W"]
            placed = ("given center" if a.center else
                      "field: windows placed on the spread of the field's own scores (no independent "
                      "annotation); the deep panels show where the field claims structure, which is not evidence")
        for i, w in enumerate(widths):
            if w <= 0:
                wins.append(whole)
            elif a.center:
                wins.append((a.center[0] - w / 2, a.center[0] + w / 2, a.center[1] - w / 2, a.center[1] + w / 2))
            else:
                wins.append(nest(pts, lab, wins[-1] if wins else whole, w, mixed=bool(a.place_key)))
    side["crops_placed_on"] = placed

    # ---- figure -------------------------------------------------------------------------------------------
    style()
    left, right, gap, top, hdr, bot = (6.0 if a.name else 2.0), 2.0, 2.0, 2.0, 7.0, 2.0
    tile = (a.width_mm - left - right - (npan - 1) * gap) / npan
    H = top + hdr + tile + bot
    fig = plt.figure(figsize=(a.width_mm / MM, H / MM))
    for i, (lv, win) in enumerate(zip(a.levels, wins)):
        x = left + i * (tile + gap)
        ax = fig.add_axes([x / a.width_mm, bot / H, tile / a.width_mm, tile / H])
        ax.set_facecolor(GROUND)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor(INK)
            s.set_linewidth(0.5)
        m = maps[lv]
        x0, x1, y0, y1 = win
        span = x1 - x0
        rec: dict = {"panel": i, "label": labels[i], "level": lv, "window": [float(v) for v in win]}
        if lv.startswith("p"):
            pitch = float(pitches[int(lv[1:])])
            ctr, ij, cnt = B[f"{lv}_ctr"], B[f"{lv}_ij"], B[f"{lv}_cnt"]
            _, _, _, keep = level_pop(lv)
            k = kbox(pitch, smooths[i]) if smooths[i] > 0 else 1
            dirs = unit(smooth(ij, B[f"{lv}_sum"], cnt.astype(np.float32), k))
            rgb = to_rgb((dirs - m["mu"]) @ m["W"], m["lo"], m["hi"], a.sat, a.value_floor)
            if a.stretch == "panel" and a.mode == "zoom":
                inw = keep & (ctr[:, 0] >= x0) & (ctr[:, 0] < x1) & (ctr[:, 1] >= y0) & (ctr[:, 1] < y1)
                if inw.sum() > 32:
                    lo, hi = stretch_of(((dirs - m["mu"]) @ m["W"])[inw])
                    rgb = to_rgb((dirs - m["mu"]) @ m["W"], lo, hi, a.sat, a.value_floor)
            img = np.zeros((ij[:, 1].max() + 1, ij[:, 0].max() + 1, 4), np.float32)
            img[ij[keep, 1], ij[keep, 0], :3] = rgb[keep]
            img[ij[keep, 1], ij[keep, 0], 3] = 1.0
            org = B["origin"]
            ax.imshow(img, extent=(org[0], org[0] + img.shape[1] * pitch, org[1], org[1] + img.shape[0] * pitch),
                      origin="lower", interpolation="nearest", zorder=2)
            inw = keep & (ctr[:, 0] >= x0) & (ctr[:, 0] < x1) & (ctr[:, 1] >= y0) & (ctr[:, 1] < y1)
            pooled = k * pitch
            rec.update({"pitch": pitch, "pooled_width": pooled, "box_sites": k, "sites_drawn": int(inw.sum()),
                        "items_behind": int(cnt[inw].sum()), "edge_sites_masked": int((~keep).sum())})
            what = f"{pooled:g} {'µm' if units == 'um' else units} " + ("bins" if k == 1 else "pooled")
            n_items = int(cnt[inw].sum())
        elif lv == "unit":
            ctr, dirs, cnt, keep = level_pop("unit")
            inw = keep & (ctr[:, 0] >= x0) & (ctr[:, 0] < x1) & (ctr[:, 1] >= y0) & (ctr[:, 1] < y1)
            rgb = to_rgb((dirs[inw] - m["mu"]) @ m["W"], m["lo"], m["hi"], a.sat, a.value_floor)
            ax.scatter(ctr[inw, 0], ctr[inw, 1], c=rgb, s=dot_pt(ctr[inw], span, tile), marker="o",
                       linewidths=0, rasterized=True, zorder=2)
            n_items = int(cnt[inw].sum())
            rec.update({"units_drawn": int(inw.sum()), "items_behind": n_items})
            what = f"{short(int(inw.sum()))} {a.unit_noun}"
        else:
            inw = ((item_xy[:, 0] >= x0) & (item_xy[:, 0] < x1) & (item_xy[:, 1] >= y0) & (item_xy[:, 1] < y1))
            idx = np.flatnonzero(inw)
            rgb = to_rgb((item_dirs[idx] - m["mu"]) @ m["W"], m["lo"], m["hi"], a.sat, a.value_floor)
            order = rng.permutation(len(idx))      # random draw order: painted area tracks abundance
            ax.scatter(item_xy[idx[order], 0], item_xy[idx[order], 1], c=rgb[order],
                       s=dot_pt(item_xy[idx], span, tile), marker="o", linewidths=0, rasterized=True, zorder=2)
            n_items = len(idx)
            rec.update({"items_drawn": n_items})
            what = "no pooling"
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        if a.mode == "zoom" and i + 1 < npan and wins[i + 1] != win:
            nx0, nx1, ny0, ny1 = wins[i + 1]
            ax.add_patch(Rectangle((nx0, ny0), nx1 - nx0, ny1 - ny0, fill=False, ec=ON_TILE, lw=0.9, zorder=6))
        rec["scale_bar"] = scalebar(ax, win, units)
        strip = what if a.no_counts else f"{short(n_items)} {a.item_noun} - {what}"
        rec["strip"] = strip
        ax.text(0.5, 1.02, strip, transform=ax.transAxes, ha="center", va="bottom", fontsize=TICK, color=INK)
        ax.set_title(labels[i], fontsize=TITLE, color=INK, pad=9.5, fontweight="medium")
        side["panels"].append(rec)
    if a.name:
        fig.text(2.0 / a.width_mm, (bot + tile / 2) / H, a.name, rotation=90, ha="center", va="center",
                 fontsize=AXIS, fontweight="bold", color=INK)
    rel = json.loads(a.bundle.with_suffix(".json").read_text()) if a.bundle.with_suffix(".json").exists() else {}
    side["reliability"] = [{k: lv.get(k) for k in ("level", "pitch", "split_half_r", "split_half_null",
                                                  "units_in_r", "rel_scope")} for lv in rel.get("levels", [])]
    side["reliability_reads"] = ("split-half r is a floor: the value survives resampling the items; it does not "
                                 "show that a scale carries independent information")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outs[0], dpi=600, facecolor="white")
    fig.savefig(outs[1], facecolor="white")
    outs[2].write_text(json.dumps(side, indent=1, default=float))
    print(f"[field_rgb] wrote {outs[0].name}, {outs[1].name}, {outs[2].name}; basis moran_I "
          f"{side['basis'].get('moran_I', '(per level)')}; crops placed on: {placed.split(':')[0]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

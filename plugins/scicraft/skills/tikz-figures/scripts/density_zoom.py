#!/usr/bin/env python3
"""Generate a multiscale density zoom (domain -> window -> points -> one point's kNN ball) as TikZ.

The figure is driven by ONE point field. Every zoom level is a crop of that same field,
so the clump seen in one frame is the clump magnified in the next:

  level 1  the whole domain as a density field (KDE, three nested filled contour bands
           per category, core drawn last)
  level 2  a window of level 1, still drawn as density
  level 3  a window of level 2, now the individual points (exactly the points inside it)
  level 4  one chosen point u, its k nearest neighbors computed over the SAME field,
           thin ink spokes, a light grey ring, and the label z_u with no leader line

The ego point u is chosen, not taken at random: among points in the central part of the
domain whose neighbors surround them (largest angular gap below --max-gap radians), the
one whose k-th neighbor distance is closest to the --radius-quantile of all candidates
(roomy but not sparse).

Input is either a CSV with columns x,y[,label] (your real data or the output of your
real code), or a seeded synthetic field of clustered, anisotropic lumps per category.
The same seed and input always give the same figure.

Outputs in --out:
  frag_L1.tex .. frag_L4.tex   TikZ fragments in local frame coordinates [-1,1]^2
  body.tex                     the four frames, zoom boxes and dashed focus lines,
                               with \\input{frag_Lk.tex} (use while iterating)
  facts.json                   every number the figure shows or depends on
  fig.tex                      only with --preamble: a self-contained figure with the
                               preamble on top and the fragments inlined (deliver this)

Needs: numpy, scipy (gaussian_filter, cKDTree) and contourpy (installed with matplotlib).

Usage:
    python3 density_zoom.py --out zoom/ --preamble ../assets/preamble.tex
    python3 density_zoom.py --points field.csv --out zoom/ --colors accent,contrast,slate
    python3 density_zoom.py --out zoom/ --seed 3 --k 6 --zoom 3,4 --frame-cm 3.2
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from contourpy import FillType, contour_generator
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

LEVELS = [(0.10, 0.22), (0.36, 0.42), (0.66, 0.72)]  # (relative density, fill opacity), core last


def synthetic_field(n: int, n_cat: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Clustered, anisotropic lumps; each category recurs in several separated places."""
    rng = np.random.default_rng(seed)
    pts, lab = [], []
    per = n // n_cat
    for c in range(n_cat):
        n_lumps = 3
        centers = rng.uniform(-0.75, 0.75, size=(n_lumps, 2))
        for j in range(n_lumps):
            m = per // n_lumps
            ang = rng.uniform(0, math.pi)
            sx, sy = rng.uniform(0.07, 0.20), rng.uniform(0.04, 0.10)
            rot = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
            p = rng.normal(size=(m, 2)) * [sx, sy] @ rot.T + centers[j]
            pts.append(p)
            lab += [c] * m
    pts = np.vstack(pts)
    keep = np.all(np.abs(pts) <= 0.97, axis=1)
    return pts[keep], np.array(lab)[keep]


def read_field(path: Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or "x" not in rows[0] or "y" not in rows[0]:
        raise SystemExit(f"{path}: needs a header with columns x,y and optionally label")
    xy = np.array([[float(r["x"]), float(r["y"])] for r in rows])
    names = [r.get("label", "0") or "0" for r in rows]
    cats = sorted(set(names), key=lambda s: (names.index(s)))
    lab = np.array([cats.index(s) for s in names])
    ctr = (xy.max(0) + xy.min(0)) / 2
    half = (xy.max(0) - xy.min(0)).max() / 2 or 1.0
    return (xy - ctr) / half * 0.95, lab, cats  # fit [-0.95, 0.95], aspect kept


def kde(p: np.ndarray, bw: float, grid: int) -> np.ndarray:
    h = np.zeros((grid, grid))
    ix = np.clip(((p[:, 0] + 1) / 2 * (grid - 1)).astype(int), 0, grid - 1)
    iy = np.clip(((p[:, 1] + 1) / 2 * (grid - 1)).astype(int), 0, grid - 1)
    np.add.at(h, (iy, ix), 1)
    return gaussian_filter(h, sigma=bw * grid / 2)


def angular_maxgap(field: np.ndarray, i: int, knn: np.ndarray) -> float:
    p = field[i]
    angs = sorted(math.atan2(field[j][1] - p[1], field[j][0] - p[0]) for j in knn)
    k = len(angs)
    return max((angs[(a + 1) % k] - angs[a]) % (2 * math.pi) for a in range(k))  # small = surrounded


def to_local(pts: np.ndarray, center: np.ndarray, half: float) -> np.ndarray:
    return (np.asarray(pts) - center) / half


def window(center: np.ndarray, half: float) -> tuple[np.ndarray, float]:
    half = min(half, 1.0)
    c = np.clip(center, -1 + half, 1 - half)  # keep the window inside the domain
    return c, half


def bands(dens: list[np.ndarray], colors: list[str], center: np.ndarray, half: float, grid: int) -> list[str]:
    """Filled density bands of every category inside a window, in local coordinates."""
    xs = np.linspace(-1, 1, grid)
    i0 = max(0, int(np.searchsorted(xs, center[0] - half)) - 1)
    i1 = min(grid, int(np.searchsorted(xs, center[0] + half)) + 2)
    j0 = max(0, int(np.searchsorted(xs, center[1] - half)) - 1)
    j1 = min(grid, int(np.searchsorted(xs, center[1] + half)) + 2)
    sx, sy = xs[i0:i1], xs[j0:j1]
    out = []
    for d, col in zip(dens, colors):
        sub = d[j0:j1, i0:i1]
        gen = contour_generator(sx, sy, sub, fill_type=FillType.OuterOffset)
        for lev, op in LEVELS:
            polys, _ = gen.filled(lev, np.inf)
            for poly in polys:
                if len(poly) < 8:
                    continue
                loc = to_local(poly[::2], center, half)
                path = " ".join(f"({x:.3f},{y:.3f})" for x, y in loc)  # SPACE separated
                out.append(f"\\fill[{col}, opacity={op}] plot[smooth cycle, tension=0.6] coordinates {{{path}}};")
    return out


def frame_block(idx: int, x0: float, s: float, frag: str, base_fill: str, inline: dict | None) -> str:
    body = inline[frag] if inline else f"\\input{{{frag}}}"
    return (f"% ---- level {idx}\n"
            f"\\begin{{scope}}[shift={{({x0:.3f},0)}}, x={s:.4f}cm, y={s:.4f}cm]\n"
            f"  \\begin{{scope}}\n    \\clip (-1,-1) rectangle (1,1);\n"
            f"    \\fill[{base_fill}] (-1,-1) rectangle (1,1);\n    {body}\n  \\end{{scope}}\n"
            f"  \\draw[frame] (-1,-1) rectangle (1,1);\n\\end{{scope}}\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Multiscale density zoom figure from one point field, as TikZ.")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--points", help="CSV with x,y[,label]; default is a seeded synthetic field")
    ap.add_argument("--seed", type=int, default=7, help="seed for the synthetic field (default 7)")
    ap.add_argument("--n", type=int, default=900, help="synthetic field size (default 900)")
    ap.add_argument("--categories", type=int, default=3, help="synthetic categories (default 3)")
    ap.add_argument("--colors", default="accent,contrast,slate",
                    help="TikZ color per category, from the preamble (default accent,contrast,slate)")
    ap.add_argument("--k", type=int, default=6, help="neighbors in the ego ball (default 6)")
    ap.add_argument("--bw", type=float, default=0.05, help="KDE bandwidth as a fraction of the domain (0.05)")
    ap.add_argument("--grid", type=int, default=720, help="KDE grid size (default 720)")
    ap.add_argument("--zoom", default="3,4",
                    help="window ratios level2/level3 and level3/level4 (default 3,4)")
    ap.add_argument("--pad", type=float, default=1.4, help="level-4 window = pad x ego radius (default 1.4)")
    ap.add_argument("--max-gap", type=float, default=2.4, help="largest angular gap of the ego's neighbors, rad")
    ap.add_argument("--radius-quantile", type=float, default=0.45, help="target quantile of the ego radius")
    ap.add_argument("--frame-cm", type=float, default=3.0, help="frame side in cm (default 3.0)")
    ap.add_argument("--preamble", help="write a self-contained fig.tex with this preamble on top")
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    colors = [c.strip() for c in args.colors.split(",") if c.strip()]
    if args.points:
        field, lab, cat_names = read_field(Path(args.points))
        source = {"points": Path(args.points).name}
    else:
        field, lab = synthetic_field(args.n, args.categories, args.seed)
        cat_names = [str(c) for c in range(args.categories)]
        source = {"synthetic": True, "seed": args.seed, "n_requested": args.n}
    n_cat = int(lab.max()) + 1
    if len(colors) < n_cat:
        raise SystemExit(f"{n_cat} categories but only {len(colors)} colors in --colors")
    if len(field) <= args.k + 1:
        raise SystemExit("too few points for the requested k")

    # density per category, normalized by its own maximum (relative levels)
    dens = []
    for c in range(n_cat):
        d = kde(field[lab == c], args.bw, args.grid)
        dens.append(d / d.max() if d.max() > 0 else d)

    # choose the ego: central, surrounded, radius near the target quantile
    tree = cKDTree(field)
    dist, idx = tree.query(field, k=args.k + 1)
    rk_all = dist[:, -1]
    cand = [i for i in range(len(field)) if np.all(np.abs(field[i]) < 0.6)]
    if not cand:
        cand = list(range(len(field)))
    gaps = {i: angular_maxgap(field, i, idx[i, 1:]) for i in cand}
    good = [i for i in cand if gaps[i] < args.max_gap] or cand
    target = float(np.quantile(rk_all[good], args.radius_quantile))
    ego = min(good, key=lambda i: (abs(rk_all[i] - target), i))
    rk = float(rk_all[ego])
    nbrs = idx[ego, 1:]

    f2, f3 = (float(v) for v in args.zoom.split(","))
    c4, h4 = window(field[ego], rk * args.pad)
    c3, h3 = window(field[ego], h4 * f3)
    c2, h2 = window(field[ego], h3 * f2)
    c1, h1 = np.zeros(2), 1.0

    frags: dict[str, str] = {}
    frags["frag_L1.tex"] = "\n".join(bands(dens, colors, c1, h1, args.grid))
    frags["frag_L2.tex"] = "\n".join(bands(dens, colors, c2, h2, args.grid))
    in3 = np.all(np.abs(field - c3) <= h3, axis=1)
    loc3 = to_local(field[in3], c3, h3)
    frags["frag_L3.tex"] = "\n".join(
        f"\\fill[{colors[l]}] ({x:.3f},{y:.3f}) circle (0.8pt);" for (x, y), l in zip(loc3, lab[in3]))
    in4 = np.all(np.abs(field - c4) <= h4, axis=1)
    lines4 = []
    ego_l = to_local(field[ego], c4, h4)
    lines4.append(f"\\draw[egoring] ({ego_l[0]:.3f},{ego_l[1]:.3f}) circle ({rk / h4:.3f});")
    for j in np.where(in4)[0]:
        if j == ego or j in nbrs:
            continue
        x, y = to_local(field[j], c4, h4)
        lines4.append(f"\\fill[{colors[lab[j]]}, opacity=0.45] ({x:.3f},{y:.3f}) circle (0.8pt);")
    nb_local = to_local(field[nbrs], c4, h4)
    for (x, y) in nb_local:
        lines4.append(f"\\draw[egospoke] ({ego_l[0]:.3f},{ego_l[1]:.3f}) -- ({x:.3f},{y:.3f});")
    for (x, y), j in zip(nb_local, nbrs):
        lines4.append(f"\\fill[{colors[lab[j]]}] ({x:.3f},{y:.3f}) circle (1.1pt);")  # own category color
    lines4.append(f"\\fill[{colors[lab[ego]]}] ({ego_l[0]:.3f},{ego_l[1]:.3f}) circle (1.5pt);")
    # label in the middle of the widest angular gap between spokes, beside the point
    angs = sorted(math.atan2(y - ego_l[1], x - ego_l[0]) for x, y in nb_local)
    lgaps = [((angs[(a + 1) % len(angs)] - angs[a]) % (2 * math.pi), a) for a in range(len(angs))]
    width, a = max(lgaps)
    mid = angs[a] + width / 2
    anchors = ["west", "south west", "south", "south east", "east", "north east", "north", "north west"]
    anchor = anchors[int(round(((mid + math.pi) % (2 * math.pi)) / (math.pi / 4))) % 8]
    anchor = anchors[(anchors.index(anchor) + 4) % 8]  # anchor on the side facing the point
    lx, ly = ego_l[0] + 0.12 * math.cos(mid), ego_l[1] + 0.12 * math.sin(mid)
    lines4.append(f"\\node[anchor={anchor}, inner sep=1pt, font=\\figfont\\figL] at "
                  f"({lx:.3f},{ly:.3f}) {{$z_u$}};  % no leader line")
    frags["frag_L4.tex"] = "\n".join(lines4)
    for name, text in frags.items():
        (out / name).write_text(text + "\n")

    # body: four frames, zoom boxes on each parent, dashed focus lines to the next frame
    s = args.frame_cm / 2
    step = 1.45 * args.frame_cm
    xs = [i * step for i in range(4)]
    wins = [(c1, h1), (c2, h2), (c3, h3), (c4, h4)]

    def body(inline: dict | None) -> str:
        parts = ["\\begin{tikzpicture}[base]"]
        base_fill = f"{colors[0]}!8"
        for k, name in enumerate(["frag_L1.tex", "frag_L2.tex", "frag_L3.tex", "frag_L4.tex"]):
            parts.append(frame_block(k + 1, xs[k], s, name, base_fill, inline))
        for k in range(3):  # zoom box of level k+2 drawn on level k+1
            (pc, ph), (cc, ch) = wins[k], wins[k + 1]
            lo = to_local(cc - ch, pc, ph)
            hi = to_local(cc + ch, pc, ph)
            gx0, gy0 = xs[k] + lo[0] * s, lo[1] * s
            gx1, gy1 = xs[k] + hi[0] * s, hi[1] * s
            parts.append(f"\\draw[ink, line width=0.5pt] ({gx0:.3f},{gy0:.3f}) rectangle ({gx1:.3f},{gy1:.3f});")
            nx = xs[k + 1] - s
            parts.append(f"\\draw[frustum] ({gx1:.3f},{gy1:.3f}) -- ({nx:.3f},{s:.3f});")
            parts.append(f"\\draw[frustum] ({gx1:.3f},{gy0:.3f}) -- ({nx:.3f},{-s:.3f});")
        parts.append("\\end{tikzpicture}")
        return "\n".join(parts) + "\n"

    (out / "body.tex").write_text(body(None))
    nb_ok = bool(np.all(np.abs(nb_local) <= 1.0))
    facts = {
        "source": source,
        "n_points": int(len(field)),
        "categories": {cat_names[c] if c < len(cat_names) else str(c): int((lab == c).sum()) for c in range(n_cat)},
        "colors": colors[:n_cat],
        "kde": {"bandwidth": args.bw, "grid": args.grid, "levels": [lv for lv, _ in LEVELS],
                "opacities": [op for _, op in LEVELS]},
        "ego": {"index": int(ego), "world_xy": [round(float(v), 4) for v in field[ego]], "k": args.k,
                "radius": round(rk, 4), "angular_maxgap_rad": round(gaps.get(ego, float("nan")), 3),
                "radius_target_quantile": args.radius_quantile, "candidates": len(cand), "surrounded": len(good)},
        "windows_world": [{"level": i + 1, "center": [round(float(v), 4) for v in c], "half_width": round(float(h), 4)}
                          for i, (c, h) in enumerate(wins)],
        "points_in_level3": int(in3.sum()),
        "neighbors_inside_level4_frame": nb_ok,
    }
    (out / "facts.json").write_text(json.dumps(facts, indent=2) + "\n")

    if args.preamble:
        pre = Path(args.preamble).read_text()
        if "\\begin{document}" not in pre:
            raise SystemExit("--preamble must end with \\begin{document}")
        (out / "fig.tex").write_text(pre.rstrip() + "\n" + body(frags) + "\\end{document}\n")

    print(f"ok  {len(field)} points, {n_cat} categories, ego {ego} (radius {rk:.4f}, "
          f"max gap {gaps.get(ego, float('nan')):.2f} rad), {int(in3.sum())} points at level 3")
    print(f"ok  neighbors inside the level-4 frame: {nb_ok}")
    print(f"ok  wrote {', '.join(sorted(frags))}, body.tex, facts.json" + (", fig.tex" if args.preamble else ""))
    return 0 if nb_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

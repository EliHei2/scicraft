#!/usr/bin/env python3
"""Map an embedding table without coordinates (one vector per row, token, document or dataset) for a picture.

The rules this script enforces, each from a real failure in the source projects:

  1. A 2-D projection (UMAP, t-SNE, PCA-2) is for pictures only. No reported number is computed from projected
     coordinates. Distances, two-sample tests and neighbors are computed in the cleaned, scaled PCA space, which
     is written beside the picture (--pca-out) for that purpose.
  2. Cleaning, scaling, PCA and the projection are fitted ONCE on a clean, balanced reference. Everything else
     (perturbed variants, derived copies, other groups' items, new data) is placed with transform and marked
     'projected', never refitted per variant. Balanced: every item of the smaller group plus an equal-sized
     (minimum 30) deterministic subset of the larger group, so the larger group's variance does not define the
     axes.
  3. Every view (embedding) is evaluated on the same items: with several --view files (concatenated, each block
     scaled to unit total variance) or --common-with files (one map per view), only ids present in all of them
     are kept, and the number dropped from each file is reported.
  4. The picture is points only: no density contours, no mean and SD markers, a full square frame, one marker
     shape per group so no meaning rests on color alone, and one legend.

Input: one or more tables (.csv or .parquet) with an id column, a group column and embedding columns
(prefix --emb-prefix), or .npz with emb plus id and group arrays.

Usage:
  project_items.py --view stats.csv --view model.csv --id dataset --group source --balance-group source \
      --reference-mask clean --out figs/map_v1 [--method umap] [--pca-out figs/map_v1_pca.csv]

  5. A UMAP map gets a PCA twin (<out>_pca.png/.pdf): PCs 1 and 2 of the same fitted space, same colors,
     markers and frame, so a reader can tell structure the projection made from structure the data carry.
  6. The exact inputs of every map are written to <out>_points.csv (id, group, fit role, whether the item entered
     the PCA fit, fit order, and every view's raw feature vector) and hashed in the sidecar, so the map can be
     replotted without rerunning the encoders.

Writes <out>.png, <out>.pdf, <out>.csv (2-D coordinates with a fit_role column), <out>_points.csv, <out>.json
and, for UMAP, <out>_pca.png/.pdf. Refuses to overwrite. Dependencies: numpy, pandas, scikit-learn, matplotlib; umap-learn for --method umap.
Adapted from the source tabular project's analysis module (view cleaner, balanced reference, fitted spaces).
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
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emb_io import sha256  # noqa: E402

MM = 25.4
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*", "<", ">"]
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]


class Cleaner:
    """Signed log (optional), drop columns >max_nan NaN or constant, prune |r|>corr pairs (optional), median
    impute, robust (IQR/1.349) or standard scale, clip. Fitted on the reference only."""

    def __init__(self, slog: bool, corr: float | None, scaler: str, max_nan: float = 0.3, clip: float = 10.0):
        self.slog, self.corr, self.scaler, self.max_nan, self.clip = slog, corr, scaler, max_nan, clip

    def _pre(self, X):
        X = np.asarray(X, np.float64).copy()
        X[~np.isfinite(X)] = np.nan
        return np.sign(X) * np.log1p(np.abs(X)) if self.slog else X

    def fit(self, X):
        Z = self._pre(X)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            keep = np.isnan(Z).mean(0) <= self.max_nan
            med = np.nanmedian(Z, axis=0)
            Zi = np.where(np.isnan(Z), med, Z)
        keep &= Zi.std(0) > 1e-9
        idx = np.flatnonzero(keep)
        if self.corr is not None and idx.size > 1:
            C = np.abs(np.corrcoef(Zi[:, idx], rowvar=False))
            np.fill_diagonal(C, 0)
            drop: set[int] = set()
            for i in range(idx.size):
                if i not in drop:
                    drop.update(int(j) for j in np.flatnonzero(C[i] > self.corr) if j > i)
            idx = np.array([c for k, c in enumerate(idx) if k not in drop], int)
        self.idx, self.med = idx, med[idx]
        Zs = Zi[:, idx]
        if self.scaler == "robust":
            q75, q25 = np.percentile(Zs, [75, 25], axis=0)
            sc = np.where((q75 - q25) / 1.349 > 1e-9, (q75 - q25) / 1.349, Zs.std(0))
            self.center = np.median(Zs, 0)
        else:
            sc, self.center = Zs.std(0), Zs.mean(0)
        self.scale = np.where(sc > 1e-9, sc, 1.0)
        return self

    def transform(self, X):
        Z = self._pre(X)[:, self.idx]
        Z = np.where(np.isnan(Z), self.med, Z)
        return np.clip((Z - self.center) / self.scale, -self.clip, self.clip)


def read_view(path: Path, id_col: str, prefix: str, extra: list[str]):
    import pandas as pd
    if path.suffix == ".npz":
        d = np.load(path, allow_pickle=False)
        df = pd.DataFrame(np.asarray(d["emb"]), columns=[f"{prefix}{j}" for j in range(d["emb"].shape[1])])
        for k in [id_col, *extra]:
            if k in d:
                df[k] = np.asarray(d[k])
    else:
        df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    if id_col not in df.columns:
        raise SystemExit(f"{path}: no id column {id_col!r}")
    if df[id_col].duplicated().any():
        raise SystemExit(f"{path}: duplicate ids in {id_col!r}")
    return df.set_index(id_col)


def balanced_reference(groups: np.ndarray, seed: int, min_n: int = 30) -> np.ndarray:
    """Indices: every item of the smallest group, plus an equal-sized (>= min_n) deterministic subset of each other."""
    vals, counts = np.unique(groups, return_counts=True)
    k = max(int(counts.min()), min_n)
    rng = np.random.default_rng(seed)
    out = []
    for v in vals:
        ix = np.flatnonzero(groups == v)
        out.append(ix if len(ix) <= k else np.sort(rng.choice(ix, k, replace=False)))
    return np.concatenate(out)


def draw(E: np.ndarray, g: np.ndarray, role: np.ndarray, width_mm: float, title: str, png: Path, pdf: Path):
    """Points only, full square frame, one marker shape and one color per group, projected items open, one legend."""
    cats, counts = np.unique(g, return_counts=True)
    order = cats[np.argsort(-counts, kind="stable")]   # largest group first, translucent; rare groups on top
    fig = plt.figure(figsize=(width_mm / MM, width_mm / MM))
    ax = fig.add_axes([0.04, 0.04, 0.92, 0.86])
    for j, c in enumerate(order):
        m = g == c
        big = counts.max() == m.sum() and len(cats) > 1
        for rl, face in (("fitted", True), ("projected", False)):
            mm = m & (role == rl)
            if mm.any():
                col = OKABE_ITO[j % len(OKABE_ITO)]
                ax.scatter(E[mm, 0], E[mm, 1], s=10 if big else 16, marker=MARKERS[j % len(MARKERS)],
                           facecolors=col if face else "none", edgecolors=col, linewidths=0.6,
                           alpha=0.55 if big else 0.95, label=f"{c}" if rl == "fitted" or not (m & (role == "fitted")).any()
                           else None, zorder=2 + j)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_linewidth(0.6)
        s.set_edgecolor("#111111")
    lo, hi = np.percentile(E, [0.5, 99.5], axis=0)
    c0, half = (lo + hi) / 2, float((hi - lo).max()) / 2 * 1.08
    xlo, xhi = min(c0[0] - half, E[:, 0].min()), max(c0[0] + half, E[:, 0].max())
    ylo, yhi = min(c0[1] - half, E[:, 1].min()), max(c0[1] + half, E[:, 1].max())
    ax.set_xlim(xlo - 0.02 * (xhi - xlo), xhi + 0.02 * (xhi - xlo))   # out-of-reference points stay inside
    ax.set_ylim(ylo - 0.02 * (yhi - ylo), yhi + 0.02 * (yhi - ylo))
    hs, ls = ax.get_legend_handles_labels()
    if (role == "projected").any():               # open markers need their own key
        from matplotlib.lines import Line2D
        hs.append(Line2D([], [], marker="o", ls="none", mfc="none", mec="#000000", mew=0.6, ms=3.5))
        ls.append("open: projected, not fitted")
    ax.legend(hs, ls, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=min(4, len(ls)), frameon=False,
              fontsize=5, handletextpad=0.3, columnspacing=1.0)
    if title:
        fig.text(0.5, 0.985, title, ha="center", va="top", fontsize=7)
    fig.savefig(png, dpi=600, facecolor="white")
    fig.savefig(pdf, facecolor="white")
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fit clean + PCA (+ UMAP) on a balanced clean reference, place the "
                                            "rest with transform, draw the map. Coordinates are for pictures only.")
    p.add_argument("--view", action="append", required=True, type=Path, help="embedding table; repeat per view")
    p.add_argument("--common-with", action="append", default=[], type=Path,
                   help="other view files: keep only ids present there too, without using their vectors (one map "
                        "per encoder, every map on the same items)")
    p.add_argument("--id", required=True, help="item id column")
    p.add_argument("--group", required=True, help="column that sets color and marker")
    p.add_argument("--balance-group", default=None, help="column whose groups are balanced in the reference")
    p.add_argument("--reference-mask", default=None, help="boolean column: True = clean item allowed in the fit. "
                   "Items with False (perturbed, derived copies) are only projected")
    p.add_argument("--exclude-pattern", nargs="*", default=[], help="ids containing any of these are projected, "
                   "never fitted (derived copies such as '_chunk', '_zero')")
    p.add_argument("--emb-prefix", default="emb_")
    p.add_argument("--cleaner", choices=("learned", "meta"), default="learned",
                   help="learned: standard scale; meta: signed log, |r|>0.98 pruning, robust scale")
    p.add_argument("--pca-dim", type=int, default=32)
    p.add_argument("--method", choices=("umap", "pca"), default="umap")
    p.add_argument("--neighbors", type=int, default=15)
    p.add_argument("--min-dist", type=float, default=0.3)
    p.add_argument("--width-mm", type=float, default=89.0)
    p.add_argument("--title", default="")
    p.add_argument("--pca-out", type=Path, default=None, help="write the cleaned PCA coordinates (the space for "
                   "any reported distance)")
    p.add_argument("--no-pca-twin", action="store_true", help="skip the PCA 1-2 twin of a UMAP map (written by "
                   "default as <out>_pca.png/.pdf from the same fitted PCA space, colors, markers and frame)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args(argv)
    import pandas as pd
    from sklearn.decomposition import PCA

    outs = [a.out.with_suffix(s) for s in (".png", ".pdf", ".csv", ".json")]
    twin = ([a.out.with_name(a.out.name + "_pca").with_suffix(s) for s in (".png", ".pdf")]
            if a.method == "umap" and not a.no_pca_twin else [])
    points = a.out.with_name(a.out.name + "_points.csv")
    outs.append(points)
    if a.pca_out:
        outs.append(a.pca_out)
    hit = [str(o) for o in outs + twin if o.exists()]
    if hit:
        raise SystemExit(f"refusing to overwrite {hit}; write the variant under a new name")
    extra = [c for c in (a.group, a.balance_group, a.reference_mask) if c]
    views = [read_view(v, a.id, a.emb_prefix, extra) for v in a.view]
    others = [read_view(v, a.id, a.emb_prefix, []) for v in a.common_with]
    common = sorted(set.intersection(*(set(v.index) for v in views + others)))
    dropped = {str(path.name): int(len(v) - len(common)) for path, v in zip(a.view + a.common_with, views + others)}
    if len(common) < 10:
        raise SystemExit(f"only {len(common)} ids are present in every view")
    meta = views[0].loc[common]
    blocks, cleaners = [], []
    ref_ok = np.ones(len(common), bool)
    if a.reference_mask:
        ref_ok &= meta[a.reference_mask].astype(str).str.lower().isin(["true", "1", "yes"]).to_numpy()
    ids = np.asarray(common, dtype=str)
    for pat in a.exclude_pattern:
        ref_ok &= np.char.find(ids, pat) < 0
    ref_idx = np.flatnonzero(ref_ok)
    if a.balance_group:
        ref_idx = ref_idx[balanced_reference(meta[a.balance_group].to_numpy()[ref_idx], a.seed)]
    for v in views:
        cols = [c for c in v.columns if str(c).startswith(a.emb_prefix)]
        X = v.loc[common, cols].to_numpy(np.float64)
        cl = (Cleaner(True, 0.98, "robust") if a.cleaner == "meta" else Cleaner(False, None, "standard"))
        cl.fit(X[ref_idx])
        Z = cl.transform(X)
        if len(views) > 1:                  # balance blocks: each view gets unit total variance on the reference
            Z = Z / (np.sqrt(Z[ref_idx].var(0).sum()) or 1.0)
        blocks.append(Z)
        cleaners.append({"view": str(v.index.name), "columns_in": len(cols), "columns_kept": int(len(cl.idx))})
    Z = np.hstack(blocks)
    k = int(max(2, min(a.pca_dim, Z.shape[1], len(ref_idx) - 1)))
    pca = PCA(n_components=k, random_state=a.seed).fit(Z[ref_idx])
    P = pca.transform(Z)
    if a.method == "umap":
        import umap
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            red = umap.UMAP(n_neighbors=min(a.neighbors, len(ref_idx) - 1), min_dist=a.min_dist,
                            random_state=a.seed).fit(P[ref_idx])
            E = red.transform(P)
        E[ref_idx] = red.embedding_
    else:
        E = P[:, :2]
    role = np.where(np.isin(np.arange(len(common)), ref_idx), "fitted", "projected")

    # ---- picture: points only, full frame, marker per group, one legend --------------------------------------
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial",
                                                                          "DejaVu Sans"],
                         "pdf.fonttype": 42, "text.color": "#000000"})
    warnings.filterwarnings("ignore", message="findfont")
    g = meta[a.group].astype(str).to_numpy()
    for o in outs + twin:
        o.parent.mkdir(parents=True, exist_ok=True)
    draw(E, g, role, a.width_mm, a.title, outs[0], outs[1])
    if twin:                                     # same PCA space, same colors, markers and frame
        draw(P[:, :2], g, role, a.width_mm, f"{a.title} (PCA 1-2)" if a.title else "", twin[0], twin[1])
    pd.DataFrame({"id": common, "group": g, "fit_role": role, "x1": E[:, 0], "x2": E[:, 1]}).to_csv(outs[2],
                                                                                                    index=False)
    # exact inputs of the map, so a colleague can replot it without rerunning the encoders
    fit_order = np.full(len(common), -1)
    fit_order[ref_idx] = np.arange(len(ref_idx))
    tab = pd.DataFrame({"id": common, "group": g, "fit_role": role, "pca_fit": fit_order >= 0,
                        "fit_order": fit_order})
    for path, v in zip(a.view, views):
        cols = [c for c in v.columns if str(c).startswith(a.emb_prefix)]
        feats = v.loc[common, cols].astype(np.float64).reset_index(drop=True)
        feats.columns = [f"{path.stem}__{c}" for c in cols]
        tab = pd.concat([tab, feats], axis=1)
    tab.to_csv(points, index=False, float_format="%.9g")
    if a.pca_out:
        pd.DataFrame(P, index=pd.Index(common, name="id"),
                     columns=[f"pc{j}" for j in range(P.shape[1])]).to_csv(a.pca_out)
    side = {"views": [{"file": v.name, "sha256": sha256(v)} for v in a.view], "items_common": len(common),
            "dropped_by_intersection": dropped, "cleaning": cleaners, "cleaner": a.cleaner,
            "n_fitted": int(len(ref_idx)), "n_projected": int((role == "projected").sum()),
            "fit_groups": {str(k): int(v) for k, v in zip(*np.unique(g[ref_idx], return_counts=True))},
            "balanced_on": a.balance_group, "reference_mask": a.reference_mask, "exclude_pattern": a.exclude_pattern,
            "pca_dim": k, "pca_evr_total": round(float(pca.explained_variance_ratio_.sum()), 4),
            "points_file": {"file": points.name, "sha256": sha256(points),
                            "columns": "id, group, fit_role, pca_fit, fit_order, then <view stem>__<column> per view"},
            "pca_twin": [t.name for t in twin] or None,
            "projection": a.method, "umap": {"n_neighbors": a.neighbors, "min_dist": a.min_dist} if a.method == "umap"
            else None, "seed": a.seed, "command": " ".join(sys.argv),
            "coordinates_are": "for pictures only; compute every reported number in the PCA space "
                               f"({a.pca_out.name if a.pca_out else 'pass --pca-out to write it'})"}
    outs[3].write_text(json.dumps(side, indent=1))
    print(f"[project] {len(common)} items in every view (dropped {dropped}); fitted {len(ref_idx)}, projected "
          f"{side['n_projected']}; wrote {outs[0].name} {outs[2].name} {points.name} {outs[3].name}"
          + (f" {twin[0].name}" if twin else ""), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

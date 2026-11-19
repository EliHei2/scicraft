#!/usr/bin/env python3
"""Pool a per-item embedding table into a small bundle: lattices at several pitches and, optionally, units by key.

Stage 1 of the two-stage pipeline (pool once, render many times). Every pooled site is stored as the RESULTANT SUM
of its items' unit vectors plus a count, never as a mean:

  * the color of a site is its von Mises-Fisher mean direction, sum / ||sum||. Normalizing is not affine, so each
    pooling level is a new population, and a PCA fitted after pooling is a different basis at every level. An
    arithmetic mean is affine: every level would be a linear blur of the next and one PCA would serve them all,
    which hides what pooling does.
  * sums are additive, so a coarser level is an exact re-pool of the same estimate (sum f x f sites), and a
    neighborhood re-pool at render time needs no second pass over the items.
  * every level is pooled from the ITEMS, never from a finer level's colors or bins.

The two random halves of every site are kept too, so split-half reliability (split_half.py) is computed for each
pitch in the same pass, and a new pooling level never ships without its own reliability.

Usage:
  pool_lattice.py TABLE --pitch 200 100 50 25 --out bundle.npz [--unit-key cell_id] [--units um]

Writes bundle.npz and bundle.json (pitches, sites per pitch, r and null per pitch, input hash). Refuses to
overwrite an existing bundle unless --force. Dependencies: numpy (pandas for .parquet/.csv).
Adapted from the source project's field-ladder prep and figure-cache prep scripts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emb_io import add_rows, read_table, sha256, unit  # noqa: E402
from split_half import MIN_CNT, split_half_r  # noqa: E402


def pool(z: np.ndarray, idx: np.ndarray, n: int, half: np.ndarray, chunk: int):
    """Two-half resultant sums and counts per site, accumulated in chunks of items. -> (sA, sB, cA, cB)"""
    d = z.shape[1]
    sa, sb = np.zeros((n, d), np.float64), np.zeros((n, d), np.float64)
    ca, cb = np.zeros(n, np.int64), np.zeros(n, np.int64)
    for s in range(0, len(z), chunk):
        k = slice(s, s + chunk)
        zz, ii, hh = unit(z[k]), idx[k], half[k]
        add_rows(sa, ii[hh], zz[hh])
        add_rows(sb, ii[~hh], zz[~hh])
        ca += np.bincount(ii[hh], minlength=n)[:n]
        cb += np.bincount(ii[~hh], minlength=n)[:n]
    return sa, sb, ca, cb


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pool an embedding table into lattice and unit bundles (resultant "
                                            "sums + counts + split halves).")
    p.add_argument("table", type=Path)
    p.add_argument("--pitch", nargs="*", type=float, default=[], help="lattice pitches, coarse first")
    p.add_argument("--unit-key", default=None, help="also pool by this key (cells, documents, datasets)")
    p.add_argument("--units", default="um", help="coordinate unit, printed in strips (um, px, tokens)")
    p.add_argument("--emb-prefix", default="emb_")
    p.add_argument("--chunk", type=int, default=2_000_000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--force", action="store_true", help="overwrite an existing bundle")
    a = p.parse_args(argv)
    if not a.pitch and not a.unit_key:
        p.error("give --pitch and/or --unit-key")
    out_json = a.out.with_suffix(".json")
    if not a.force and (a.out.exists() or out_json.exists()):
        raise SystemExit(f"{a.out} exists; pick a new name or pass --force")
    t = read_table(a.table, a.emb_prefix, [a.unit_key] if a.unit_key else [])
    z, xy = t["emb"], t["xy"]
    if a.pitch and xy is None:
        raise SystemExit("--pitch needs coordinates")
    n = len(z)
    half = np.random.default_rng(a.seed).random(n) < 0.5
    bundle: dict = {"n_items": np.int64(n), "seed": np.int64(a.seed), "units": np.str_(a.units),
                    "pitches": np.asarray(a.pitch, np.float64)}
    meta: dict = {"table": str(a.table.name), "table_sha256": sha256(a.table), "n_items": n, "dim": int(z.shape[1]),
                  "units": a.units, "seed": a.seed, "pooling": "sum of unit vectors per site (vMF direction "
                  "= sum/||sum||), every level pooled from the items", "levels": []}
    if xy is not None:
        origin = np.floor(xy.min(0))
        bundle["origin"], bundle["extent"] = origin, np.array([*xy.min(0), *xy.max(0)])
        meta["extent"] = [float(v) for v in bundle["extent"]]
        for i, pitch in enumerate(a.pitch):
            ij = np.floor((xy - origin) / pitch).astype(np.int64)
            nx, ny = int(ij[:, 0].max()) + 1, int(ij[:, 1].max()) + 1
            idx = ij[:, 0] * ny + ij[:, 1]
            sa, sb, ca, cb = pool(z, idx, nx * ny, half, a.chunk)
            cnt = ca + cb
            occ = np.flatnonzero(cnt > 0)
            r, r0, used = split_half_r(sa[occ], sb[occ], ca[occ], cb[occ], a.seed)
            ctr = np.column_stack([occ // ny + 0.5, occ % ny + 0.5]) * pitch + origin
            bundle.update({f"p{i}_ctr": ctr.astype(np.float64), f"p{i}_sum": (sa + sb)[occ].astype(np.float32),
                           f"p{i}_cnt": cnt[occ].astype(np.int64), f"p{i}_ij": np.column_stack([occ // ny, occ % ny])})
            lev = {"level": f"p{i}", "pitch": pitch, "sites": int(len(occ)), "grid": [nx, ny],
                   "median_items_per_site": float(np.median(cnt[occ])), "split_half_r": None if np.isnan(r)
                   else round(r, 4), "split_half_null": None if np.isnan(r0) else round(r0, 4),
                   "units_in_r": used, "rel_scope": "whole sample, sites with >= %d items per half" % MIN_CNT}
            meta["levels"].append(lev)
            print(f"[pool] pitch {pitch:g} {a.units}: {len(occ):,} sites, median {lev['median_items_per_site']:.0f} "
                  f"items, split-half r {lev['split_half_r']} (null {lev['split_half_null']})", flush=True)
    if a.unit_key:
        keys, idx = np.unique(t[a.unit_key], return_inverse=True)
        sa, sb, ca, cb = pool(z, idx, len(keys), half, a.chunk)
        cnt = ca + cb
        r, r0, used = split_half_r(sa, sb, ca, cb, a.seed)
        bundle.update({"u_sum": (sa + sb).astype(np.float32), "u_cnt": cnt.astype(np.int64),
                       "u_key": keys.astype(str) if keys.dtype.kind in "OUS" else keys})
        if xy is not None:
            cx = np.zeros((len(keys), 2))
            for j in range(2):
                cx[:, j] = np.bincount(idx, weights=xy[:, j], minlength=len(keys)) / np.maximum(cnt, 1)
            bundle["u_ctr"] = cx
        meta["levels"].append({"level": "unit", "key": a.unit_key, "units": int(len(keys)),
                               "median_items_per_unit": float(np.median(cnt)),
                               "split_half_r": None if np.isnan(r) else round(r, 4),
                               "split_half_null": None if np.isnan(r0) else round(r0, 4), "units_in_r": used,
                               "rel_scope": "whole sample, units with >= %d items per half" % MIN_CNT})
        print(f"[pool] unit {a.unit_key}: {len(keys):,} units, split-half r "
              f"{meta['levels'][-1]['split_half_r']} (null {meta['levels'][-1]['split_half_null']})", flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, **bundle)
    meta["bundle_sha256"] = sha256(a.out)
    out_json.write_text(json.dumps(meta, indent=1))
    print(f"[pool] wrote {a.out} and {out_json.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

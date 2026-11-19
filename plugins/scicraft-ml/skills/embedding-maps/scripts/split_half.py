#!/usr/bin/env python3
"""Split-half reliability of a pooled embedding field, with a re-paired null.

Each unit's items (the tokens of a sentence, the points of a lattice bin, the rows of a dataset, the transcripts of
a cell) are split in two at random. Each half is pooled on its own (sum of unit vectors, then normalized, the
von Mises-Fisher mean direction). The two half-directions are CENTRED on their own grand means, and r is the mean
cosine between the two halves of the same unit. The null re-pairs half B's units at random, which destroys exactly
the correspondence r tests.

  * Centering is required: uncentered unit vectors all point near the grand mean and correlate about 0.99 whatever
    the data do.
  * What r establishes: the pooled value survives resampling the items behind it.
  * What r does NOT establish: that the unit scale carries information of its own. When the encoder's receptive
    field (or context window) is larger than the unit, the two halves share most of their input and must agree.
    In the source project r barely moved across a sweep of pooling pitches, against a null of about 0.000 at
    every pitch. r is a floor, never a way to choose the pooling scale.

Usage:
  split_half.py TABLE --unit-key cell_id            # pool by a key (cells, documents, datasets)
  split_half.py TABLE --pitch 8 15 45               # pool on square lattices of these pitches (needs xy)

Prints one JSON object per pooling (r, r_null, n_units, scope) and exits 1 if any r could not be computed.
Dependencies: numpy (pandas for .parquet/.csv). Adapted from the source project's field-ladder prep script.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emb_io import add_rows, read_table, unit  # noqa: E402

MIN_CNT = 3          # a unit with fewer items per half is noise and is left out
MIN_UNITS = 20       # fewer valid units than this: no estimate


def split_half_r(sa: np.ndarray, sb: np.ndarray, ca: np.ndarray, cb: np.ndarray, seed: int,
                 min_cnt: int = MIN_CNT) -> tuple[float, float, int]:
    """(resultant sums of half A, of half B, counts A, counts B) per unit -> (r, r_null, n_units used)."""
    ok = (ca >= min_cnt) & (cb >= min_cnt)
    if int(ok.sum()) < MIN_UNITS:
        return float("nan"), float("nan"), int(ok.sum())
    a, b = unit(sa[ok]), unit(sb[ok])
    a, b = unit(a - a.mean(0)), unit(b - b.mean(0))
    perm = np.random.default_rng(seed).permutation(len(b))
    return float(np.mean(np.sum(a * b, 1))), float(np.mean(np.sum(a * b[perm], 1))), int(ok.sum())


def halves_by_index(z: np.ndarray, idx: np.ndarray, n_units: int, seed: int):
    """Pool unit vectors z into n_units by idx, in two random halves. -> (sumA, sumB, cntA, cntB)"""
    half = np.random.default_rng(seed).random(len(z)) < 0.5
    out = []
    for hm in (half, ~half):
        s = np.zeros((n_units, z.shape[1]), np.float64)
        add_rows(s, idx[hm], z[hm])
        out.append(s)
    ca = np.bincount(idx[half], minlength=n_units)[:n_units]
    cb = np.bincount(idx[~half], minlength=n_units)[:n_units]
    return out[0], out[1], ca, cb


def lattice_index(xy: np.ndarray, pitch: float, origin: np.ndarray) -> tuple[np.ndarray, int]:
    """Flat index on a square lattice anchored at origin (floor, never round). -> (idx, n_sites)"""
    ij = np.floor((xy - origin) / pitch).astype(np.int64)
    nx, ny = int(ij[:, 0].max()) + 1, int(ij[:, 1].max()) + 1
    return ij[:, 0] * ny + ij[:, 1], nx * ny


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Split-half reliability of a pooled embedding field, with a "
                                            "re-paired null. Prints JSON lines.")
    p.add_argument("table", type=Path, help=".npz / .parquet / .csv embedding table")
    p.add_argument("--unit-key", default=None, help="pool by this key (integer or string ids)")
    p.add_argument("--pitch", nargs="*", type=float, default=[], help="lattice pitches in coordinate units")
    p.add_argument("--emb-prefix", default="emb_")
    p.add_argument("--min-count", type=int, default=MIN_CNT, help="items per half a unit needs")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--scope", default="whole sample", help="what the statistic is computed over (printed)")
    a = p.parse_args(argv)
    if not a.unit_key and not a.pitch:
        p.error("give --unit-key or --pitch")
    t = read_table(a.table, a.emb_prefix, [a.unit_key] if a.unit_key else [])
    z = unit(t["emb"])
    bad = 0
    poolings: list[tuple[str, np.ndarray, int]] = []
    if a.unit_key:
        keys, idx = np.unique(t[a.unit_key], return_inverse=True)
        poolings.append((f"unit:{a.unit_key}", idx, len(keys)))
    if a.pitch:
        if t["xy"] is None:
            raise SystemExit("--pitch needs coordinates (xy in .npz, or x and y columns)")
        origin = t["xy"].min(0)
        for pitch in a.pitch:
            idx, n = lattice_index(t["xy"], pitch, origin)
            poolings.append((f"lattice:{pitch:g}", idx, n))
    for name, idx, n in poolings:
        sa, sb, ca, cb = halves_by_index(z, idx, n, a.seed)
        r, r0, used = split_half_r(sa, sb, ca, cb, a.seed, a.min_count)
        med = float(np.median((ca + cb)[(ca >= a.min_count) & (cb >= a.min_count)])) if used else 0.0
        rec = {"pooling": name, "r": None if np.isnan(r) else round(r, 4),
               "r_null": None if np.isnan(r0) else round(r0, 4), "n_units": used,
               "median_items_per_unit": med, "min_items_per_half": a.min_count, "scope": a.scope,
               "seed": a.seed, "reads": "floor only: r says the value survives resampling, not that this "
                                         "scale carries independent information"}
        print(json.dumps(rec))
        bad += int(np.isnan(r))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

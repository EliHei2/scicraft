#!/usr/bin/env python3
"""Classify the current render of a figure repository against its frozen baseline.

Run render_all.py --baseline once before the change, render_all.py after it, then:

    python compare.py --snap <repo>/_verify_snap --intended INTENDED_CHANGES.tsv

Each output file falls in one class:
  identical                  exact sha256 match;
  identical-modulo-encoding  perceptual mean absolute difference below --eps (re-encode noise);
  changed-as-intended        difference at or above --eps and listed in the intended-changes file;
  regressed                  difference at or above --eps and not listed, or the PDF page size
                             changed, or the output vanished, or its unit failed to render;
  new                        present now, absent from the baseline (listed, not failed).

The intended-changes file has one row per output: <path relative to repo>\t<one-line reason>.
Lines starting with # are comments. A page-size change is a regression even when listed,
because the composer places panels by size.

Writes baseline|current|difference triptychs for every non-identical PNG or PDF to
<snap>/diffs/ for a visual look. Exit 1 if anything regressed.

Dependencies: numpy, Pillow. Adapted from the render-parity harness of a paper-figures repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sig  # noqa: E402

EPS = 0.004  # perceptual difference below this reads as visually identical


def load(snap: Path, mode: str) -> tuple[dict, dict]:
    base = snap / mode
    if not (base / "manifest.tsv").is_file():
        sys.exit(f"no {mode} snapshot in {snap}; run render_all.py{' --baseline' if mode == 'baseline' else ''} first")
    rows: dict[str, dict] = {}
    for line in (base / "manifest.tsv").read_text().splitlines()[1:]:
        rel, kind, _nbytes, sha, w, h = line.split("\t")
        rows[rel] = {"kind": kind, "sha": sha, "w": w, "h": h}
    npz = np.load(base / "grids.npz")
    return rows, {k.replace("__", "/"): npz[k] for k in npz.files}


def intended(path: Path | None) -> dict[str, str]:
    if not path or not path.is_file():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            rel, _, reason = line.partition("\t")
            out[rel.strip()] = reason.strip()
    return out


def triptych(diffs: Path, rel: str, b: np.ndarray, c: np.ndarray) -> None:
    diffs.mkdir(parents=True, exist_ok=True)
    d = np.abs(b.astype(np.int16) - c.astype(np.int16)).astype(np.uint8)
    gap = np.full((b.shape[0], 2), 128, np.uint8)
    strip = np.concatenate([b, gap, c, gap, 255 - d], axis=1)
    Image.fromarray(strip).resize((strip.shape[1] * 3, strip.shape[0] * 3), Image.NEAREST) \
        .save(diffs / (rel.replace("/", "__") + ".png"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Classify current figure outputs against the baseline snapshot.")
    ap.add_argument("--snap", type=Path, required=True, help="snapshot folder written by render_all.py")
    ap.add_argument("--intended", type=Path, help="TSV of outputs meant to change, with a reason each")
    ap.add_argument("--eps", type=float, default=EPS, help=f"perceptual threshold (default {EPS})")
    args = ap.parse_args()

    b_rows, b_grids = load(args.snap, "baseline")
    c_rows, c_grids = load(args.snap, "current")
    want = intended(args.intended)
    diffs = args.snap / "diffs"

    failed = []
    log = args.snap / "current" / "render_log.tsv"
    if log.is_file():
        failed = [r.split("\t")[0] for r in log.read_text().splitlines()[1:] if r and r.split("\t")[2] != "0"]

    buckets: dict[str, list[str]] = {k: [] for k in
                                     ("identical", "identical-modulo-encoding", "changed-as-intended", "new", "regressed")}
    for rel in sorted(set(b_rows) | set(c_rows)):
        if rel not in b_rows:
            buckets["new"].append(rel)
            continue
        if rel not in c_rows:
            buckets["regressed"].append(f"{rel}  (MISSING after render)")
            continue
        if b_rows[rel]["sha"] == c_rows[rel]["sha"]:
            buckets["identical"].append(rel)
            continue
        geom = b_rows[rel]["kind"] == "pdf" and (b_rows[rel]["w"], b_rows[rel]["h"]) != (c_rows[rel]["w"], c_rows[rel]["h"])
        d = sig.mad(b_grids[rel], c_grids[rel])
        if d < args.eps and not geom:
            buckets["identical-modulo-encoding"].append(rel)
            continue
        triptych(diffs, rel, b_grids[rel], c_grids[rel])
        tag = f"{rel}  (MAD={d:.4f}{', PAGE-SIZE CHANGED' if geom else ''})"
        if rel in want and not geom:
            buckets["changed-as-intended"].append(f"{tag}  -- {want[rel]}")
        else:
            buckets["regressed"].append(tag)

    print("=== render-parity report (baseline vs current) ===")
    for k, items in buckets.items():
        print(f"\n[{k}] {len(items)}")
        for it in items:
            print(f"    {it}")
    unused = sorted(set(want) - set(b_rows) - set(c_rows))
    if unused:
        print(f"\n[intended-changes rows matching no output] {unused}")
    if failed:
        print(f"\n[render FAILURES] {failed}")
    if diffs.exists():
        print(f"\ntriptychs -> {diffs}")
    sys.exit(1 if buckets["regressed"] or failed else 0)


if __name__ == "__main__":
    main()

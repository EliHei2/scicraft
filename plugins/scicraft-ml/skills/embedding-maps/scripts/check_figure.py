#!/usr/bin/env python3
"""Gate for embedding-map figures: sidecar completeness, and proof that no figure the author has seen was changed.

Checks, for every .png given (or found under a folder):
  1. a .json sidecar sits beside it, and a .pdf twin;
  2. a field map sidecar (from field_rgb.py) records: the stretch percentiles, the edge-mask fraction, the basis
     (level, axes rule, Moran's I), per panel the level, window and the strip text, the crop placement, the seed,
     the input hashes, and a split-half r with its null and scope for at least one level;
  3. an item map sidecar (from project_items.py) records: the views and their hashes, the items kept in every view
     and the number dropped, the fitted and projected counts, the projection and the seed; the points file it
     names still has its recorded hash; a UMAP map without a PCA twin, or without a points file, is a warning. A
     PCA twin (<stem>_pca.png) is covered by the sidecar of its UMAP map;
  4. with --ledger: every file recorded in the ledger still exists with the same hash (a figure the author has
     seen is never overwritten or deleted). --record adds the given figures to the ledger after the checks pass.

A sidecar written by hand passes when it carries the same keys. Warnings (stretch not 5/95, crops placed on the
field, a failed reliability estimate) are printed and do not fail the run; missing keys and changed seen
figures do. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

FIELD_KEYS = ["stretch_percentiles", "fill_mask_fraction", "basis", "panels", "crops_placed_on", "seed",
              "bundle_sha256", "reliability"]
ITEM_KEYS = ["views", "items_common", "dropped_by_intersection", "n_fitted", "n_projected", "projection", "seed",
             "coordinates_are"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_one(png: Path, errs: list[str], warns: list[str]) -> None:
    js, pdf = png.with_suffix(".json"), png.with_suffix(".pdf")
    if not js.exists() and png.stem.endswith("_pca"):
        parent = png.with_name(png.stem[:-4] + ".json")
        try:
            if parent.exists() and png.name in (json.loads(parent.read_text()).get("pca_twin") or []):
                return
        except json.JSONDecodeError:
            pass
    if not js.exists():
        errs.append(f"{png}: no sidecar {js.name}; every number that left the figure must arrive there")
        return
    if not pdf.exists():
        warns.append(f"{png}: no PDF twin")
    try:
        s = json.loads(js.read_text())
    except json.JSONDecodeError as e:
        errs.append(f"{js}: not valid JSON ({e})")
        return
    if "coordinates_are" in s or "views" in s:
        for k in ITEM_KEYS:
            if k not in s:
                errs.append(f"{js}: missing '{k}'")
        pts = s.get("points_file")
        if not pts:
            warns.append(f"{js}: no points file; write the exact inputs of the map so it can be replotted")
        else:
            f = js.parent / pts["file"]
            if not f.exists():
                errs.append(f"{js}: points file {f.name} is missing")
            elif sha(f) != pts.get("sha256"):
                errs.append(f"{js}: points file {f.name} changed since the map was drawn")
        if s.get("projection") == "umap" and not s.get("pca_twin"):
            warns.append(f"{js}: UMAP map without a PCA twin; render one from the same PCA space")
        if s.get("n_fitted", 0) and s.get("n_projected", 0) == 0:
            warns.append(f"{js}: nothing projected; check that perturbed or derived items were not fitted")
        return
    for k in FIELD_KEYS:
        if k not in s:
            errs.append(f"{js}: missing '{k}'")
    if s.get("stretch_percentiles") not in (None, [5.0, 95.0], [5, 95]):
        warns.append(f"{js}: stretch {s.get('stretch_percentiles')} is not 5/95; say why in the caption")
    for i, pnl in enumerate(s.get("panels", [])):
        for k in ("level", "window", "strip"):
            if k not in pnl:
                errs.append(f"{js}: panel {i} missing '{k}'")
    rel = [r for r in s.get("reliability", []) if r.get("split_half_r") is not None]
    if not rel:
        errs.append(f"{js}: no split-half r with a null; pool with pool_lattice.py or add it by hand")
    for r in rel:
        if r.get("split_half_null") is None or not r.get("rel_scope"):
            errs.append(f"{js}: reliability at {r.get('level')} lacks its null or its scope")
    if str(s.get("crops_placed_on", "")).startswith("field"):
        warns.append(f"{js}: crops placed on the field being judged; the caption must say so")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check embedding-map figures: sidecars complete, seen figures intact.")
    p.add_argument("paths", nargs="+", type=Path, help=".png files or folders holding them")
    p.add_argument("--ledger", type=Path, default=None, help="text file of 'sha256  path' lines for seen figures")
    p.add_argument("--record", action="store_true", help="after the checks pass, add these figures to the ledger")
    a = p.parse_args(argv)
    pngs: list[Path] = []
    for q in a.paths:
        pngs += sorted(q.rglob("*.png")) if q.is_dir() else [q]
    errs: list[str] = []
    warns: list[str] = []
    for png in pngs:
        check_one(png, errs, warns)
    seen: dict[str, str] = {}
    if a.ledger and a.ledger.exists():
        for line in a.ledger.read_text().splitlines():
            if line.strip():
                h, path = line.split(None, 1)
                seen[path] = h
        for path, h in seen.items():
            q = Path(path)
            if not q.exists():
                errs.append(f"seen figure deleted or renamed: {path}")
            elif sha(q) != h:
                errs.append(f"seen figure overwritten: {path} (write variants under a new name)")
    for w in warns:
        print("warn  ", w)
    for e in errs:
        print("ERROR ", e)
    print(f"[check_figure] {len(pngs)} figure(s), {len(errs)} error(s), {len(warns)} warning(s); "
          f"{len(seen)} seen figure(s) in the ledger")
    if errs:
        return 1
    if a.record and a.ledger:
        with open(a.ledger, "a") as fh:
            for png in pngs:
                for q in (png, png.with_suffix(".pdf"), png.with_suffix(".json")):
                    if q.exists() and str(q) not in seen:
                        fh.write(f"{sha(q)}  {q}\n")
        print(f"[check_figure] recorded {len(pngs)} figure(s) in {a.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

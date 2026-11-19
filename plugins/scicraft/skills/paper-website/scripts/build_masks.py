#!/usr/bin/env python3
"""Filled outlines of many objects for a web viewer, traced from each object's own points. Never deployed.

    python3 build_masks.py POINTS OUT_DIR [--objects OBJECTS] [--tile 128] [--share 0.1] [--batch 20000] ...
    python3 build_masks.py --self-test

POINTS holds one row per point with columns x, y and id (the object the point belongs to; rows with id < 0 are
skipped). OBJECTS, optional, holds one row per object with id, x, y (its center) and r, g, b and type for its fill;
without it the center is the mean of the object's points and the fill is grey. Both are .npz (one array per column)
or .csv with a header. The unit of x and y is free; the defaults are in µm, from the original use (cells traced from
their transcripts), and fit any labeled point cloud: clusters in an embedding, objects in a LiDAR scan.

Per object, in batches of --batch objects so memory stays flat:
  1. take a random --share of its points and drop those farther than --near from its center (strays make giant hulls);
  2. concave hull (--ratio: 0 tightest, 1 convex); an object with too few points or a hull under --min-area becomes a
     small disc of radius --fallback;
  3. close (buffer out, then in) by --close to round the hull's spikes, and shrink by --seam so neighbors keep a dark
     seam between them;
  4. simplify by --simplify and clip to a disc of radius --clip around the center;
  5. constrained Delaunay triangulation, so the GPU draws the fill as plain triangles with no polygon library.

Out, in OUT_DIR:
  masks.bin        gzip chunks per tile; planar per vertex: i16 x, i16 y (in 1/--q units from the tile center),
                   u8 r, g, b, type; three vertices per triangle
  masks_index.bin  u32 (byte offset, vertex count) per tile, row-major
  masks.json       {file, index, unit, anchor: "center", tile, bbox, tiles_w, tiles_h, n}
assets/unpack_points.js (unpackMasks) turns a chunk back into positions and colors.

Needs numpy and shapely 2.1 or later (constrained_delaunay_triangles).
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

try:
    import shapely
except ImportError:  # pragma: no cover
    sys.exit('needs shapely 2.1 or later: pip install "shapely>=2.1"')

T0 = time.time()


def log(msg):
    print(f'[{time.time() - T0:6.1f}s] {msg}', flush=True)


def load(path: Path, need) -> dict:
    if path.suffix == '.npz':
        with np.load(path) as z:
            cols = {k: np.asarray(z[k]) for k in z.files}
    elif path.suffix == '.csv':
        with open(path, newline='') as f:
            rows = list(csv.DictReader(f))
        cols = {k: np.array([float(r[k]) for r in rows]) for k in (rows[0] if rows else [])}
    else:
        sys.exit(f'{path}: expected .npz or .csv')
    missing = [k for k in need if k not in cols]
    if missing:
        sys.exit(f'{path}: missing column(s) {", ".join(missing)}')
    return cols


def build(args):
    if not hasattr(shapely, 'constrained_delaunay_triangles'):
        sys.exit(f'shapely {shapely.__version__} has no constrained_delaunay_triangles; needs 2.1 or later')
    P = load(Path(args.points), ('x', 'y', 'id'))
    pid = P['id'].astype(np.int64)
    keep = pid >= 0
    rng = np.random.default_rng(args.seed)
    keep &= rng.random(len(pid)) < args.share
    x, y, pid = P['x'][keep].astype(np.float64), P['y'][keep].astype(np.float64), pid[keep]

    if args.objects:
        O = load(Path(args.objects), ('id', 'x', 'y'))
        ids = O['id'].astype(np.int64)
        centre = np.column_stack([O['x'], O['y']]).astype(np.float64)
        col = np.full((len(ids), 4), [150, 150, 158, 0], np.uint8)
        for j, k in enumerate(('r', 'g', 'b', 'type')):
            if k in O:
                col[:, j] = np.clip(np.round(O[k]), 0, 255).astype(np.uint8)
    else:
        ids = np.unique(pid)
        code = np.searchsorted(ids, pid)
        cnt = np.bincount(code, minlength=len(ids))
        centre = np.column_stack([np.bincount(code, x, len(ids)), np.bincount(code, y, len(ids))]) / np.maximum(cnt, 1)[:, None]
        col = np.tile(np.array([150, 150, 158, 0], np.uint8), (len(ids), 1))
    order_ids = np.argsort(ids)
    pos = np.searchsorted(ids[order_ids], pid)
    pos = np.clip(pos, 0, len(ids) - 1)
    known = ids[order_ids][pos] == pid
    c = order_ids[pos][known]
    x, y = x[known], y[known]
    o = np.argsort(c, kind='stable')
    x, y, c = x[o], y[o], c[o]
    n_obj = len(ids)
    counts = np.bincount(c, minlength=n_obj)
    log(f'{len(x):,} points kept for {n_obj:,} objects; median {np.median(counts[counts > 0]) if counts.any() else 0:.0f} '
        f'per object, {int((counts == 0).sum()):,} without any')

    bounds_c = np.searchsorted(c, np.arange(n_obj + 1))
    V, OWN, nb = [], [], 0
    for a in range(0, n_obj, args.batch):
        b = min(a + args.batch, n_obj)
        lo, hi = int(bounds_c[a]), int(bounds_c[b])
        cc, xx, yy = c[lo:hi], x[lo:hi], y[lo:hi]
        near = np.hypot(xx - centre[cc, 0], yy - centre[cc, 1]) <= args.near
        cc, xx, yy = cc[near], xx[near], yy[near]
        ctr = shapely.points(centre[a:b])
        hull = np.empty(b - a, dtype=object)
        hull[:] = None
        if len(cc):
            present, sub = np.unique(cc - a, return_inverse=True)
            mp = shapely.multipoints(np.column_stack([xx, yy]), indices=sub)
            hull[present] = shapely.concave_hull(mp, ratio=args.ratio, allow_holes=False)
        bad = np.array([h is None or shapely.get_type_id(h) != 3 or shapely.area(h) < args.min_area for h in hull])
        if bad.any():
            hull[bad] = shapely.buffer(ctr[bad], args.fallback, quad_segs=4)
        nb += int(bad.sum())
        closed = shapely.buffer(hull.astype(object), args.close, quad_segs=4)
        shrunk = shapely.buffer(closed, -args.close - args.seam, quad_segs=4)
        lost = shapely.is_empty(shrunk) | (shapely.get_type_id(shrunk) != 3)
        shrunk[lost] = hull[lost]
        poly = shapely.simplify(shrunk, args.simplify, preserve_topology=True)
        poly = shapely.intersection(poly, shapely.buffer(ctr, args.clip, quad_segs=8))
        poly = np.where(shapely.get_type_id(poly) == 3, poly, shapely.buffer(ctr, args.fallback, quad_segs=4))
        tri = shapely.constrained_delaunay_triangles(poly)
        parts, owner = shapely.get_parts(tri, return_index=True)
        coords, cidx = shapely.get_coordinates(parts, return_index=True)
        first = np.flatnonzero(np.r_[True, cidx[1:] != cidx[:-1]])
        V.append(coords[(first[:, None] + np.arange(3)).ravel()])
        OWN.append((owner + a).astype(np.int64))
        log(f'objects {b:,} / {n_obj:,}')
    v = np.concatenate(V) if V else np.zeros((0, 2))
    tri_owner = np.concatenate(OWN) if OWN else np.zeros(0, np.int64)
    log(f'{len(tri_owner):,} triangles, {len(tri_owner) / max(n_obj, 1):.1f} per object; {nb:,} fell back to a disc')

    x0, y0 = float(centre[:, 0].min()), float(centre[:, 1].min())
    tw = int(np.floor((centre[:, 0].max() - x0) / args.tile)) + 1
    th = int(np.floor((centre[:, 1].max() - y0) / args.tile)) + 1
    gx = np.minimum(((centre[:, 0] - x0) / args.tile).astype(np.int64), tw - 1)
    gy = np.minimum(((centre[:, 1] - y0) / args.tile).astype(np.int64), th - 1)
    tile = (gy * tw + gx)[tri_owner]
    ot = np.argsort(tile, kind='stable')
    bounds = np.searchsorted(tile[ot], np.arange(tw * th + 1))
    reach = (args.tile / 2 + args.clip) * args.q
    if reach >= 32767:
        sys.exit(f'(--tile / 2 + --clip) * --q = {reach:.0f} does not fit int16; lower --q or --tile')

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    idx = np.zeros((tw * th, 2), np.uint32)
    off = 0
    with open(out / 'masks.bin.part', 'wb') as f:
        for i in range(tw * th):
            a, b = int(bounds[i]), int(bounds[i + 1])
            idx[i, 0] = off
            if a == b:
                continue
            tris = ot[a:b]
            vv = v.reshape(-1, 3, 2)[tris].reshape(-1, 2)
            jx, jy = i % tw, i // tw
            lx = np.round((vv[:, 0] - (x0 + (jx + 0.5) * args.tile)) * args.q)
            ly = np.round((vv[:, 1] - (y0 + (jy + 0.5) * args.tile)) * args.q)
            cc = np.repeat(col[tri_owner[tris]], 3, axis=0)
            raw = b''.join((lx.astype('<i2').tobytes(), ly.astype('<i2').tobytes(),
                            cc[:, 0].tobytes(), cc[:, 1].tobytes(), cc[:, 2].tobytes(), cc[:, 3].tobytes()))
            blob = gzip.compress(raw, 6, mtime=0)
            idx[i, 1] = len(vv)
            f.write(blob)
            off += len(blob)
    (out / 'masks.bin.part').replace(out / 'masks.bin')
    (out / 'masks_index.bin').write_bytes(idx.astype('<u4').tobytes())
    meta = dict(file='masks.bin', index='masks_index.bin', unit=1 / args.q, anchor='center', tile=args.tile,
                bbox=[x0, y0, float(centre[:, 0].max()), float(centre[:, 1].max())], tiles_w=tw, tiles_h=th,
                n=int(n_obj), share=args.share)
    (out / 'masks.json').write_text(json.dumps(meta, indent=1))
    log(f'masks.bin {off / 1e6:.2f} MB')
    return dict(v=v, owner=tri_owner, centre=centre, fallback=nb)


def self_test():
    """Synthetic blobs on a lattice: every object gets triangles, its fill stays near its center, area is plausible."""
    rng = np.random.default_rng(3)
    k = 12
    cx, cy = np.meshgrid(np.arange(k) * 20.0 + 10, np.arange(k) * 20.0 + 10)
    centre = np.column_stack([cx.ravel(), cy.ravel()])
    n_obj = len(centre)
    per = 400
    pid = np.repeat(np.arange(n_obj), per)
    ang, rad = rng.uniform(0, 2 * np.pi, len(pid)), 6.0 * np.sqrt(rng.uniform(0, 1, len(pid)))
    px = centre[pid, 0] + rad * np.cos(ang)
    py = centre[pid, 1] + rad * np.sin(ang)
    px, py, pid = np.r_[px, 500.0], np.r_[py, 500.0], np.r_[pid, -1]          # one unassigned point is skipped
    with tempfile.TemporaryDirectory() as d:
        np.savez(Path(d) / 'pts.npz', x=px, y=py, id=pid)
        np.savez(Path(d) / 'obj.npz', id=np.arange(n_obj), x=centre[:, 0], y=centre[:, 1],
                 r=np.full(n_obj, 230), g=np.full(n_obj, 159), b=np.zeros(n_obj), type=np.arange(n_obj) % 7)
        a = parser().parse_args([str(Path(d) / 'pts.npz'), str(Path(d) / 'out'), '--objects', str(Path(d) / 'obj.npz'),
                                 '--batch', '50', '--tile', '64', '--share', '0.5'])
        r = build(a)
        v, own = r['v'].reshape(-1, 3, 2), r['owner']
        tri_area = 0.5 * np.abs((v[:, 1, 0] - v[:, 0, 0]) * (v[:, 2, 1] - v[:, 0, 1])
                                - (v[:, 2, 0] - v[:, 0, 0]) * (v[:, 1, 1] - v[:, 0, 1]))
        area = np.bincount(own, tri_area, n_obj)
        far = np.hypot(v[..., 0] - centre[own, 0][:, None], v[..., 1] - centre[own, 1][:, None]).max()
        idx = np.frombuffer((Path(d) / 'out/masks_index.bin').read_bytes(), '<u4').reshape(-1, 2)
        ok = (np.bincount(own, minlength=n_obj) > 0).all() and far <= 6.5 and 60 < np.median(area) < np.pi * 36 \
            and int(idx[:, 1].sum()) == 3 * len(own) and r['fallback'] == 0
        print(f'self-test: {n_obj} objects, all with triangles; median area {np.median(area):.1f} '
              f'(disc of radius 6 is {np.pi * 36:.1f}); farthest vertex {far:.2f} from its center; '
              f'{int(idx[:, 1].sum()):,} vertices written: {"PASS" if ok else "FAIL"}')
        return 0 if ok else 1


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('points', nargs='?', help='.npz or .csv with x, y, id')
    ap.add_argument('out_dir', nargs='?', help='folder for masks.bin, masks_index.bin, masks.json')
    ap.add_argument('--objects', help='.npz or .csv with id, x, y and optional r, g, b, type')
    ap.add_argument('--tile', type=float, default=128.0, help='side of one chunk (default 128)')
    ap.add_argument('--share', type=float, default=0.10, help='share of each object\'s points used (default 0.10)')
    ap.add_argument('--batch', type=int, default=20_000, help='objects per batch (default 20000)')
    ap.add_argument('--ratio', type=float, default=0.42, help='concave hull ratio, 0 tightest to 1 convex (default 0.42)')
    ap.add_argument('--close', type=float, default=1.1, help='closing radius (default 1.1)')
    ap.add_argument('--seam', type=float, default=0.22, help='inward shrink per side (default 0.22)')
    ap.add_argument('--simplify', type=float, default=0.22, help='simplify tolerance (default 0.22)')
    ap.add_argument('--clip', type=float, default=30.0, help='clip to a disc of this radius around the center (default 30)')
    ap.add_argument('--near', type=float, default=25.0, help='drop points farther than this from the center (default 25)')
    ap.add_argument('--fallback', type=float, default=3.2, help='disc radius for objects without a usable hull (default 3.2)')
    ap.add_argument('--min-area', type=float, default=6.0, help='smallest hull area kept (default 6)')
    ap.add_argument('--q', type=float, default=128.0, help='vertex steps per unit (default 128)')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--self-test', action='store_true', help='trace synthetic blobs and check the result')
    return ap


def main():
    ap = parser()
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.points or not a.out_dir:
        ap.error('POINTS and OUT_DIR are required')
    build(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())

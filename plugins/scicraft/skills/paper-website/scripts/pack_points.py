#!/usr/bin/env python3
"""Pack a large colored point layer into small gzip chunks that a web viewer fetches by HTTP range. Never deployed.

    python3 pack_points.py POINTS OUT_DIR [--tile 128] [--grid 4096] [--probe] [--threads 6]
    python3 pack_points.py --self-test

POINTS is a .npz with arrays x, y, r, g, b and optionally type (one value per point), or a .csv with a header holding
those columns. Coordinates are in any unit; --tile is the side of one square chunk in that unit (128 µm in the
original viewer, where a dot was 0.3 µm wide).

Each point is quantized to what a dot can show and written planar, then gzip -9 per tile:

    u8 x lo, u8 x hi, u8 dy lo, u8 dy hi    x and y on a GRID x GRID raster inside the tile; points sorted by y, y as deltas
    u8 color lo, u8 color hi                RGB565, rounded (mean error about 1.6/255, never above 4/255)
    u8 type                                 a class label the viewer may filter on (0 when absent)

Planar bytes (all low bytes, then all high bytes) compress far better than interleaved records. Any field the viewer
never reads stays out: in the original, dropping a per-point identifier and quantizing this way took the layer from
567 MB to 255 MB.

Out, in OUT_DIR:
  points.bin        the gzip chunks, back to back
  points_index.bin  u32 (byte offset, point count) per tile, row-major; empty tiles keep a monotone offset
  points.json       {format: "q-planar", grid, tile, bbox, tiles_w, tiles_h, n, file, index}

In the page, assets/unpack_points.js turns a fetched chunk back into the GPU layout the viewer draws (planar u16 x,
u16 y, u8 r, g, b, type; positions on 0..65535 across the tile, at the center of their grid cell).

--probe reports the projected size ratio and the color error on a sample of tiles without writing anything.
Keep the source layer outside public/ (for example pipeline/cache/), so the packing can be redone, and shoot the same
close-up at the finest zoom before and after packing.

Needs numpy.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

T0 = time.time()


def log(msg):
    print(f'[{time.time() - T0:6.1f}s] {msg}', flush=True)


def load(path: Path) -> dict:
    if path.suffix == '.npz':
        with np.load(path) as z:
            cols = {k: np.asarray(z[k]) for k in z.files}
    elif path.suffix == '.csv':
        with open(path, newline='') as f:
            rows = list(csv.DictReader(f))
        if not rows:
            sys.exit(f'{path}: no rows')
        cols = {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}
    else:
        sys.exit(f'{path}: expected .npz or .csv')
    missing = [k for k in ('x', 'y', 'r', 'g', 'b') if k not in cols]
    if missing:
        sys.exit(f'{path}: missing column(s) {", ".join(missing)}')
    n = len(cols['x'])
    out = {k: cols[k].astype(np.float64) for k in ('x', 'y')}
    for k in ('r', 'g', 'b'):
        out[k] = np.clip(np.round(cols[k]), 0, 255).astype(np.uint8)
    out['t'] = np.clip(np.round(cols['type']), 0, 255).astype(np.uint8) if 'type' in cols else np.zeros(n, np.uint8)
    return out


def rgb565(r, g, b):
    """Rounded to the nearest level; plain truncation (r >> 3) errs by up to 8/255."""
    r, g, b = (a.astype(np.uint32) for a in (r, g, b))
    r5, g6, b5 = (r * 31 + 127) // 255, (g * 63 + 127) // 255, (b * 31 + 127) // 255
    return ((r5 << 11) | (g6 << 5) | b5).astype(np.uint16)


def unrgb565(v):
    """The viewer's expansion (assets/unpack_points.js), mirrored here to measure the error."""
    v = v.astype(np.int32)
    return np.stack([((v >> 11) * 527 + 23) >> 6, (((v >> 5) & 63) * 259 + 33) >> 6, ((v & 31) * 527 + 23) >> 6], 1)


class Packer:
    def __init__(self, P: dict, tile: float, grid: int):
        if grid < 2 or grid > 65536 or grid & (grid - 1):
            sys.exit('--grid must be a power of two from 2 to 65536')
        self.P, self.tile, self.grid = P, tile, grid
        x0, y0 = float(P['x'].min()), float(P['y'].min())
        self.bbox = [x0, y0, float(P['x'].max()), float(P['y'].max())]
        self.tw = max(1, int(np.floor((self.bbox[2] - x0) / tile)) + 1)
        self.th = max(1, int(np.floor((self.bbox[3] - y0) / tile)) + 1)
        gx = np.minimum(((P['x'] - x0) / tile).astype(np.int64), self.tw - 1)
        gy = np.minimum(((P['y'] - y0) / tile).astype(np.int64), self.th - 1)
        self.tile_of = gy * self.tw + gx
        self.order = np.argsort(self.tile_of, kind='stable')
        self.bounds = np.searchsorted(self.tile_of[self.order], np.arange(self.tw * self.th + 1))

    def raw(self, i):
        a, b = int(self.bounds[i]), int(self.bounds[i + 1])
        sel = self.order[a:b]
        P, g = self.P, self.grid
        jx, jy = i % self.tw, i // self.tw
        fx = (P['x'][sel] - (self.bbox[0] + jx * self.tile)) / self.tile
        fy = (P['y'][sel] - (self.bbox[1] + jy * self.tile)) / self.tile
        xq = np.clip((fx * g).astype(np.int64), 0, g - 1).astype(np.uint16)
        yq = np.clip((fy * g).astype(np.int64), 0, g - 1).astype(np.uint16)
        o = np.lexsort((xq, yq))
        xq, yq, sel = xq[o], yq[o], sel[o]
        dy = np.diff(yq, prepend=np.uint16(0)).astype(np.uint16)
        c = rgb565(P['r'][sel], P['g'][sel], P['b'][sel])
        lo = lambda v: (v & 255).astype(np.uint8).tobytes()  # noqa: E731
        hi = lambda v: (v >> 8).astype(np.uint8).tobytes()   # noqa: E731
        body = b''.join((lo(xq), hi(xq), lo(dy), hi(dy), lo(c), hi(c), np.ascontiguousarray(P['t'][sel]).tobytes()))
        rgb = np.stack([P['r'][sel], P['g'][sel], P['b'][sel]], 1).astype(np.int32)
        err = np.abs(unrgb565(c) - rgb)
        return len(sel), body, err

    def pack(self, i):
        n, body, err = self.raw(i)
        if n == 0:
            return 0, b'', 0.0, 0
        return n, gzip.compress(body, 9, mtime=0), float(err.mean()), int(err.max())


def naive_size(n):
    """Bytes of the same points as plain float32 x, y and u8 r, g, b, type: the baseline the ratio is given against."""
    return 12 * n


def run(args):
    P = load(Path(args.points))
    pk = Packer(P, args.tile, args.grid)
    n_all = len(P['x'])
    full = np.flatnonzero(np.diff(pk.bounds))
    log(f'{n_all:,} points, {pk.tw} x {pk.th} tiles of {args.tile:g}, {len(full):,} not empty, grid {args.grid}')
    if args.probe:
        ids = np.random.default_rng(0).choice(full, size=min(120, len(full)), replace=False)
        old = new = 0
        errs = []
        for i in ids:
            n, blob, e, em = pk.pack(int(i))
            old += naive_size(n)
            new += len(blob)
            errs.append((e, em))
        e = np.array(errs)
        log(f'sample: {new / old:.3f} of float32 records; color error mean {e[:, 0].mean():.2f}/255, '
            f'max {int(e[:, 1].max())}/255')
        return 0
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    idx = np.zeros((pk.tw * pk.th, 2), np.uint32)
    off, errs, emax = 0, [], 0
    tmp = out / 'points.bin.part'
    with open(tmp, 'wb') as f, ThreadPoolExecutor(args.threads) as ex:
        for k, (i, res) in enumerate(zip(full, ex.map(pk.pack, [int(i) for i in full]))):
            n, blob, e, em = res
            idx[i] = off, n
            f.write(blob)
            off += len(blob)
            errs.append(e)
            emax = max(emax, em)
            if k and k % 500 == 0:
                log(f'tile {k:,} / {len(full):,}: {off / 1e6:.1f} MB so far')
    if off >= 2 ** 32:
        sys.exit('points.bin passed 4 GB, which a u32 index cannot address; use larger --tile or split the layer')
    empty = idx[:, 1] == 0
    idx[empty, 0] = np.maximum.accumulate(np.where(empty, 0, idx[:, 0]))[empty]
    tmp.replace(out / 'points.bin')
    (out / 'points_index.bin').write_bytes(idx.astype('<u4').tobytes())
    meta = dict(format='q-planar', grid=args.grid, tile=args.tile, bbox=pk.bbox, tiles_w=pk.tw, tiles_h=pk.th,
                n=int(n_all), file='points.bin', index='points_index.bin')
    (out / 'points.json').write_text(json.dumps(meta, indent=1))
    log(f'points.bin {off / 1e6:.2f} MB ({off / naive_size(n_all):.3f} of float32 records); color error mean '
        f'{np.mean(errs):.2f}/255, max {emax}/255')
    return 0


def self_test():
    """Synthetic layer: pack, read back as the viewer would, and check position and color error."""
    rng = np.random.default_rng(1)
    n = 200_000
    x, y = rng.uniform(0, 1000, n), rng.uniform(0, 600, n)
    cls = (x // 200 + y // 200).astype(int) % 5
    base = np.array([[230, 159, 0], [86, 180, 233], [0, 158, 115], [240, 228, 66], [204, 121, 167]])
    rgbv = np.clip(base[cls] + rng.integers(-20, 20, (n, 3)), 0, 255)
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / 'layer.npz'
        np.savez(src, x=x, y=y, r=rgbv[:, 0], g=rgbv[:, 1], b=rgbv[:, 2], type=cls)
        a = argparse.Namespace(points=str(src), out_dir=str(Path(d) / 'out'), tile=128.0, grid=4096, probe=False,
                               threads=4)
        run(a)
        meta = json.loads((Path(d) / 'out/points.json').read_text())
        idx = np.frombuffer((Path(d) / 'out/points_index.bin').read_bytes(), '<u4').reshape(-1, 2)
        blob = (Path(d) / 'out/points.bin').read_bytes()
        shift = 16 - int(np.log2(meta['grid']))
        got = 0
        worst_pos = 0.0
        for i in np.flatnonzero(idx[:, 1]):
            a0, cnt = int(idx[i, 0]), int(idx[i, 1])
            nxt = idx[i + 1:, 0][idx[i + 1:, 1] > 0]
            b0 = int(nxt[0]) if len(nxt) else len(blob)
            s = np.frombuffer(gzip.decompress(blob[a0:b0]), np.uint8).astype(np.int64)
            xs = ((s[:cnt] | (s[cnt:2 * cnt] << 8)) << shift) | ((1 << shift) >> 1)
            ys = (np.cumsum(s[2 * cnt:3 * cnt] | (s[3 * cnt:4 * cnt] << 8)) << shift) | ((1 << shift) >> 1)
            jx, jy = i % meta['tiles_w'], i // meta['tiles_w']
            ux = meta['bbox'][0] + (jx + xs / 65536) * meta['tile']
            uy = meta['bbox'][1] + (jy + ys / 65536) * meta['tile']
            # nearest source point in the same tile must be within half a grid cell diagonal
            inside = (np.minimum(((x - meta['bbox'][0]) // meta['tile']), meta['tiles_w'] - 1) == jx) & \
                     (np.minimum(((y - meta['bbox'][1]) // meta['tile']), meta['tiles_h'] - 1) == jy)
            sx, sy = np.sort(x[inside]), np.sort(y[inside])
            worst_pos = max(worst_pos, float(np.abs(np.sort(ux) - sx).max()), float(np.abs(np.sort(uy) - sy).max()))
            got += cnt
        cell = meta['tile'] / meta['grid']
        ok = got == n and worst_pos <= cell
        print(f'self-test: {got:,} of {n:,} points read back; worst position error {worst_pos:.4f} '
              f'(one grid cell is {cell:.4f}): {"PASS" if ok else "FAIL"}')
        return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('points', nargs='?', help='.npz or .csv with x, y, r, g, b and optional type')
    ap.add_argument('out_dir', nargs='?', help='folder for points.bin, points_index.bin, points.json')
    ap.add_argument('--tile', type=float, default=128.0, help='side of one chunk in the unit of x and y (default 128)')
    ap.add_argument('--grid', type=int, default=4096, help='positions per tile side, a power of two (default 4096)')
    ap.add_argument('--probe', action='store_true', help='report size and color error on a sample, write nothing')
    ap.add_argument('--threads', type=int, default=6)
    ap.add_argument('--self-test', action='store_true', help='pack a synthetic layer and check the round trip')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.points or (not a.out_dir and not a.probe):
        ap.error('POINTS and OUT_DIR are required (OUT_DIR not needed with --probe)')
    return run(a)


if __name__ == '__main__':
    sys.exit(main())

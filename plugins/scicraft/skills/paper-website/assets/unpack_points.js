// Viewer side of scripts/pack_points.py and scripts/build_masks.py. No dependencies. Copy into public/.
//
//   import { loadIndex, fetchChunk, unpackPoints, unpackMasks } from './unpack_points.js';
//   const meta = await (await fetch('data/points/points.json')).json();
//   const index = await loadIndex('data/points/' + meta.index);
//   const raw = await fetchChunk('data/points/' + meta.file, index, tile);     // gunzipped bytes of one tile
//   const gpu = unpackPoints(raw, index[2 * tile + 1], meta.grid);
//
// unpackPoints returns one ArrayBuffer in the GPU layout the viewer draws, planar: u16 x[n], u16 y[n], u8 r[n], g[n],
// b[n], type[n]. x and y run over 0..65535 across the tile, each at the center of its grid cell, so the vertex shader
// maps a point to the page with  tileOrigin + tile * (x / 65536).

// u32 (offset, count) per tile.
export async function loadIndex(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return new Uint32Array(await r.arrayBuffer());
}

// One tile's bytes by HTTP range, gunzipped in the browser (DecompressionStream). The end of a tile is the offset of
// the next tile that has points; empty tiles carry a monotone offset, so the next larger offset is the end.
export async function fetchChunk(url, index, tile) {
  const a = index[2 * tile];
  if (!index[2 * tile + 1]) return new Uint8Array(0);
  let b = null;
  for (let k = tile + 1; 2 * k < index.length; k++) if (index[2 * k + 1] && index[2 * k] > a) { b = index[2 * k] - 1; break; }
  const r = await fetch(url, { headers: { Range: `bytes=${a}-${b ?? ''}` } });
  if (r.status !== 206 && r.status !== 200) throw new Error(`${url}: ${r.status}`);
  let buf = new Uint8Array(await r.arrayBuffer());
  if (r.status === 200) buf = buf.subarray(a, b == null ? undefined : b + 1);     // a server without ranges
  const out = new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream('gzip')));
  return new Uint8Array(await out.arrayBuffer());
}

export function unpackPoints(src, n, grid = 4096) {
  const s = src instanceof Uint8Array ? src : new Uint8Array(src);
  if (s.length !== 7 * n) throw new Error(`chunk holds ${s.length} bytes, expected ${7 * n}`);
  const shift = 16 - Math.log2(grid), half = (1 << shift) >> 1;
  const out = new ArrayBuffer(8 * n);
  const x = new Uint16Array(out, 0, n), y = new Uint16Array(out, 2 * n, n), c = new Uint8Array(out, 4 * n, 4 * n);
  let yy = 0;
  for (let i = 0; i < n; i++) {
    x[i] = ((s[i] | (s[n + i] << 8)) << shift) | half;
    yy += s[2 * n + i] | (s[3 * n + i] << 8);
    y[i] = (yy << shift) | half;
    const v = s[4 * n + i] | (s[5 * n + i] << 8);
    c[i] = ((v >> 11) * 527 + 23) >> 6;                 // 5 bits to 8, as scripts/pack_points.py measures it
    c[n + i] = (((v >> 5) & 63) * 259 + 33) >> 6;       // 6 bits to 8
    c[2 * n + i] = ((v & 31) * 527 + 23) >> 6;
    c[3 * n + i] = s[6 * n + i];
  }
  return out;
}

// A masks.bin tile (scripts/build_masks.py): n vertices, three per triangle, planar i16 x, i16 y in units of
// meta.unit from the tile center, then u8 r, g, b, type. Returns Float32 positions in the data unit and the colors.
export function unpackMasks(src, n, meta, tile) {
  const s = src instanceof Uint8Array ? src : new Uint8Array(src);
  if (s.length !== 8 * n) throw new Error(`chunk holds ${s.length} bytes, expected ${8 * n}`);
  const dv = new DataView(s.buffer, s.byteOffset, s.byteLength);
  const jx = tile % meta.tiles_w, jy = Math.floor(tile / meta.tiles_w);
  const cx = meta.bbox[0] + (jx + 0.5) * meta.tile, cy = meta.bbox[1] + (jy + 0.5) * meta.tile;
  const pos = new Float32Array(2 * n);
  for (let i = 0; i < n; i++) {
    pos[2 * i] = cx + dv.getInt16(2 * i, true) * meta.unit;
    pos[2 * i + 1] = cy + dv.getInt16(2 * n + 2 * i, true) * meta.unit;
  }
  return { pos, rgbt: s.subarray(4 * n, 8 * n) };     // planar r[n], g[n], b[n], type[n]
}

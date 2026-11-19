// Drawing parts for method figures on assets/fx/core.js: the palette, plates, arrows, pulses, dots, a window of real
// data with a scale bar, and a unit sphere that turns under the pointer. Diagram parts are light plates with dark
// ink, as in a paper's figures; real data stays on the dark ground of the page.

import { clamp, lerp, text } from './core.js';

// Page tokens (assets/starter/public/site.css) and plate tokens. Add the paper's own figure colors here by name.
export const C = {
  ink: '#f4f4f5', quiet: '#9b9ba2', hair: '#3a3a40', faint: '#232327', greyPt: '#8a8a93', tile: '#0c0c0e',
  paper: '#ffffff', paperInk: '#17171a', paperQuiet: '#6a6a73', paperHair: '#c4c4cd', paperSoft: '#eeeef2',
  ours: '#8ec9ff', accent: '#2a78d6', deep: '#174a8c', rival: '#e69f00', warn: '#d9382a',
};

export function plate(ctx, x, y, w, h, o = {}) {
  const a = o.alpha ?? 1;
  if (a <= 0.003) return;
  ctx.save();
  ctx.globalAlpha *= a;
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, o.r ?? 6);
  if (o.fill !== null) { ctx.fillStyle = o.fill || C.paper; ctx.fill(); }
  if (o.stroke) { ctx.lineWidth = o.lw || 1; ctx.strokeStyle = o.stroke; if (o.dash) ctx.setLineDash(o.dash); ctx.stroke(); }
  ctx.restore();
}

// A polyline drawn up to the fraction p of its length, with a head once it is nearly complete.
export function arrow(ctx, pts, o = {}) {
  const p = clamp(o.p ?? 1), a = o.alpha ?? 1;
  if (p <= 0 || a <= 0.003) return;
  const len = [0];
  for (let i = 1; i < pts.length; i++) len.push(len[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const total = len[len.length - 1], upto = total * p, head = o.head ?? 6.5, lw = o.lw || 1.3;
  ctx.save();
  ctx.globalAlpha *= a;
  ctx.strokeStyle = ctx.fillStyle = o.color || C.ink;
  ctx.lineWidth = lw;
  ctx.lineJoin = 'round';
  if (o.dash) ctx.setLineDash(o.dash);
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  let end = pts[0], dir = [1, 0];
  for (let i = 1; i < pts.length; i++) {
    const seglen = len[i] - len[i - 1];
    if (seglen <= 0) continue;
    const f = clamp((upto - len[i - 1]) / seglen);
    if (f <= 0) break;
    dir = [(pts[i][0] - pts[i - 1][0]) / seglen, (pts[i][1] - pts[i - 1][1]) / seglen];
    end = [lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)];
    // the shaft stops short of the tip so the head stays sharp
    const cut = head && i === pts.length - 1 && f >= 1 ? head * 0.7 : 0;
    ctx.lineTo(end[0] - dir[0] * cut, end[1] - dir[1] * cut);
  }
  ctx.stroke();
  if (head && p > 0.9) {
    const s = clamp((p - 0.9) / 0.1) * head, [x, y] = end, [dx, dy] = dir;
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x - dx * s * 1.5 - dy * s * 0.62, y - dy * s * 1.5 + dx * s * 0.62);
    ctx.lineTo(x - dx * s * 1.5 + dy * s * 0.62, y - dy * s * 1.5 - dx * s * 0.62);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();
}

// A point at the fraction f along a polyline.
export function along(pts, f) {
  const len = [0];
  for (let i = 1; i < pts.length; i++) len.push(len[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const at = len[len.length - 1] * clamp(f);
  for (let i = 1; i < pts.length; i++) {
    if (at <= len[i] || i === pts.length - 1) {
      const u = (at - len[i - 1]) / ((len[i] - len[i - 1]) || 1);
      return [lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u)];
    }
  }
  return pts[0];
}

// A pulse travelling along a polyline: a short bright stroke around the fraction f.
export function pulse(ctx, pts, f, o = {}) {
  if (f <= 0 || f >= 1) return;
  const a = along(pts, f - 0.06), b = along(pts, f);
  ctx.save();
  ctx.globalAlpha *= (o.alpha ?? 1) * Math.sin(Math.PI * f);
  ctx.strokeStyle = o.color || '#fff';
  ctx.lineWidth = o.lw || 2.6;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(a[0], a[1]);
  ctx.lineTo(b[0], b[1]);
  ctx.stroke();
  ctx.restore();
}

export function dot(ctx, x, y, r, fill, o = {}) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, 6.2832);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (o.stroke) { ctx.lineWidth = o.lw || 1.2; ctx.strokeStyle = o.stroke; ctx.stroke(); }
}

// ------------------------------------------------------------------------------------------------ data window
// A square window of real data drawn into a square of the stage. D = { xy: Float32Array [x0, y0, x1, y1, ...] in data
// units with y up, half: half the window's side }. `view` picks the part shown ({x0, y0, s}); `bar` is the scale bar
// length in data units, labeled with `unit`.
export class DataWindow {
  constructor(D, x, y, side, view, unit = 'µm') {
    this.D = D;
    this.x = x; this.y = y; this.side = side; this.unit = unit;
    this.v = view || { x0: -D.half, y0: -D.half, s: 2 * D.half };
    this.k = side / this.v.s;
  }

  X(um) { return this.x + (um - this.v.x0) * this.k; }
  Y(um) { return this.y + this.side - (um - this.v.y0) * this.k; }
  px(i) { return this.X(this.D.xy[2 * i]); }
  py(i) { return this.Y(this.D.xy[2 * i + 1]); }
  um(X, Y) { return [this.v.x0 + (X - this.x) / this.k, this.v.y0 + (this.y + this.side - Y) / this.k]; }
  has(X, Y) { return X >= this.x && Y >= this.y && X <= this.x + this.side && Y <= this.y + this.side; }

  frame(ctx, alpha = 1, bar = 10) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = C.tile;
    ctx.fillRect(this.x, this.y, this.side, this.side);
    ctx.strokeStyle = C.hair;
    ctx.lineWidth = 1;
    ctx.strokeRect(this.x + 0.5, this.y + 0.5, this.side - 1, this.side - 1);
    ctx.restore();
    this.bar = bar;
  }

  // The scale bar goes on last, over the points.
  scale(ctx, alpha = 1) {
    const w = this.bar * this.k, x1 = this.x + this.side - 12, y = this.y + this.side - 13;
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = 'rgba(12,12,14,.72)';
    ctx.fillRect(x1 - w - 7, y - 19, w + 14, 27);
    ctx.fillStyle = '#fff';
    ctx.fillRect(x1 - w, y, w, 2);
    ctx.restore();
    text(ctx, `${this.bar} ${this.unit}`, x1 - w / 2, y - 6, { size: 11, align: 'center', alpha });
  }

  path(ctx, poly) {
    ctx.beginPath();
    poly.forEach(([px, py], i) => (i ? ctx.lineTo(this.X(px), this.Y(py)) : ctx.moveTo(this.X(px), this.Y(py))));
    ctx.closePath();
  }
}

// ------------------------------------------------------------------------------------------------ sphere
const mul = (A, B) => {
  const R = new Array(9);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) R[3 * i + j] = A[3 * i] * B[j] + A[3 * i + 1] * B[3 + j] + A[3 * i + 2] * B[6 + j];
  return R;
};
const axisAngle = ([x, y, z], a) => {
  const c = Math.cos(a), s = Math.sin(a), t = 1 - c;
  return [t * x * x + c, t * x * y - s * z, t * x * z + s * y, t * x * y + s * z, t * y * y + c, t * y * z - s * x, t * x * z - s * y, t * y * z + s * x, t * z * z + c];
};

// The unit sphere (for embeddings on a sphere, directions, rotations), drawn white. Directions are three-dimensional; `rot` turns them into view space, where +z faces out.
export class Globe {
  constructor(rot) { this.home = rot.slice(); this.rot = rot.slice(); this.cx = 0; this.cy = 0; this.r = 1; }

  place(cx, cy, r) { this.cx = cx; this.cy = cy; this.r = r; }
  view(x, y, z) { const R = this.rot; return [R[0] * x + R[1] * y + R[2] * z, R[3] * x + R[4] * y + R[5] * z, R[6] * x + R[7] * y + R[8] * z]; }
  // screen position and depth of a direction scaled by `len` (1 = on the surface)
  at(d, len = 1) { const v = this.view(d[0], d[1], d[2]); return [this.cx + v[0] * this.r * len, this.cy - v[1] * this.r * len, v[2] * len]; }
  has(X, Y, pad = 0) { return Math.hypot(X - this.cx, Y - this.cy) <= this.r + pad; }

  drag(dx, dy) { this.rot = mul(mul(axisAngle([0, 1, 0], dx / this.r), axisAngle([1, 0, 0], dy / this.r)), this.rot); }

  // Turn so that direction d faces the viewer by at least zmin; eased, a little each frame.
  turnTo(d, dt, zmin = 0.45) {
    const v = this.view(d[0], d[1], d[2]);
    if (v[2] >= zmin) return false;
    let ax = [-v[1], v[0], 0];                                        // z x v: turning about it raises v toward +z
    const n = Math.hypot(ax[0], ax[1]);
    ax = n < 1e-6 ? [1, 0, 0] : [ax[0] / n, ax[1] / n, 0];
    const need = Math.acos(clamp(v[2], -1, 1)) - Math.acos(zmin);
    this.rot = mul(axisAngle(ax, -need * (1 - Math.exp(-dt / 0.16))), this.rot);
    return true;
  }

  // Ease back toward a given rotation (used when a figure replays).
  settle(rot, f) { for (let i = 0; i < 9; i++) this.rot[i] = lerp(this.rot[i], rot[i], f); this.ortho(); }
  ortho() {
    const R = this.rot, n = (i) => { const l = Math.hypot(R[i], R[i + 1], R[i + 2]) || 1; R[i] /= l; R[i + 1] /= l; R[i + 2] /= l; };
    n(0);
    const d = R[0] * R[3] + R[1] * R[4] + R[2] * R[5];
    R[3] -= d * R[0]; R[4] -= d * R[1]; R[5] -= d * R[2];
    n(3);
    R[6] = R[1] * R[5] - R[2] * R[4]; R[7] = R[2] * R[3] - R[0] * R[5]; R[8] = R[0] * R[4] - R[1] * R[3];
  }

  draw(ctx, alpha = 1) {
    if (alpha <= 0.003) return;
    const { cx, cy, r } = this;
    ctx.save();
    ctx.globalAlpha *= alpha;
    const g = ctx.createRadialGradient(cx - 0.3 * r, cy - 0.36 * r, 0.04 * r, cx - 0.12 * r, cy - 0.14 * r, 1.22 * r);
    g.addColorStop(0, '#ffffff');
    g.addColorStop(0.62, '#f2f3f7');
    g.addColorStop(1, '#c3c8d6');
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, 6.2832);
    ctx.fillStyle = g;
    ctx.fill();
    // graticule on the body of the sphere, so it turns with it
    ctx.strokeStyle = 'rgba(52,62,92,.13)';
    ctx.lineWidth = 0.8;
    ctx.beginPath();
    const line = (f) => {
      let pen = false;
      for (let s = 0; s <= 48; s++) {
        const [x, y, z] = f(s / 48 * 6.2832), v = this.view(x, y, z);
        if (v[2] < 0) { pen = false; continue; }
        const X = cx + v[0] * r, Y = cy - v[1] * r;
        if (pen) ctx.lineTo(X, Y); else ctx.moveTo(X, Y);
        pen = true;
      }
    };
    for (let m = 0; m < 6; m++) { const a = m * Math.PI / 6; line((t) => [Math.cos(t) * Math.cos(a), Math.sin(t), Math.cos(t) * Math.sin(a)]); }
    for (const lat of [-0.5, 0, 0.5]) { const c = Math.cos(lat * Math.PI / 2 * 1.2), s = Math.sin(lat * Math.PI / 2 * 1.2); line((t) => [c * Math.cos(t), s, c * Math.sin(t)]); }
    ctx.stroke();
    ctx.restore();
  }

  // A vector from the centre; `len` in units of the radius. Dashed where it points away from the viewer.
  vector(ctx, d, len, o = {}) {
    const [x, y, z] = this.at(d, len);
    ctx.save();
    ctx.globalAlpha *= o.alpha ?? 1;
    ctx.strokeStyle = o.color || C.paperInk;
    ctx.lineWidth = o.lw || 1.6;
    ctx.lineCap = 'round';
    if (z < 0) ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(this.cx, this.cy);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.restore();
    return [x, y, z];
  }
}

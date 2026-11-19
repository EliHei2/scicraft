/* =====================================================================
 * canvas-schematics biology pack (load after core_lib.js)
 * ---------------------------------------------------------------------
 * Cells with character (round, elongated, spiky, irregular, lobed, blob),
 * soft pastel fills with a white spacing halo and a darker outline, nuclei,
 * molecule dots, dashed organic masks, masks that hug a point cluster,
 * ghost cells for continuity across panels, and cluster-consistent colours.
 *
 * Each cell type is {fill (soft), nuc (saturated), dot (molecule), bounds (outline)}.
 * Colour means identity. Name the types for the figure in SCENE, not here.
 * ===================================================================== */
(function () {
  'use strict';
  if (!window.LIB) throw new Error('pack_bio.js needs core_lib.js loaded first');
  const PAL = window.PAL, FONT = window.FONT, LIB = window.LIB;

  Object.assign(PAL, {
    blue:    { fill: '#d9eefb', nuc: '#3498db', dot: '#2980b9', bounds: '#2980b9' },
    green:   { fill: '#c1e1c1', nuc: '#489e34', dot: '#2d911b', bounds: '#1e6612' },
    mustard: { fill: '#fbf2d9', nuc: '#f1c40f', dot: '#e1b12c', bounds: '#b38822' },
    orange:  { fill: '#fadbb2', nuc: '#ea9f37', dot: '#d66a2b', bounds: '#c4621f' },
    teal:    { fill: '#d1efe8', nuc: '#46a596', dot: '#138774', bounds: '#0f6f5e' },
    lav:     { fill: '#e4d5f0', nuc: '#8e5db8', dot: '#6e3d9e', bounds: '#5e2d8e' },
    rose:    { fill: '#f8d9e6', nuc: '#d83a73', dot: '#b62e5f', bounds: '#9e2a55' },
    excluded:{ fill: '#eceef0', nuc: '#b4bbc2', dot: '#aeb5bd', bounds: '#b4bbc2' },
    imgBg:   '#0b0e13',   // dark field for a real image crop
    dapi:    '#3D7BFF',
    errSoft: '#ff4d4d',
    mask:    '#888888',
  });
  PAL.cells = [PAL.orange, PAL.blue, PAL.green, PAL.mustard, PAL.teal, PAL.lav, PAL.rose];

  // Chaikin corner cutting: smooths a closed polygon.
  LIB.chaikin = function (pts, iters) {
    if (iters <= 0 || pts.length < 3) return pts;
    const out = [];
    for (let i = 0; i < pts.length; i++) {
      const p0 = pts[i], p1 = pts[(i + 1) % pts.length];
      out.push({ x: 0.75 * p0.x + 0.25 * p1.x, y: 0.75 * p0.y + 0.25 * p1.y });
      out.push({ x: 0.25 * p0.x + 0.75 * p1.x, y: 0.25 * p0.y + 0.75 * p1.y });
    }
    return LIB.chaikin(out, iters - 1);
  };

  // A cell outline with character: few low-frequency lobes, smoothed, never a gear.
  // shape: 'round' | 'elong' | 'spiky' (alias 'epi') | 'irregular' | 'lobed' | 'blob'
  // opt {sx, sy, rot, n}
  LIB.cellShape = function (cx, cy, r, shape, seed, opt) {
    opt = opt || {}; const rng = LIB.rng((seed || 7) * 2654435761 >>> 0);
    const sx = opt.sx || 1, sy = opt.sy || 1, rot = opt.rot || 0, ph = rng() * 6.283;
    let n, smooth = 4;
    if (shape === 'epi' || shape === 'spiky') n = opt.n || 13;
    else if (shape === 'lobed') n = opt.n || 18;
    else if (shape === 'irregular') n = opt.n || 22;
    else n = opt.n || 30;
    const pts = [];
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2; let rx, ry;
      if (shape === 'round') { const rr = r * (1 + Math.sin(a * 3 + ph) * 0.035 + Math.cos(a * 5 + ph) * 0.03 + (rng() - 0.5) * 0.05); rx = ry = rr; }
      else if (shape === 'elong') { rx = r * (0.50 + Math.cos(a * 2) * 0.03) + (rng() - 0.5) * r * 0.04; ry = r * (1.08 + Math.sin(a) * 0.03) + (rng() - 0.5) * r * 0.05; }
      else if (shape === 'epi' || shape === 'spiky') { const rr = r * (1 + (i % 2 === 0 ? 0.17 : -0.07) + (rng() - 0.5) * 0.04); rx = ry = rr; smooth = 3; }
      else if (shape === 'lobed') { const rr = r * (1 + Math.cos(a * 3 + ph) * 0.13 + (rng() - 0.5) * 0.04); rx = ry = rr; }
      else if (shape === 'irregular') { const rr = r * (1 + Math.cos(a * 3 + ph) * 0.12 + Math.sin(a * 5 + ph * 1.7) * 0.07 + (rng() - 0.5) * 0.06); rx = ry = rr; }
      else { const rr = r * (1 + Math.sin(a * 3 + ph) * 0.10 + Math.cos(a * 5 + ph) * 0.06 + (rng() - 0.5) * 0.05); rx = ry = rr; }
      const px = Math.cos(a) * rx * sx, py = Math.sin(a) * ry * sy, ca = Math.cos(rot), sa = Math.sin(rot);
      pts.push({ x: cx + px * ca - py * sa, y: cy + px * sa + py * ca });
    }
    return LIB.chaikin(pts, smooth);
  };
  LIB.makeCell = function (cx, cy, r, n, seed, sx, sy) { return LIB.cellShape(cx, cy, r, 'blob', seed, { n: n || 34, sx: sx, sy: sy }); };

  LIB.polyPath = function (ctx, pts, close) {
    ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
    if (close !== false) ctx.closePath();
  };

  // Soft fill, then a white spacing halo, then the coloured outline.
  // opt {fill, stroke, lw (2.4), dash, halo (true), haloW (8), alpha, noFill}
  LIB.drawCell = function (ctx, pts, cType, opt) {
    opt = opt || {}; const fill = opt.fill || (cType && cType.fill), stroke = opt.stroke || (cType && cType.bounds);
    ctx.save();
    if (opt.alpha != null) ctx.globalAlpha = opt.alpha;
    LIB.polyPath(ctx, pts, true);
    if (!opt.noFill && fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (opt.halo !== false) { ctx.lineWidth = opt.haloW || 8; ctx.strokeStyle = PAL.halo; ctx.setLineDash([]); LIB.polyPath(ctx, pts, true); ctx.stroke(); }
    if (stroke) { ctx.lineWidth = opt.lw || 2.4; ctx.strokeStyle = stroke; ctx.lineJoin = 'round'; ctx.setLineDash(opt.dash || []); LIB.polyPath(ctx, pts, true); ctx.stroke(); ctx.setLineDash([]); }
    ctx.restore();
  };

  LIB.drawNucleus = function (ctx, x, y, cType, r) {
    ctx.save(); ctx.beginPath(); ctx.arc(x, y, r || 16, 0, Math.PI * 2);
    ctx.fillStyle = (cType && cType.nuc) || cType; ctx.fill(); ctx.restore();
  };

  // Molecule dot, radius 3.0 everywhere in one figure. opt {halo, errorBorder, alpha}
  LIB.drawDot = function (ctx, x, y, r, color, opt) {
    opt = opt || {}; ctx.save();
    if (opt.alpha != null) ctx.globalAlpha = opt.alpha;
    if (opt.halo) { ctx.beginPath(); ctx.arc(x, y, r + (opt.halo === true ? 1.3 : opt.halo), 0, Math.PI * 2); ctx.fillStyle = PAL.halo; ctx.fill(); }
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill();
    if (opt.errorBorder) { ctx.lineWidth = 2.2; ctx.strokeStyle = PAL.errSoft; ctx.stroke(); }
    ctx.restore();
  };
  LIB.drawSquare = function (ctx, x, y, s, color) { ctx.save(); ctx.fillStyle = color; ctx.fillRect(x - s, y - s, s * 2, s * 2); ctx.restore(); };

  // Dashed organic mask: grey [8, 6] at lw 2.5 by default; errors use PAL.err, [5, 4], lw 2.2 to 2.4.
  LIB.drawMask = function (ctx, pts, color, lw, dash) {
    ctx.save(); LIB.polyPath(ctx, pts, true);
    ctx.lineWidth = lw || 2.5; ctx.strokeStyle = color || PAL.mask; ctx.setLineDash(dash || [8, 6]); ctx.lineJoin = 'round'; ctx.stroke(); ctx.setLineDash([]); ctx.restore();
  };

  // Organic mask that hugs a cluster of points [{x, y}], padded by `padding` px.
  LIB.clusterMask = function (pts, padding) {
    let cx = 0, cy = 0; pts.forEach(t => { cx += t.x; cy += t.y; }); cx /= pts.length; cy /= pts.length;
    const N = 28, m = [];
    for (let i = 0; i < N; i++) {
      const a = (i / N) * Math.PI * 2; let maxR = padding;
      pts.forEach(t => { const proj = (t.x - cx) * Math.cos(a) + (t.y - cy) * Math.sin(a); if (proj + padding > maxR) maxR = proj + padding; });
      maxR += Math.sin(a * 3 + cx * 0.05) * 5 + Math.cos(a * 7 + cy * 0.05) * 3;
      m.push({ x: cx + Math.cos(a) * maxR, y: cy + Math.sin(a) * maxR });
    }
    return LIB.chaikin(m, 3);
  };

  // Ghost of a cell from an earlier panel, so a later panel reads as the same field.
  // opt {fillAlpha (0.10; 0.08 to 0.12 for lighter), strokeAlpha (0.30), lw (1.4)}
  LIB.ghost = function (ctx, pts, color, opt) {
    opt = opt || {}; const c = color || '#cfd6dd';
    ctx.save(); ctx.globalAlpha = opt.fillAlpha == null ? 0.10 : opt.fillAlpha; LIB.polyPath(ctx, pts, true); ctx.fillStyle = c; ctx.fill();
    ctx.globalAlpha = opt.strokeAlpha == null ? 0.30 : opt.strokeAlpha; ctx.lineWidth = opt.lw || 1.4; ctx.strokeStyle = c; ctx.setLineDash([6, 5]); ctx.stroke(); ctx.setLineDash([]); ctx.restore();
  };

  LIB.dashedRing = function (ctx, x, y, r, color, lw, dash) { ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.strokeStyle = color; ctx.lineWidth = lw || 1.6; ctx.setLineDash(dash || [6, 5]); ctx.stroke(); ctx.restore(); };

  // The one allowed radial shading: a soft density blob. Not for decoration.
  LIB.densityGlow = function (ctx, x, y, r, rgb, a0) { const g = ctx.createRadialGradient(x, y, 1, x, y, r); g.addColorStop(0, `rgba(${rgb},${a0 == null ? 0.16 : a0})`); g.addColorStop(1, `rgba(${rgb},0)`); ctx.save(); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.restore(); };

  // Cluster-consistent colours: every item takes the colour of its CLUSTER, not of
  // the order it was found in, so two separate pieces of one cluster share a colour.
  // clusterOf(item) -> cluster id or null; palette is a list of cell types.
  LIB.colorByCluster = function (items, clusterOf, palette) {
    const ids = [...new Set(items.map(clusterOf).filter(c => c != null))].sort((a, b) => (a > b ? 1 : a < b ? -1 : 0));
    const map = new Map(ids.map((id, i) => [id, palette[i % palette.length]]));
    return items.map(it => { const c = clusterOf(it); return c == null ? null : map.get(c); });
  };

  // Seeded molecules inside a cell: n dots within 0.62 r of the centre.
  LIB.scatterIn = function (cx, cy, r, n, rng) {
    const out = []; for (let k = 0; k < n; k++) { const a = rng() * Math.PI * 2, d = Math.sqrt(rng()) * r * 0.62; out.push({ x: cx + Math.cos(a) * d, y: cy + Math.sin(a) * d * 0.92 }); } return out;
  };
})();

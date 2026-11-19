/* Worked example (core library only): a datasets-used overview for a benchmark.
 * One row per dataset: group label and bracket, a group glyph, the dataset name, then a
 * row of descriptor cells. Every cell has the same size and carries its printed value;
 * the cell's opacity scales with the value inside its column (column minimum to maximum).
 * Color encodes the group (provider, platform, modality) and nothing else, so no column
 * repeats the group. Text is black at a regular weight; group labels take their group color.
 *
 * Data comes from a global (default window.DATASETS, or R.data names another global):
 *   { groups:  { key: { label, color } },
 *     columns: [ { key, label, fmt: 'int' | 'k' | 'd1' | 'd2' | 'bool' } ],   // units in label
 *     rows:    [ { label, group, <column key>: value } ],                    // sorted by group
 *     drawIcon(ctx, cx, cy, size, row, color)   optional, replaces the default glyph }
 * Group colors live in the data global because they are chosen once per paper with the data.
 * Every descriptor must come from the provider's own page; record the source per row in
 * PROVENANCE.md.
 *
 * Uses only PAL, FONT, LIB and the data global. The master draws the panel letter and title.
 * Copy it to regions/region_<id>.js and rename the function to match LAYOUT. */
function drawRegion_a(ctx, W, H, R) {
  const D = window[(R && R.data) || 'DATASETS'];
  if (!D) { LIB.text(ctx, 'no data global', 10, 30, { size: FONT.L2 }); return; }
  const F = FONT, P = PAL, cols = D.columns, rows = D.rows;

  // ---- geometry: fixed left block, cells share the rest ---------------------------
  const groupW = 150, bracketW = 14, iconW = 44, labelW = 190, gap = 6;
  const x0 = groupW + bracketW + 8, xIcon = x0 + iconW / 2, xLabel = x0 + iconW + 10;
  const xCells = xLabel + labelW, headH = 66, legendH = 52;
  const cw = Math.min(96, (W - xCells) / cols.length);
  const rh = Math.min(60, (H - headH - legendH) / rows.length);
  const cell = Math.min(cw, rh) - gap;

  // ---- column headers: two lines at most, units in parentheses -------------------
  cols.forEach((c, j) => {
    const n = LIB.text(ctx, c.label, xCells + j * cw + cw / 2, 0, { size: F.L3, align: 'center', baseline: 'top', maxWidth: cw - 4 });
    if (n > 2) console.warn('header "' + c.label + '" wraps to ' + n + ' lines; shorten it');
  });

  // ---- per-column dynamic range ---------------------------------------------------
  const range = {};
  cols.forEach(c => {
    if (c.fmt === 'bool') return;
    const v = rows.map(r => r[c.key]).filter(x => x != null);
    range[c.key] = [Math.min(...v), Math.max(...v)];
  });
  const fmt = (v, f) => f === 'k' ? (v >= 1000 ? (v / 1000).toFixed(v >= 10000 ? 0 : 1) + 'K' : String(Math.round(v)))
    : f === 'd1' ? v.toFixed(1) : f === 'd2' ? v.toFixed(2) : String(Math.round(v));
  const blendLum = (hex, a) => { const c = LIB.hex2rgb(hex).map(x => 255 + (x - 255) * a); return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255; };

  // ---- rows -----------------------------------------------------------------------
  rows.forEach((r, i) => {
    const cy = headH + i * rh + rh / 2, color = D.groups[r.group].color;
    if (typeof D.drawIcon === 'function') D.drawIcon(ctx, xIcon, cy, iconW - 12, r, color);
    else {                                   // default glyph: a small table in the group color
      const s = iconW - 18, gx = xIcon - s / 2, gy = cy - s / 2;
      LIB.frame(ctx, gx, gy, s, s, { radius: 3, fill: LIB.alpha(color, 0.12), stroke: color, lw: 1.4 });
      for (let k = 1; k < 3; k++) LIB.line(ctx, gx + 4, gy + k * s / 3, gx + s - 4, gy + k * s / 3, color, 1.2);
    }
    LIB.text(ctx, r.label, xLabel, cy, { size: F.L2, baseline: 'middle' });
    cols.forEach((c, j) => {
      const cx = xCells + j * cw + cw / 2, v = r[c.key];
      if (v == null) { LIB.text(ctx, 'n/a', cx, cy, { size: F.L3, align: 'center', baseline: 'middle' }); return; }
      if (c.fmt === 'bool') {
        ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, cell * 0.28, 0, Math.PI * 2);
        if (v) { ctx.fillStyle = color; ctx.fill(); } else { ctx.strokeStyle = color; ctx.lineWidth = 1.6; ctx.stroke(); }
        ctx.restore(); return;
      }
      const [lo, hi] = range[c.key], t = hi > lo ? (v - lo) / (hi - lo) : 1, a = 0.12 + 0.88 * t;
      LIB.roundRectPath(ctx, cx - cell / 2, cy - cell / 2, cell, cell, 4);
      ctx.fillStyle = LIB.alpha(color, a); ctx.fill();
      LIB.text(ctx, fmt(v, c.fmt), cx, cy + 1, { size: F.L3, align: 'center', baseline: 'middle', color: blendLum(color, a) < 0.5 ? P.paper : P.ink });
    });
  });

  // ---- group brackets and labels ---------------------------------------------------
  let s = 0;
  for (let i = 1; i <= rows.length; i++) {
    if (i < rows.length && rows[i].group === rows[s].group) continue;
    const g = D.groups[rows[s].group], y1 = headH + s * rh + 8, y2 = headH + i * rh - 8, bx = groupW + 4;
    ctx.save(); ctx.strokeStyle = g.color; ctx.lineWidth = 2.4; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(bx + bracketW, y1); ctx.lineTo(bx, y1); ctx.lineTo(bx, y2); ctx.lineTo(bx + bracketW, y2); ctx.stroke(); ctx.restore();
    LIB.text(ctx, g.label, groupW - 6, (y1 + y2) / 2, { size: F.L3, align: 'right', baseline: 'middle', color: g.color, maxWidth: groupW - 10 });
    s = i;
  }

  // ---- legend: what the opacity means ---------------------------------------------
  const ly = headH + rows.length * rh + legendH / 2 + 6;
  let lx = xCells;
  LIB.text(ctx, 'low', lx, ly, { size: F.L3, baseline: 'middle' });
  lx += LIB.measure(ctx, 'low', F.L3) + 8;
  [0.12, 0.34, 0.56, 0.78, 1].forEach(a => { ctx.fillStyle = LIB.alpha(P.line, a); ctx.fillRect(lx, ly - 8, 16, 16); lx += 19; });
  LIB.text(ctx, 'high, within each column', lx + 6, ly, { size: F.L3, baseline: 'middle' });
}

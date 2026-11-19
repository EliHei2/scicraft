/* =====================================================================
 * canvas-schematics core library
 * ---------------------------------------------------------------------
 * Shared by every region of one schematic figure. Region functions draw
 * through PAL (palette tokens), FONT (three text tiers plus the panel
 * letter) and LIB (drawing primitives) and never hard-code a hex or a font.
 *
 * Coordinate contract: the master canvas is laid out at 10 logical px per
 * mm (1830 px = 183 mm). 1 pt = 0.35278 mm = 3.528 logical px.
 * Tiers: LETTER 29 px (8.2 pt), L1 25 px (7.1 pt), L2 21 px (6.0 pt),
 * L3 18 px (5.1 pt, the floor). Nothing is drawn below FONT.FLOOR.
 *
 * Load order: core_lib.js, then pack_arch.js and/or pack_bio.js, then
 * layout.js, data files, region files, main.js.
 *
 * Globals: PAL, FONT, LIB
 * ===================================================================== */
(function () {
  'use strict';

  // -------------------------------------------------------------------
  // PALETTE: structure and text tokens shared by both packs.
  // All text is PAL.ink. A secondary gloss is a lighter weight, never gray.
  // -------------------------------------------------------------------
  const PAL = {
    ink:      '#1a1a1a',   // titles, primary labels, panel letters
    inkSoft:  '#5b6470',   // non-text marks only (tick stubs, faint outlines); never text
    line:     '#3a3f47',   // block borders, forward arrows
    flow:     '#999999',   // soft flow arrows between stages (#bbb is too faint in print)
    leader:   '#9aa0a6',   // thin call-out leaders
    guide:    '#D6DAE0',   // faint construction lines
    rule:     '#E4E8ED',
    paper:    '#ffffff',
    halo:     '#ffffff',   // white halo under dots and labels
    fillGrey: '#eef0f3',
    cardBg:   '#f7f9fb',
    cardStroke: '#dfe4ea',
    greyPt:   '#9aa0a6',   // neutral / noise / unassigned points
    ok:       '#2d911b',   // positive edge (solid)
    err:      '#d32f2f',   // negative edge (dashed) or error mask
    highSim:  '#FF9500',   // warm: high-similarity edge
    lowSim:   '#5AC8FA',   // cold: low-similarity edge

    // sequential ramp for magnitudes (the same ramp as the data figures)
    rank5: ['#F1F6FF', '#C7DCFF', '#8FB9FF', '#4D97FF', '#003FBD'],
    // diverging ramp for signed matrices drawn without printed values
    delta: ['#2166AC', '#F7F7F7', '#D55E00'],
    // diverging ramp with a wide white plateau, for matrices whose values are printed
    deltaPrinted: [[0, '#0A84FF'], [0.30, '#7FBDFF'], [0.43, '#D6EAFF'], [0.50, '#FFFFFF'],
                   [0.57, '#FFD9D6'], [0.70, '#FF8A80'], [1, '#FF3B30']],
  };

  // -------------------------------------------------------------------
  // TYPE: three tiers plus the panel letter, in logical px at 10 px/mm.
  // A subtitle is a lighter weight of a tier, never a fourth size.
  // -------------------------------------------------------------------
  const FONT = {
    family: "'Helvetica Neue', Helvetica, Arial, sans-serif",
    mono:   "'SF Mono', Menlo, monospace",   // code tokens only
    LETTER: 29, L1: 25, L2: 21, L3: 18,
    FLOOR: 18,                                // 5 pt at 10 px/mm
    PX_PER_MM: 10, PX_PER_PT: 3.528,
    light: 300, regular: 400, medium: 500, semibold: 600, bold: 700,
  };

  const LIB = { S: 1, _boxes: [] };

  // ---- units ---------------------------------------------------------
  LIB.mm = function (v) { return v * FONT.PX_PER_MM; };
  LIB.pt = function (v) { return v * FONT.PX_PER_PT; };

  // ---- deterministic RNG (one seed per scene, shared by all panels) --
  LIB.rng = function (seed) { let s = (seed >>> 0) || 1; return function () { s = (s * 9301 + 49297) % 233280; return s / 233280; }; };

  // ---- colour math and ramps ------------------------------------------
  LIB.hex2rgb = function (h) { h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; };
  LIB.lerp = function (a, b, t) { const A = LIB.hex2rgb(a), B = LIB.hex2rgb(b); return `rgb(${Math.round(A[0] + (B[0] - A[0]) * t)},${Math.round(A[1] + (B[1] - A[1]) * t)},${Math.round(A[2] + (B[2] - A[2]) * t)})`; };
  // stops: ['#hex', ...] evenly spaced, or [[pos, '#hex'], ...]
  LIB.ramp = function (stops, t) {
    t = Math.max(0, Math.min(1, t));
    if (Array.isArray(stops[0])) {
      for (let i = 0; i < stops.length - 1; i++) {
        const [p0, c0] = stops[i], [p1, c1] = stops[i + 1];
        if (t <= p1) return LIB.lerp(c0, c1, p1 === p0 ? 0 : (t - p0) / (p1 - p0));
      }
      return stops[stops.length - 1][1];
    }
    const seg = (stops.length - 1) * t, i = Math.min(stops.length - 2, Math.floor(seg));
    return LIB.lerp(stops[i], stops[i + 1], seg - i);
  };
  LIB.rank = function (t) { return LIB.ramp(PAL.rank5, t); };                                  // continuous
  LIB.rank5 = function (t) { return PAL.rank5[Math.max(0, Math.min(4, Math.round(t * 4)))]; };  // five steps
  LIB.delta = function (t) { return LIB.ramp(PAL.delta, t); };
  LIB.deltaPrinted = function (t) { return LIB.ramp(PAL.deltaPrinted, t); };
  LIB.alpha = function (hex, a) { const c = LIB.hex2rgb(hex); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; };

  // ---- text -----------------------------------------------------------
  // Every call records its box in canvas coordinates so render.js --check
  // can report text under the floor and text that overlaps other text.
  LIB._record = function (ctx, line, x, y, sz) {
    const m = ctx.getTransform ? ctx.getTransform() : null;
    const w = ctx.measureText(line).width;
    let x0 = x;
    if (ctx.textAlign === 'center') x0 = x - w / 2; else if (ctx.textAlign === 'right' || ctx.textAlign === 'end') x0 = x - w;
    const asc = sz * 0.72, desc = sz * 0.22;
    let top = y - asc;
    if (ctx.textBaseline === 'middle') top = y - (asc + desc) / 2;
    else if (ctx.textBaseline === 'top' || ctx.textBaseline === 'hanging') top = y;
    else if (ctx.textBaseline === 'bottom' || ctx.textBaseline === 'ideographic') top = y - asc - desc;
    const corners = [[x0, top], [x0 + w, top], [x0, top + asc + desc], [x0 + w, top + asc + desc]].map(([px, py]) =>
      m ? [(m.a * px + m.c * py + m.e) / LIB.S, (m.b * px + m.d * py + m.f) / LIB.S] : [px, py]);
    const xs = corners.map(c => c[0]), ys = corners.map(c => c[1]);
    const scale = m ? Math.hypot(m.a, m.b) / LIB.S : 1;
    LIB._boxes.push({ str: line, x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys), px: sz * scale });
  };
  // opt {size, align, baseline, weight, color, italic, mono, maxWidth, lineHeight}
  LIB.text = function (ctx, str, x, y, opt) {
    opt = opt || {}; const sz = opt.size || FONT.L3; ctx.save();
    ctx.font = `${opt.italic ? 'italic ' : ''}${opt.weight || FONT.regular} ${sz}px ${opt.mono ? FONT.mono : FONT.family}`;
    ctx.fillStyle = opt.color || PAL.ink; ctx.textAlign = opt.align || 'left'; ctx.textBaseline = opt.baseline || 'alphabetic';
    const lh = opt.lineHeight || sz * 1.3; let lines = String(str).split('\n');
    if (opt.maxWidth) lines = lines.flatMap(l => LIB._wrap(ctx, l, opt.maxWidth));
    lines.forEach((l, i) => { ctx.fillText(l, x, y + i * lh); LIB._record(ctx, l, x, y + i * lh, sz); });
    ctx.restore(); return lines.length;
  };
  LIB._wrap = function (ctx, str, maxW) { const w = str.split(' '), out = []; let cur = ''; for (const wd of w) { const t = cur ? cur + ' ' + wd : wd; if (ctx.measureText(t).width > maxW && cur) { out.push(cur); cur = wd; } else cur = t; } if (cur) out.push(cur); return out; };
  LIB.measure = function (ctx, str, size, weight, mono, italic) { ctx.save(); ctx.font = `${italic ? 'italic ' : ''}${weight || FONT.regular} ${size || FONT.L3}px ${mono ? FONT.mono : FONT.family}`; const w = ctx.measureText(str).width; ctx.restore(); return w; };
  // Italic maths with subscripts: segs [{t, sub, italic, color}]. Subscripts
  // never go below the floor, so set maths at L2 or L1.
  LIB.subSize = function (size) { return Math.max(FONT.FLOOR, Math.round(size * 0.72)); };
  LIB.math = function (ctx, x, y, segs, size, align) {
    size = size || FONT.L2; const ss = LIB.subSize(size); let total = 0;
    segs.forEach(s => { total += LIB.measure(ctx, s.t, size, FONT.regular, false, s.italic !== false) + (s.sub ? LIB.measure(ctx, s.sub, ss) + 1 : 0); });
    let px = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
    segs.forEach(s => {
      LIB.text(ctx, s.t, px, y, { size, italic: s.italic !== false, color: s.color || PAL.ink, baseline: 'middle' });
      px += LIB.measure(ctx, s.t, size, FONT.regular, false, s.italic !== false);
      if (s.sub) { LIB.text(ctx, s.sub, px + 1, y + size * 0.32, { size: ss, color: s.color || PAL.ink, baseline: 'middle' }); px += LIB.measure(ctx, s.sub, ss) + 1; }
    });
    return total;
  };

  // ---- lines and arrows -----------------------------------------------
  LIB.line = function (ctx, x1, y1, x2, y2, color, lw, dash) { ctx.save(); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.strokeStyle = color || PAL.line; ctx.lineWidth = lw || 1.2; ctx.lineCap = 'round'; ctx.setLineDash(dash || []); ctx.stroke(); ctx.restore(); };
  LIB._head = function (ctx, x2, y2, a, head) { ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - head * Math.cos(a - 0.32), y2 - head * Math.sin(a - 0.32)); ctx.lineTo(x2 - head * Math.cos(a + 0.32), y2 - head * Math.sin(a + 0.32)); ctx.closePath(); ctx.fill(); };
  // Filled-head arrow, one head shape everywhere. opt {color, lw, head, dash}.
  // A colour string in place of opt is accepted.
  LIB.arrow = function (ctx, x1, y1, x2, y2, opt) {
    if (typeof opt === 'string') opt = { color: opt };
    opt = opt || {}; const color = opt.color || PAL.line, lw = opt.lw || 2.0, head = opt.head || lw * 3.4; ctx.save();
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineCap = 'round';
    const a = Math.atan2(y2 - y1, x2 - x1), bx = x2 - head * 0.85 * Math.cos(a), by = y2 - head * 0.85 * Math.sin(a);
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(bx, by); ctx.lineWidth = lw; ctx.setLineDash(opt.dash || []); ctx.stroke(); ctx.setLineDash([]);
    LIB._head(ctx, x2, y2, a, head); ctx.restore();
  };
  // Orthogonal arrow. mode 'hv' (horizontal first) or 'vh'.
  LIB.elbow = function (ctx, x1, y1, x2, y2, mode, opt) {
    opt = opt || {}; const color = opt.color || PAL.line, lw = opt.lw || 2.0, head = opt.head || lw * 3.4; ctx.save();
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.setLineDash(opt.dash || []);
    const a = mode === 'vh' ? (x2 > x1 ? 0 : Math.PI) : (y2 > y1 ? Math.PI / 2 : -Math.PI / 2);
    ctx.beginPath(); ctx.moveTo(x1, y1);
    if (mode === 'vh') ctx.lineTo(x1, y2); else ctx.lineTo(x2, y1);
    ctx.lineTo(x2 - head * 0.85 * Math.cos(a), y2 - head * 0.85 * Math.sin(a)); ctx.stroke(); ctx.setLineDash([]);
    LIB._head(ctx, x2, y2, a, head); ctx.restore();
  };

  // ---- containers -----------------------------------------------------
  LIB.roundRectPath = function (ctx, x, y, w, h, r) { r = Math.min(r, w / 2, h / 2); ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); };
  // Flat frame: thin border, optional near-white fill. There is no shadow option.
  LIB.frame = function (ctx, x, y, w, h, opt) { opt = opt || {}; ctx.save(); const r = opt.radius == null ? 4 : opt.radius; LIB.roundRectPath(ctx, x, y, w, h, r); if (opt.fill !== false) { ctx.fillStyle = opt.fill || PAL.paper; ctx.fill(); } if (opt.stroke !== false) { ctx.lineWidth = opt.lw || 1.0; ctx.strokeStyle = opt.stroke || PAL.cardStroke; ctx.setLineDash(opt.dash || []); LIB.roundRectPath(ctx, x, y, w, h, r); ctx.stroke(); } ctx.restore(); };
  LIB.clipRect = function (ctx, x, y, w, h, r) { LIB.roundRectPath(ctx, x, y, w, h, r || 0); ctx.clip(); };
  // Small circled step number. Sparse use only, never in place of a panel letter.
  LIB.badge = function (ctx, x, y, r, n, opt) { opt = opt || {}; r = Math.max(r, FONT.FLOOR * 0.62); ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = opt.fill || PAL.ink; ctx.fill(); ctx.restore(); LIB.text(ctx, String(n), x, y + 0.5, { size: Math.max(FONT.FLOOR, opt.size || r * 1.3), weight: FONT.medium, align: 'center', baseline: 'middle', color: opt.color || PAL.paper }); };

  // ---- tables, matrices, ramps ------------------------------------------
  // Table-as-bars idiom: a table drawn as solid colour columns with a label above.
  LIB.colorBar = function (ctx, x, y, w, h, color, opt) { opt = opt || {}; ctx.save(); ctx.fillStyle = color; ctx.fillRect(x, y, w, h); if (opt.stroke) { ctx.lineWidth = 1; ctx.strokeStyle = opt.stroke; ctx.strokeRect(x, y, w, h); } ctx.restore(); if (opt.label) LIB.text(ctx, opt.label, x + w / 2, y - 6, { size: FONT.L3, align: 'center' }); };
  // values(r, c) -> [0, 1] or null. opt {gap, stroke, strokeW, cmap, round, printed(r,c)->string}
  LIB.heatmap = function (ctx, x, y, cw, ch, nrows, ncols, values, opt) {
    opt = opt || {}; const gap = opt.gap == null ? 1.0 : opt.gap, cmap = opt.cmap || LIB.rank;
    for (let r = 0; r < nrows; r++) for (let c = 0; c < ncols; c++) {
      const v = values(r, c), px = x + c * cw, py = y + r * ch;
      ctx.fillStyle = (v == null) ? PAL.fillGrey : cmap(v);
      if (opt.round) { LIB.roundRectPath(ctx, px + gap / 2, py + gap / 2, cw - gap, ch - gap, opt.round); ctx.fill(); } else ctx.fillRect(px + gap / 2, py + gap / 2, cw - gap, ch - gap);
      if (opt.printed && v != null) { const lum = LIB._lum(cmap(v)); LIB.text(ctx, opt.printed(r, c), px + cw / 2, py + ch / 2, { size: FONT.L3, align: 'center', baseline: 'middle', color: lum < 0.45 ? PAL.paper : PAL.ink }); }
    }
    if (opt.stroke !== false && opt.stroke) { ctx.save(); ctx.strokeStyle = opt.stroke; ctx.lineWidth = opt.strokeW || 1; ctx.strokeRect(x, y, cw * ncols, ch * nrows); ctx.restore(); }
  };
  LIB._lum = function (c) { const m = c.match(/\d+/g); const [r, g, b] = c[0] === '#' ? LIB.hex2rgb(c) : m.map(Number); return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255; };
  LIB.strip = function (ctx, x, y, w, h, n, valueFn, opt) { opt = opt || {}; const cw = w / n, cmap = opt.cmap || LIB.rank, g = opt.gap == null ? 0.6 : opt.gap; for (let i = 0; i < n; i++) { ctx.fillStyle = cmap(valueFn(i)); ctx.fillRect(x + i * cw + g / 2, y, cw - g, h); } if (opt.stroke) { ctx.save(); ctx.strokeStyle = opt.stroke; ctx.lineWidth = opt.strokeW || 1; ctx.strokeRect(x, y, w, h); ctx.restore(); } };

  // ---- points -----------------------------------------------------------
  // pts [{x, y, c, r}]. opt {r, c, halo}. The white halo keeps dots legible over dense content.
  LIB.points = function (ctx, pts, opt) {
    opt = opt || {}; ctx.save();
    pts.forEach(p => {
      const r = p.r || opt.r || 3.0;
      if (opt.halo) { ctx.beginPath(); ctx.arc(p.x, p.y, r + 1.3, 0, Math.PI * 2); ctx.fillStyle = PAL.halo; ctx.fill(); }
      ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.fillStyle = p.c || opt.c || PAL.greyPt; ctx.fill();
    });
    ctx.restore();
  };

  // ---- legend -------------------------------------------------------------
  // items [{label, color, fill, shape: 'dot'|'square'|'block'|'line'|'dash'|'ring', dash, italic}]
  // opt {horizontal, gap, itemGap, size, tx, r}
  LIB.legend = function (ctx, x, y, items, opt) {
    opt = opt || {}; const sz = Math.max(FONT.FLOOR, opt.size || FONT.L3), tx = opt.tx || 15, horiz = opt.horizontal, gap = opt.gap || (sz * 1.6), ig = opt.itemGap || 26, r = opt.r || 5;
    let cursor = horiz ? x : y;
    items.forEach(it => {
      const ix = horiz ? cursor : x, iy = horiz ? y : cursor, sh = it.shape || 'dot';
      ctx.save();
      if (sh === 'square') { ctx.fillStyle = it.color; ctx.fillRect(ix - r, iy - r, 2 * r, 2 * r); }
      else if (sh === 'block') { LIB.roundRectPath(ctx, ix - r, iy - r, 2 * r, 2 * r, 1.5); ctx.fillStyle = it.fill || PAL.fillGrey; ctx.fill(); ctx.strokeStyle = it.color; ctx.lineWidth = 1.2; ctx.stroke(); }
      else if (sh === 'line') LIB.line(ctx, ix - r - 3, iy, ix + r + 3, iy, it.color, it.lw || 2, it.dash);
      else if (sh === 'dash') LIB.line(ctx, ix - r - 3, iy, ix + r + 3, iy, it.color, it.lw || 1.6, it.dash || [4, 3]);
      else if (sh === 'ring') { ctx.beginPath(); ctx.arc(ix, iy, r, 0, Math.PI * 2); ctx.strokeStyle = it.color; ctx.lineWidth = 1.6; ctx.setLineDash(it.dash || [3, 3]); ctx.stroke(); }
      else { ctx.beginPath(); ctx.arc(ix, iy, r, 0, Math.PI * 2); ctx.fillStyle = it.color; ctx.fill(); }
      ctx.restore();
      LIB.text(ctx, it.label, ix + tx, iy, { size: sz, baseline: 'middle', italic: it.italic });
      if (horiz) cursor += tx + LIB.measure(ctx, it.label, sz, FONT.regular, false, it.italic) + ig; else cursor += gap;
    });
  };

  // ---- text audit (called by render.js --check) ----------------------------
  // Returns text drawn under the floor and pairs of text boxes that intersect
  // by more than `tol` logical px in both directions.
  LIB.checkText = function (tol) {
    tol = tol == null ? 1.5 : tol; const B = LIB._boxes, small = [], overlaps = [];
    B.forEach(b => { if (b.px < FONT.FLOOR - 0.01) small.push({ str: b.str, px: +b.px.toFixed(1) }); });
    for (let i = 0; i < B.length; i++) for (let j = i + 1; j < B.length; j++) {
      const a = B[i], b = B[j];
      const ox = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0), oy = Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0);
      if (ox > tol && oy > tol) overlaps.push({ a: a.str, b: b.str, at: [Math.round(Math.max(a.x0, b.x0)), Math.round(Math.max(a.y0, b.y0))] });
    }
    return { n: B.length, small, overlaps };
  };

  window.PAL = PAL; window.FONT = FONT; window.LIB = LIB;
})();

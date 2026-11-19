/* One small scene reused by every panel that shows the same field (input, graph, output),
 * so the figure reads as one field at several stages. Positions are normalised [0, 1]
 * (y down). Molecules come from ONE fixed seed, so every region gets identical points.
 * Never re-sample per panel or per zoom level; crop the same field instead.
 * TYPES maps the figure's own type names to pack_bio cell types: rename them here. */
(function () {
  const TYPES = { typeA: PAL.green, typeB: PAL.rose, excluded: PAL.excluded };
  const SEED = 4242;
  const CELLS = [
    { x: 0.31, y: 0.42, r: 0.150, type: 'typeA',    shape: 'spiky',     seed: 11 },
    { x: 0.56, y: 0.31, r: 0.140, type: 'typeA',    shape: 'spiky',     seed: 23 },
    { x: 0.76, y: 0.60, r: 0.130, type: 'typeB',    shape: 'round',     seed: 31 },
    { x: 0.27, y: 0.72, r: 0.120, type: 'typeB',    shape: 'elong',     seed: 47 },
    { x: 0.62, y: 0.83, r: 0.092, type: 'excluded', shape: 'irregular', seed: 59 },
  ];

  function build(seed) {
    const rng = LIB.rng(seed || SEED), mol = [], bg = [];
    CELLS.forEach((c, ci) => {
      const n = c.type === 'excluded' ? 3 : 6;
      for (let i = 0; i < n; i++) {
        const a = rng() * Math.PI * 2, d = Math.sqrt(rng()) * c.r * 0.66;
        mol.push({ x: c.x + Math.cos(a) * d, y: c.y + Math.sin(a) * d * 0.92, type: c.type, cell: ci });
      }
    });
    // one stray molecule of type A inside a type B cell: the case the figure is about
    mol.push({ x: CELLS[2].x - 0.02, y: CELLS[2].y - 0.03, type: 'typeA', cell: 2, stray: true });
    for (let i = 0; i < 11; i++) bg.push({ x: 0.06 + rng() * 0.88, y: 0.08 + rng() * 0.86 });
    return { cells: CELLS, mol, bg };
  }

  // Map the normalised scene into a local rect {x, y, w, h}; radii scale by min(w, h).
  function map(rect, pad) {
    pad = pad == null ? 0 : pad;
    const x0 = rect.x + pad, y0 = rect.y + pad, w = rect.w - pad * 2, h = rect.h - pad * 2, rr = Math.min(w, h);
    const s = build(rect.seed), px = (p) => ({ x: x0 + p.x * w, y: y0 + p.y * h });
    return {
      cells: s.cells.map(c => ({ ...c, cx: x0 + c.x * w, cy: y0 + c.y * h, R: c.r * rr, ct: TYPES[c.type] })),
      mol: s.mol.map(t => ({ ...t, ...px(t), ct: TYPES[t.type] })),
      bg: s.bg.map(px),
    };
  }

  function cellPts(mc, scale) { return LIB.cellShape(mc.cx, mc.cy, mc.R * (scale || 1), mc.shape, mc.seed); }

  window.SCENE = { TYPES, CELLS, SEED, build, map, cellPts };
})();

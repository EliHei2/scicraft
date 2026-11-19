/* Worked example (biology pack): a generic tissue panel. Region rect about 974 x 444.
 * LEFT: one tissue scene of cells with character (spiky, round, elongated, lobed), white-halo
 * spacing, coloured outlines, nuclei, molecule scatter, one dashed organic mask hugging a group
 * of cells (a tissue region), grey background molecules and four call-outs with thin leaders.
 * RIGHT: a 2 x 2 grid of small framed vignettes, one cell shape each, label below.
 * Uses only PAL, FONT and LIB. The master draws letter and title.
 * Copy it to regions/region_<id>.js and rename the function to match LAYOUT. */
function drawRegion_a(ctx, W, H, R) {
  const P = PAL;

  // ============================ LEFT: tissue scene ============================
  const SX = 0, SY = 6, SH = H - 10;
  // a loose patch of characterful cells (positions hand-placed for an organic tissue)
  const cells = [
    { x: 84,  y: 92,  r: 56, shape: 'spiky',  t: P.teal,    seed: 13 },
    { x: 196, y: 74,  r: 52, shape: 'spiky',  t: P.teal,    seed: 29 },
    { x: 140, y: 190, r: 54, shape: 'spiky',  t: P.teal,    seed: 37 },
    { x: 300, y: 128, r: 46, shape: 'round',  t: P.rose,    seed: 41 },
    { x: 92,  y: 300, r: 48, shape: 'round',  t: P.rose,    seed: 53 },
    { x: 222, y: 300, r: 62, shape: 'elong',  t: P.mustard, seed: 61, rot: -0.6 },
    { x: 340, y: 262, r: 50, shape: 'lobed',  t: P.lav,     seed: 73 },
  ];

  const rng = LIB.rng(808);
  const pts = cells.map(c => LIB.cellShape(SX + c.x, SY + c.y, c.r, c.shape, c.seed, { rot: c.rot || 0 }));
  cells.forEach((c, i) => LIB.drawCell(ctx, pts[i], c.t, { lw: 2.4, haloW: 9 }));
  cells.forEach((c) => LIB.drawNucleus(ctx, SX + c.x, SY + c.y, c.t, c.r * 0.30));

  // molecules inside each cell, in the cell's colour, plus grey background molecules
  cells.forEach((c) => {
    LIB.scatterIn(SX + c.x, SY + c.y, c.r, 5 + Math.floor(rng() * 3), rng)
      .forEach(p => LIB.drawDot(ctx, p.x, p.y, 3.0, c.t.dot, { halo: true }));
  });
  const bg = [[300, 210], [262, 40], [380, 60], [30, 200], [176, 380], [392, 178]];
  bg.forEach(([x, y]) => LIB.drawDot(ctx, SX + x, SY + y, 3.0, P.greyPt, { halo: true }));

  // one tissue region: an organic dashed mask hugging the three spiky cells
  const regionPts = [];
  [0, 1, 2].forEach(i => pts[i].forEach(p => regionPts.push(p)));
  LIB.drawMask(ctx, LIB.clusterMask(regionPts, 10), P.mask, 2.5, [8, 6]);

  // call-outs
  const callout = (lx, ly, tx, ty, label) => {
    LIB.line(ctx, lx, ly, tx, ty, P.leader, 1.0); LIB.drawDot(ctx, lx, ly, 2.0, P.leader);
    LIB.text(ctx, label, tx + (tx > lx ? 6 : -6), ty, { size: FONT.L3, color: P.ink, align: tx > lx ? 'left' : 'right', baseline: 'middle' });
  };
  callout(SX + 246, SY + 46, SX + 430, SY + 36, 'Tissue region');
  callout(SX + 300, SY + 128, SX + 430, SY + 112, 'Nucleus');
  callout(SX + 300, SY + 210, SX + 430, SY + 188, 'Background molecule');
  callout(SX + 250, SY + 322, SX + 430, SY + 262, 'Elongated cell');

  // legend
  const lgY = SY + SH - 44;
  LIB.drawSquare(ctx, SX + 14, lgY, 6, P.teal.nuc); LIB.text(ctx, 'nucleus', SX + 26, lgY, { size: FONT.L3, color: P.ink, baseline: 'middle' });
  LIB.drawSquare(ctx, SX + 14, lgY + 22, 6, P.teal.fill); LIB.text(ctx, 'cell', SX + 26, lgY + 22, { size: FONT.L3, color: P.ink, baseline: 'middle' });
  LIB.drawDot(ctx, SX + 14, lgY + 44, 4, P.teal.dot); LIB.text(ctx, 'molecule', SX + 26, lgY + 44, { size: FONT.L3, color: P.ink, baseline: 'middle' });

  // RIGHT: 2 x 2 shape vignettes. GX leaves room for the longest call-out label at L3 (18 px).
  const GX = 640, GY = 20, GW = W - GX - 6, GH = SH - 28;
  const cellW = (GW - 18) / 2, cellH = (GH - 46) / 2;
  const vign = [
    { c: 0, r: 0, label: 'Round',     shape: 'round',     t: P.rose,    seed: 12 },
    { c: 1, r: 0, label: 'Elongated', shape: 'elong',     t: P.mustard, seed: 21, rot: 0.9 },
    { c: 0, r: 1, label: 'Lobed',     shape: 'lobed',     t: P.lav,     seed: 31 },
    { c: 1, r: 1, label: 'Irregular', shape: 'irregular', t: P.blue,    seed: 47 },
  ];
  vign.forEach((v, idx) => {
    const vx = GX + v.c * (cellW + 18), vy = GY + v.r * (cellH + 46);
    LIB.frame(ctx, vx, vy, cellW, cellH, { fill: P.paper, stroke: P.cardStroke, radius: 4 });
    ctx.save(); LIB.clipRect(ctx, vx, vy, cellW, cellH, 4);
    const mcx = vx + cellW / 2, mcy = vy + cellH / 2, vr = Math.min(cellW, cellH) * 0.30;
    const p = LIB.cellShape(mcx, mcy, vr, v.shape, v.seed, { rot: v.rot || 0 });
    LIB.drawCell(ctx, p, v.t, { lw: 2.2 });
    LIB.drawNucleus(ctx, mcx, mcy, v.t, vr * 0.28);
    LIB.scatterIn(mcx, mcy, vr, 5, LIB.rng(100 + idx)).forEach(q => LIB.drawDot(ctx, q.x, q.y, 3.0, v.t.dot, { halo: true }));
    ctx.restore();
    LIB.text(ctx, v.label, vx + cellW / 2, vy + cellH + 18, { size: FONT.L3, color: P.ink, align: 'center', baseline: 'middle' });
  });
}

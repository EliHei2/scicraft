/* Master: sizes the canvas, draws every region in its own translated frame, then the
 * panel letters (bold lowercase, no period) with LEFT-ALIGNED titles on the same baseline,
 * then the spine arrows between panels. No dividers, no panel background boxes, no
 * subtitles. Regions never draw their own letter or title. */
(function () {
  const { CANVAS, REGIONS, STRUCT } = LAYOUT;
  const canvas = document.getElementById('c');
  canvas.width = CANVAS.W * CANVAS.S; canvas.height = CANVAS.H * CANVAS.S;
  canvas.style.width = CANVAS.W + 'px'; canvas.style.height = CANVAS.H + 'px';
  const ctx = canvas.getContext('2d');
  LIB.S = CANVAS.S;
  ctx.setTransform(CANVAS.S, 0, 0, CANVAS.S, 0, 0);
  ctx.fillStyle = PAL.paper; ctx.fillRect(0, 0, CANVAS.W, CANVAS.H);
  const errors = [];

  for (const key of Object.keys(REGIONS)) {
    const R = REGIONS[key];
    ctx.save(); ctx.translate(R.x, R.y);
    const fn = window[R.fn];
    if (typeof fn === 'function') {
      try { fn(ctx, R.w, R.h, R); }
      catch (e) { errors.push(key + ': ' + e.message); console.error('region ' + key + ': ' + e.stack); }
    } else {
      LIB.frame(ctx, 0, 0, R.w, R.h, { fill: '#fbfcfd', stroke: PAL.guide, dash: [4, 4] });
      LIB.text(ctx, (R.fn || key) + ' pending', R.w / 2, R.h / 2, { size: FONT.L2, color: PAL.leader, align: 'center', baseline: 'middle' });
    }
    ctx.restore();
  }

  for (const key of Object.keys(REGIONS)) {
    const R = REGIONS[key], by = R.titleY || STRUCT.titleY;
    let tx = R.x;
    if (R.letter) { LIB.text(ctx, R.letter, R.x, by, { size: FONT.LETTER, weight: FONT.bold }); tx = R.x + LIB.measure(ctx, R.letter, FONT.LETTER, FONT.bold) + 12; }
    if (R.title) LIB.text(ctx, R.title, tx, by, { size: FONT.L1, weight: FONT.semibold });
  }

  (STRUCT.flow || []).forEach(g => LIB.arrow(ctx, g.x0, g.y0, g.x1, g.y1, { color: g.color || PAL.line, lw: g.lw || 2.0, head: g.head || 8 }));

  window.__RENDER_ERRORS = errors;
  document.getElementById('done-flag').style.display = 'block';
})();

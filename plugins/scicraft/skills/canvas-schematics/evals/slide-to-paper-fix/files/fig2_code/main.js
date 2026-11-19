(function () {
  const L = LAYOUT, c = document.getElementById('c');
  c.width = L.W * L.S; c.height = L.H * L.S; c.style.width = L.W + 'px'; c.style.height = L.H + 'px';
  const ctx = c.getContext('2d'); ctx.setTransform(L.S, 0, 0, L.S, 0, 0);
  ctx.fillStyle = '#F8FAFC'; ctx.fillRect(0, 0, L.W, L.H);
  LIB.text(ctx, 'Figure 2: How our model works.', L.W / 2, 90, { size: FONT.TITLE, weight: 700, align: 'center' });
  LIB.text(ctx, 'A simple overview of the training and evaluation pipeline', L.W / 2, 132, { size: 20, align: 'center', color: PAL.grey });
  Object.entries(L.regions).forEach(([k, R], i) => {
    ctx.save(); ctx.translate(R.x, R.y); window['drawRegion_' + k](ctx, R.w, R.h); ctx.restore();
    ctx.save(); ctx.fillStyle = PAL.ink; ctx.beginPath(); ctx.arc(R.x + 6, R.y - 26, 20, 0, 7); ctx.fill(); ctx.restore();
    LIB.text(ctx, String(i + 1), R.x + 6, R.y - 19, { size: 22, weight: 700, align: 'center', color: '#fff' });
  });
  document.getElementById('done-flag').style.display = 'block';
})();

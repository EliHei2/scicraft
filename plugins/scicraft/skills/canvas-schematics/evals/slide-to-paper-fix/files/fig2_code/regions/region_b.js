function drawRegion_b(ctx, W, H) {
  LIB.card(ctx, 0, 0, W, H);
  LIB.text(ctx, 'Step 2: Downstream use', 30, 60, { size: FONT.H2, weight: 600 });
  LIB.text(ctx, 'the encoder is frozen and a probe is trained', 30, 92, { size: FONT.BODY, color: PAL.grey });
  const g = ctx.createLinearGradient(0, 140, 0, 300); g.addColorStop(0, '#93C5FD'); g.addColorStop(1, '#3B82F6');
  ctx.fillStyle = g; ctx.beginPath(); ctx.roundRect(60, 160, 200, 140, 16); ctx.fill();
  LIB.text(ctx, 'Frozen encoder', 160, 238, { size: 24, weight: 600, align: 'center', color: '#ffffff' });
  LIB.arrow(ctx, 270, 230, 330, 230);
  LIB.card(ctx, 340, 160, 170, 140, '#F5F3FF');
  LIB.text(ctx, 'Linear probe', 425, 238, { size: 24, weight: 600, align: 'center', color: PAL.purple });
  LIB.text(ctx, 'accuracy on held-out labels', 425, 330, { size: FONT.SMALL, align: 'center', color: PAL.grey });
}

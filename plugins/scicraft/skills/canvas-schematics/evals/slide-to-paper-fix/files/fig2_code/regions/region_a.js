function drawRegion_a(ctx, W, H) {
  const g = ctx.createLinearGradient(0, 0, W, 0); g.addColorStop(0, '#EEF2FF'); g.addColorStop(1, '#FDF4FF');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, 70);
  LIB.text(ctx, 'Step 1: The model learns to reconstruct masked inputs.', 24, 46, { size: FONT.H2, weight: 600 });
  const boxes = [['Masked input', 30, PAL.grey], ['Encoder', 300, PAL.blue], ['Latent z', 570, PAL.purple], ['Decoder', 840, PAL.blue]];
  boxes.forEach(([label, x, c]) => {
    LIB.card(ctx, x, 260, 220, 160);
    LIB.text(ctx, label, x + 110, 345, { size: 28, weight: 600, align: 'center', color: c });
    LIB.text(ctx, 'transformer block', x + 110, 380, { size: FONT.SMALL, align: 'center', color: PAL.grey });
  });
  LIB.pill(ctx, 'NEW', 330, 240, PAL.orange);
  for (let i = 0; i < 3; i++) LIB.arrow(ctx, 250 + i * 270, 340, 296 + i * 270, 340);
  LIB.card(ctx, 300, 520, 760, 120, '#FFF7ED');
  LIB.text(ctx, 'Reconstruction loss', 680, 575, { size: 28, weight: 600, align: 'center', color: PAL.orange });
  LIB.text(ctx, 'compares the decoder output with the original unmasked input values', 680, 610, { size: FONT.SMALL, align: 'center', color: PAL.grey });
}

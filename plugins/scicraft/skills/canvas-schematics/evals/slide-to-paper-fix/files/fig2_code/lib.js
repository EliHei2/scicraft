// shared helpers for figure 2
window.PAL = { ink: '#222222', grey: '#999999', blue: '#3B82F6', purple: '#8B5CF6', orange: '#F59E0B', card: '#ffffff' };
window.FONT = { family: "'Helvetica Neue', Helvetica, Arial, sans-serif", TITLE: 44, H2: 30, BODY: 16, SMALL: 13 };
window.LIB = {
  text(ctx, s, x, y, o) { o = o || {}; ctx.save(); ctx.font = `${o.weight || 400} ${o.size || FONT.BODY}px ${FONT.family}`; ctx.fillStyle = o.color || PAL.ink; ctx.textAlign = o.align || 'left'; ctx.textBaseline = o.baseline || 'alphabetic'; ctx.fillText(s, x, y); ctx.restore(); },
  card(ctx, x, y, w, h, fill) { ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.25)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 6; ctx.fillStyle = fill || PAL.card; ctx.beginPath(); ctx.roundRect(x, y, w, h, 18); ctx.fill(); ctx.restore(); },
  pill(ctx, s, x, y, color) { ctx.save(); ctx.font = `600 13px ${FONT.family}`; const w = ctx.measureText(s).width + 24; ctx.fillStyle = color; ctx.beginPath(); ctx.roundRect(x, y - 14, w, 24, 12); ctx.fill(); ctx.fillStyle = '#fff'; ctx.fillText(s, x + 12, y + 3); ctx.restore(); },
  arrow(ctx, x1, y1, x2, y2, color) { ctx.save(); ctx.strokeStyle = color || '#bbbbbb'; ctx.fillStyle = color || '#bbbbbb'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - 14, y2); ctx.stroke(); ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - 18, y2 - 10); ctx.lineTo(x2 - 18, y2 + 10); ctx.fill(); ctx.restore(); },
};

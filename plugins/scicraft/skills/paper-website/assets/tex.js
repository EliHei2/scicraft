// TeX labels for canvas figures and running text, filled from the glyph outlines that scripts/tex_labels.py writes.
// No dependencies. Copy into public/ next to the figure code.
//
//   import { loadTex, tex, texBox, upgradeTex } from './tex.js';
//   await loadTex('data/tex.json');
//   tex(ctx, 'loss', 120, 80, { size: 18, align: 'center', color: '#f4f4f5' });   // (x, y) is the baseline point
//   upgradeTex(document);       // every [data-tex="id"] element gets its label as inline SVG; its text stays for screen readers
let TEX = null;
const outline = [];

export async function loadTex(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  TEX = await r.json();
  return TEX;
}
const glyph = (i) => outline[i] || (outline[i] = new Path2D(TEX.glyphs[i]));

// Size of a label set at `size` px per 10 pt em.
export function texBox(id, size = 16) {
  const L = TEX.labels[id], k = size / 10;
  if (!L) throw new Error(`no TeX label "${id}"`);
  return { w: L.w * k, h: L.h * k, b: L.b * k };
}

// Fill a label. (x, y) is its baseline point: left, centre or right along x; `valign: 'middle'` centres the box on y.
export function tex(ctx, id, x, y, o = {}) {
  const L = TEX.labels[id];
  if (!L) throw new Error(`no TeX label "${id}"`);
  const size = o.size || 16, k = size / 10, a = o.alpha ?? 1;
  if (a <= 0.003) return L.w * k;
  const x0 = x - (o.align === 'center' ? L.w * k / 2 : o.align === 'right' ? L.w * k : 0);
  const y0 = o.valign === 'middle' ? y - L.h * k / 2 : o.valign === 'top' ? y : y - L.b * k;
  ctx.save();
  ctx.globalAlpha *= a;
  ctx.fillStyle = o.color || '#f4f4f5';
  ctx.translate(x0, y0);
  ctx.scale(k, k);
  const g = L.g;
  for (let i = 0; i < g.length; i += 4) {
    ctx.save();
    ctx.translate(g[i + 2], g[i + 3]);
    ctx.scale(g[i + 1], -g[i + 1]);
    ctx.fill(glyph(g[i]));
    ctx.restore();
  }
  if (L.l) {
    ctx.strokeStyle = ctx.fillStyle;
    for (let i = 0; i < L.l.length; i += 5) {
      ctx.lineWidth = L.l[i + 4];
      ctx.beginPath();
      ctx.moveTo(L.l[i], L.l[i + 1]);
      ctx.lineTo(L.l[i + 2], L.l[i + 3]);
      ctx.stroke();
    }
  }
  ctx.restore();
  return L.w * k;
}

// The same label as an inline SVG for running text; it takes the text colour.
export function texSVG(id, size = 16) {
  const L = TEX.labels[id], k = size / 10;
  const g = L.g, parts = [];
  for (let i = 0; i < g.length; i += 4) parts.push(`<path transform="translate(${g[i + 2]} ${g[i + 3]}) scale(${g[i + 1]} ${-g[i + 1]})" d="${TEX.glyphs[g[i]]}"/>`);
  if (L.l) for (let i = 0; i < L.l.length; i += 5) parts.push(`<path d="M${L.l[i]} ${L.l[i + 1]}L${L.l[i + 2]} ${L.l[i + 3]}" fill="none" stroke="currentColor" stroke-width="${L.l[i + 4]}"/>`);
  const span = document.createElement('span');
  span.className = 'tex';
  span.innerHTML = `<svg viewBox="0 0 ${L.w} ${L.h}" width="${(L.w * k).toFixed(2)}" height="${(L.h * k).toFixed(2)}" fill="currentColor" aria-hidden="true" style="vertical-align:${(-(L.h - L.b) * k).toFixed(2)}px">${parts.join('')}</svg>`;
  return span;
}

// Every [data-tex] element in `root` gets its label; its text stays for screen readers and for a page without script.
export function upgradeTex(root = document) {
  for (const e of root.querySelectorAll('[data-tex]')) {
    if (e.dataset.texDone || !TEX.labels[e.dataset.tex]) continue;
    const label = e.textContent;
    e.textContent = '';
    e.appendChild(texSVG(e.dataset.tex, Number(e.dataset.size) || 17));
    if (label) e.setAttribute('aria-label', label);
    e.setAttribute('role', 'img');
    e.dataset.texDone = '1';
  }
}

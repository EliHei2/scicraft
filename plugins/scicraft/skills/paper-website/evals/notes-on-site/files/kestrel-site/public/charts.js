// Result figures drawn from data/results.json as plain SVG, with no dependencies. Each chart plays once when it comes
// into view and redraws at its final state when its column changes width. A chart inside a closed row is drawn when
// the row opens. Names of terms (tasks, metrics) carry their definition under the pointer.
//
// results.json is written by pipeline/build_results.py from the paper's records. Nothing here is typed by hand. The
// starter's own results.json holds synthetic example data from a seeded generator, not the numbers of any paper.

const NS = 'http://www.w3.org/2000/svg';
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const C = { ours: '#8ec9ff', rival: '#e69f00', other: '#5c5c64', axis: '#3a3a42', ground: '#141416' };
const clamp01 = (x) => Math.max(0, Math.min(1, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = (t) => 1 - Math.pow(1 - t, 3);
const back = (x) => { const s = 1.7, t = x - 1; return 1 + t * t * ((s + 1) * t + s); };      // ease out, a little past 1
const num = (v, d = 3) => { const s = Math.abs(v).toFixed(d).replace(/^0\./, '.'); return (v < 0 ? '−' : '') + s; };      // .42, −.07: as papers print scores
function svgEl(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function text(parent, x, y, s, attrs = {}) {
  const e = svgEl('text', { x, y, ...attrs }, parent);
  e.textContent = s;
  return e;
}

// One chart: build(width, root) draws it and returns frame(p), p in [0, 1].
function chart(root, build, duration) {
  let played = false, width = 0, frame = () => {};
  const draw = (p) => {
    root.textContent = '';
    width = root.clientWidth;
    if (!width) { frame = () => {}; return; }               // inside a closed row: drawn when it opens
    frame = build(width, root);
    frame(p);
  };
  const play = () => {
    played = true;
    if (reduced) { frame(1); return; }
    const t0 = performance.now();
    const step = (now) => { const p = Math.min(1, (now - t0) / duration); frame(p); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  };
  draw(reduced ? 1 : 0);
  new ResizeObserver(() => { if (Math.abs(root.clientWidth - width) > 4) draw(played ? 1 : 0); }).observe(root);
  const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { io.disconnect(); play(); } }, { threshold: 0.35 });
  io.observe(root);
}

// a small label that follows a mark inside one chart
function tipBox(root) {
  const tip = document.createElement('div'), strong = document.createElement('b'), sub = document.createElement('span');
  tip.className = 'ch-tip';
  tip.append(strong, sub);
  root.appendChild(tip);
  return {
    show(x, y, a, b) {
      strong.textContent = a;
      sub.textContent = b || '';
      tip.classList.add('on');
      const w = tip.offsetWidth, W = root.clientWidth;
      tip.style.left = `${Math.max(w / 2, Math.min(W - w / 2, x))}px`;
      tip.style.top = `${y}px`;
    },
    hide() { tip.classList.remove('on'); },
  };
}

// ------------------------------------------------------------------------------------ bars from a baseline
// One bar per method from the baseline's value to its own: the paper's method in its colour, the strongest
// comparator in orange, the rest grey. No interval marks: the paper's own statistics say what is significant.
function barsChart(D) {
  return (W, root) => {
    const B = D.bars, rows = B.rows, RH = 25, top = 22, BH = 13;
    const H = top + rows.length * RH + 46;
    const svg = svgEl('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, class: 'ch' }, root);
    const labelW = Math.min(150, W * 0.34), x0 = labelW + 14, plotW = W - x0 - 52;
    const x = (v) => x0 + ((v - B.min) / (B.max - B.min)) * plotW, zero = x(B.base), base = top + rows.length * RH + 4;
    svgEl('line', { x1: x0, x2: x0 + plotW, y1: base, y2: base, stroke: C.axis }, svg);
    for (const v of B.ticks) {
      svgEl('line', { x1: x(v), x2: x(v), y1: base, y2: base + 4, stroke: C.axis }, svg);
      text(svg, x(v), base + 17, v, { 'text-anchor': 'middle', class: 'tick' });
    }
    text(svg, x0 + plotW / 2, base + 36, B.label, { 'text-anchor': 'middle', class: 'lab' });
    svgEl('line', { x1: zero, x2: zero, y1: top - 6, y2: base, stroke: C.axis }, svg);
    text(svg, zero, top - 10, B.baseName, { 'text-anchor': 'middle', class: 'tick' });
    const items = rows.map((r, i) => {
      const y = top + (i + 0.5) * RH, ours = r.name === D.ours, rival = r.name === D.rival;
      const g = svgEl('g', { class: 'row' }, svg);
      text(g, labelW, y + 4, r.name, { 'text-anchor': 'end', class: ours ? 'hero' : '', fill: ours ? C.ours : rival ? C.rival : null });
      const bar = svgEl('rect', { x: Math.min(zero, x(r.value)), y: y - BH / 2, height: BH, rx: 2.5, fill: ours ? C.ours : rival ? C.rival : C.other }, g);
      const val = text(g, x0 + plotW + 48, y + 4, '', { 'text-anchor': 'end', class: ours ? 'hero' : 'tick', fill: ours ? C.ours : null });
      return { r, bar, val, delay: 140 + i * 70 };
    });
    return (p) => {
      for (const it of items) {
        const l = ease(clamp01((p * 2000 - it.delay) / 900)), v = lerp(B.base, it.r.value, l);
        it.bar.setAttribute('x', Math.min(zero, x(v)));
        it.bar.setAttribute('width', Math.max(0.01, Math.abs(x(v) - zero)));
        it.val.textContent = B.dec ? v.toFixed(B.dec) : Math.round(v);
        it.val.setAttribute('opacity', clamp01(l * 2));
      }
    };
  };
}

// --------------------------------------------------------------------------- a heat map: ranks, or losses
// Rows by columns of tiles. `fill(v, col)` gives a tile's colour and ink, `label(v)` its words; a missing value is an
// empty tile. Column names carry data-term, so pointing at one shows what it is.
// Rank tiles on the dark ground: the best rank is the lightest tile. Each bucket has its own label ink. The ramp was
// validated with the dataviz method; an earlier #104281 failed its 2:1 contrast floor and was replaced.
const RAMP = ['#b7d3f6', '#5598e7', '#256abf', '#184f95', '#1c2029'];           // rank 1, 2, 3, 4 to 7, 8 and worse
const RAMP_INK = ['#0b1526', '#ffffff', '#ffffff', '#c9d6ea', '#8b8b93'];
const inkOn = (hex) => { const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((s) => (s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4)); return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.2 ? '#0b1526' : '#f1f4f9'; };
const rankBucket = (v) => (v <= 1 ? 0 : v <= 2 ? 1 : v <= 3 ? 2 : v <= 7 ? 3 : 4);
const rankFill = (v) => RAMP[rankBucket(v)];
const rankInk = (v) => RAMP_INK[rankBucket(v)];
const LOSS = ['#184f95', '#256abf', '#5598e7', '#b7d3f6'];                      // a larger loss is lighter, within its column
const lossFill = (t) => { const x = clamp01(t) * (LOSS.length - 1), i = Math.min(LOSS.length - 2, Math.floor(x)), mix = (k) => Math.round(lerp(parseInt(LOSS[i].slice(k, k + 2), 16), parseInt(LOSS[i + 1].slice(k, k + 2), 16), x - i)).toString(16).padStart(2, '0'); return `#${mix(1)}${mix(3)}${mix(5)}`; };

function tiles(root, W, { cols, rows, fill, label, tipFor, note, ink, top }) {
  const compact = W < 560, labelW = compact ? Math.min(150, W * 0.42) : 190, gridX = labelW + 12;
  const colW = Math.min(compact ? 200 : 150, (W - gridX) / cols.length), RH = compact ? 34 : 30, TOP = 34;
  const H = TOP + rows.length * RH + (note ? 30 : 8);
  const svg = svgEl('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, class: 'ch' }, root);
  const head = svgEl('g', {}, svg);
  cols.forEach((c, k) => text(head, gridX + (k + 0.5) * colW, 16, colW < 84 && c.short ? c.short : c.name, { 'text-anchor': 'middle', class: 'tick', 'data-term': c.term || null }));
  const cells = [];
  const rowEls = rows.map((r, i) => {
    const y = TOP + i * RH, g = svgEl('g', { class: 'row', 'data-i': i }, svg);
    svgEl('rect', { x: 0, y, width: W, height: RH, fill: 'transparent' }, g);
    text(g, labelW, y + RH / 2 + 4, r.name, { 'text-anchor': 'end', class: r.ours ? 'hero' : '', fill: r.ours ? C.ours : null });
    r.values.forEach((v, k) => {
      const c = svgEl('g', { 'data-k': k, class: 'cell' }, g), f = v == null ? '#19191d' : fill(v, k);
      svgEl('rect', { x: -colW / 2 + 1, y: -RH / 2 + 1, width: colW - 2, height: RH - 2, rx: 3, fill: f }, c);
      if (v != null) text(c, 0, 4, label(v, k, colW), { 'text-anchor': 'middle', fill: ink ? ink(v, k) : inkOn(f), class: top && top(v, k) ? 'cell-t top' : 'cell-t' });
      cells.push({ g: c, x: gridX + (k + 0.5) * colW, y: y + RH / 2, delay: 160 + k * 90 + i * 40 });
    });
    return g;
  });
  if (note) text(svg, compact ? W : gridX + 2, H - 8, note, { 'text-anchor': compact ? 'end' : 'start', class: 'lab' });      // on a phone it ends at the right edge, or it would run past it
  const tip = tipBox(root);
  const clear = () => { svg.classList.remove('focusing'); rowEls.forEach((q) => q.classList.remove('on')); tip.hide(); };
  svg.addEventListener('pointerover', (e) => {
    const g = e.target.closest('.row'), c = e.target.closest('.cell');
    if (!g) { clear(); return; }
    svg.classList.add('focusing');
    rowEls.forEach((q) => q.classList.toggle('on', q === g));
    if (!c) { tip.hide(); return; }
    const i = +g.dataset.i, k = +c.dataset.k, [a, b] = tipFor(rows[i], k);
    tip.show(gridX + (k + 0.5) * colW, TOP + i * RH - 3, a, b);
  });
  svg.addEventListener('pointerleave', clear);
  return (p) => {
    head.setAttribute('opacity', clamp01(p * 4));
    for (const c of cells) {
      const l = clamp01((p * 1800 - c.delay) / 520);
      c.g.setAttribute('transform', `translate(${c.x},${c.y})${l < 1 ? ` scale(${(0.35 + 0.65 * back(l)).toFixed(3)})` : ''}`);
      c.g.setAttribute('opacity', clamp01(l * 2.5));
    }
  };
}

// rank of every method on every task
function heatChart(D) {
  return (W, root) => tiles(root, W, {
    cols: D.tasks.map((t) => ({ name: t.name, short: t.short, term: t.name })),
    rows: D.heat.rows.map((r) => ({ name: r.name, ours: r.name === D.ours, values: r.ranks })),
    fill: rankFill, ink: rankInk, top: (v) => v === 1, label: (v) => String(v),
    tipFor: (r, k) => [r.values[k] == null ? 'not evaluated' : `rank ${r.values[k]}`, `${r.name} on ${D.tasks[k].name}`],
  });
}

// the largest significant loss of each part at each scale; an empty tile has none
function ablateMap(D) {
  return (W, root) => {
    const A = D.ablate, max = A.scales.map((_, k) => Math.max(...A.rows.map((r) => (r.drops[k] ? Math.abs(r.drops[k].est) : 0))));
    return tiles(root, W, {
      cols: A.scales.map((s) => ({ name: s })),
      rows: A.rows.map((r) => ({ name: r.label, values: r.drops, text: r.text })),
      fill: (d, k) => lossFill(0.12 + 0.88 * (Math.abs(d.est) / max[k])),
      label: (d, k, colW) => `${num(d.est)}${colW >= 130 ? `  ${d.task}` : ''}`,
      tipFor: (r, k) => (r.values[k] ? [`${num(r.values[k].est)}   ${r.values[k].task}`, `${r.name}, ${A.scales[k]}`] : ['no significant loss', `${r.name}, ${A.scales[k]}`]),
      note: 'an empty tile has no significant loss',
    });
  };
}

// -------------------------------------------------------------------- what a term is, under the pointer
// Every element with data-term (chart axes, the table's header) shows that term's one-line definition from the paper
// and, where it has one, its score. One tooltip for the page.
function termTips(D) {
  const terms = new Map(D.tasks.filter((t) => t.about).map((t) => [t.name, t]));
  if (!terms.size) return;
  const tip = document.createElement('div'), b = document.createElement('b'), s = document.createElement('span'), m = document.createElement('i');
  tip.className = 'term-tip';
  tip.setAttribute('role', 'tooltip');
  tip.append(b, s, m);
  document.body.appendChild(tip);
  let on = null;
  const show = (el) => {
    const t = terms.get(el.dataset.term);
    if (!t) return;
    on = el;
    b.textContent = t.name;
    s.textContent = t.about;
    m.textContent = t.metric ? `Scored by ${t.metric}.` : '';
    tip.classList.add('on');
    const r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    const above = r.top - h - 8 > 64;                     // under the name where the bar or the screen's top is in the way
    tip.style.left = `${Math.max(8, Math.min(document.documentElement.clientWidth - w - 8, r.left + r.width / 2 - w / 2))}px`;
    tip.style.top = `${above ? r.top - h - 8 : r.bottom + 8}px`;
  };
  const hide = () => { if (on) { on = null; tip.classList.remove('on'); } };
  const named = (e) => (e.target instanceof Element ? e.target.closest('[data-term]') : null);
  document.addEventListener('pointerover', (e) => { const el = named(e); if (el) show(el); else hide(); });
  document.addEventListener('focusin', (e) => { const el = named(e); if (el) show(el); });
  document.addEventListener('focusout', hide);
  addEventListener('scroll', hide, { passive: true });
}

// ---------------------------------------------------------------------------------------- the full table
function fillTable(table, D) {
  if (!table || !D.table) return;
  const T = D.table, tasks = new Set(D.tasks.map((t) => t.name));
  const head = table.createTHead().insertRow();
  for (const c of T.cols) {
    const th = document.createElement('th');
    th.textContent = c;
    if (tasks.has(c)) { th.dataset.term = c; th.tabIndex = 0; }
    head.appendChild(th);
  }
  const body = table.createTBody();
  for (const r of T.rows) {
    const tr = body.insertRow();
    if (r[0] === D.ours) tr.className = 'us';
    for (const v of r) tr.insertCell().textContent = v;
  }
}

// --------------------------------------------------------------------------------- numbers that count up
function countUp(root) {
  for (const dt of root.querySelectorAll('[data-count]')) {
    const to = +dt.dataset.count, dec = +(dt.dataset.dec || 0), unit = dt.dataset.unit || '';
    const show = (v) => { dt.textContent = (dec ? v.toFixed(dec) : Math.round(v).toLocaleString('en-US')) + unit; };
    if (reduced || !Number.isFinite(to)) { if (Number.isFinite(to)) show(to); continue; }
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      const t0 = performance.now();
      const step = (now) => { const p = Math.min(1, (now - t0) / 1300); show(to * ease(p)); if (p < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    }, { threshold: 0.6 });
    io.observe(dt);
  }
}

export async function initCharts() {
  countUp(document);
  const roots = [...document.querySelectorAll('[data-chart]')];
  let D;
  try { D = await (await fetch('data/results.json')).json(); } catch (e) { console.warn('results unavailable', e); return; }
  const kinds = { bars: [barsChart, 2000], heat: [heatChart, 2200], ablate: [ablateMap, 1800] };
  for (const r of roots) {
    const [make, dur] = kinds[r.dataset.chart] || [];
    if (make) chart(r, make(D), dur);
  }
  fillTable(document.querySelector('table[data-table]'), D);
  termTips(D);
}

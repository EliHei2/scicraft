// The page's behaviour, with no dependencies: the bar and its mark, things that rise once, rows that open on a click,
// links that open the row they point into, the divider between two renders, and the gallery (a wall and a dialog).

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const el = (tag, cls, parent, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  if (parent) parent.appendChild(e);
  return e;
};
const glide = () => (matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth');      // no gliding where motion is reduced

// ------------------------------------------------------------------------------------------------- the bar
// How far down the page is, which section is on screen, and the mark: large beside the name at the top, shrinking
// into its place in the bar as the page scrolls. It is the bar's own image that moves, so there is never a second one.
function initBar() {
  const bar = $('#bar');
  if (!bar) return;
  const mark = $('#mark'), slot = $('.mast-mark');
  const place = () => {
    if (!mark || !slot || !slot.offsetParent) { if (mark) mark.style.transform = ''; return; }
    const home = mark.parentNode.getBoundingClientRect(), w = mark.offsetWidth, h = mark.offsetHeight, s = slot.getBoundingClientRect();
    const x0 = home.left, y0 = home.top + (home.height - h) / 2;                // where the small mark rests
    const reach = s.top + scrollY - y0;                                         // the scroll at which the large one would get there
    const t = reach > 0 ? Math.min(1, Math.max(0, scrollY / reach)) : 1, e = t * t * (3 - 2 * t);
    if (t >= 1) { mark.style.transform = ''; return; }
    const k = (s.width / w) * (1 - e) + e;
    mark.style.transform = `translate(${(s.left + (x0 - s.left) * e - x0).toFixed(2)}px, ${(s.top + (y0 - s.top) * e - y0).toFixed(2)}px) scale(${k.toFixed(4)})`;
  };
  let queued = false;
  const update = () => {
    queued = false;
    const max = document.documentElement.scrollHeight - innerHeight;
    bar.style.setProperty('--p', max > 0 ? Math.min(1, scrollY / max).toFixed(4) : '0');
    bar.classList.toggle('scrolled', scrollY > 12);
    place();
  };
  addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(update); } }, { passive: true });
  addEventListener('resize', update);
  update();
  // while the name rises into place on load, and once the fonts have set its size, the mark follows its slot
  const t0 = performance.now();
  const follow = () => { place(); if (performance.now() - t0 < 1400) requestAnimationFrame(follow); };
  requestAnimationFrame(follow);
  document.fonts?.ready.then(place);
  const name = $('.mast h1');
  if (name) new IntersectionObserver(([e]) => bar.classList.toggle('past', !e.isIntersecting), { rootMargin: '-52px 0px 0px 0px' }).observe(name);
  const links = new Map($$('.top-nav a').map((a) => [a.getAttribute('href').slice(1), a]));
  const io = new IntersectionObserver((es) => {
    for (const e of es) {
      if (!e.isIntersecting) continue;
      for (const [id, a] of links) { if (id === e.target.id) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); }
    }
  }, { rootMargin: '-45% 0px -50% 0px' });                         // the section that crosses the middle of the screen
  $$('main > section[id], .hero').forEach((x) => io.observe(x));
}

// ---------------------------------------------------------------------------------- things that rise once
function initReveal() {
  const els = $$('[data-rv]');
  if (!els.length || !('IntersectionObserver' in window)) return;
  document.documentElement.classList.add('rv');
  const io = new IntersectionObserver((es) => {
    for (const e of es) if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }, { rootMargin: '0px 0px -7% 0px', threshold: 0.1 });
  els.forEach((e) => io.observe(e));
}

// ------------------------------------------------------------------------------------------------- folds
// A finding, a table or a list that stays closed until its line is clicked. When what it holds would not fit under
// the line, opening it brings the line to the top of the screen, so the figure is seen whole. A link that points at
// something inside a closed row opens it first: on load, on a click, and when the address changes later.
function unfold(t) {
  for (let d = t.closest('details'); d; d = d.parentElement && d.parentElement.closest('details')) d.open = true;
}
function initFolds() {
  for (const d of $$('details.fold')) {
    d.addEventListener('toggle', () => {
      if (!d.open) return;
      requestAnimationFrame(() => {
        if (d.getBoundingClientRect().bottom > innerHeight) $('summary', d).scrollIntoView({ behavior: glide(), block: 'start' });
      });
    });
  }
  const arrive = (scroll) => {
    const t = location.hash.length > 1 && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!t) return;
    unfold(t);
    if (scroll) t.scrollIntoView({ block: 'start' });
  };
  arrive(false);
  addEventListener('hashchange', () => arrive(true));
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    const t = a && document.getElementById(a.getAttribute('href').slice(1));
    if (!t) return;
    e.preventDefault();
    unfold(t);
    t.scrollIntoView({ behavior: glide(), block: 'start' });
    history.replaceState(null, '', `${location.pathname}${location.search}#${t.id}`);
  });
}

// ---------------------------------------------------------------------------- a divider between two renders
// The range input covers the picture, so a drag, a tap and the arrow keys all move the divider.
function initCompare(cmp) {
  const range = $('.cmp-range', cmp);
  if (!range) return () => {};
  const place = (v) => { range.value = v; cmp.style.setProperty('--pos', `${v}%`); };
  range.addEventListener('input', () => place(range.value));
  place(range.value);
  return place;
}

// ----------------------------------------------------------------------------------------------- gallery
// A wall of tiles from data/gallery/manifest.json. A click opens the comparison in a dialog over the page; inside it,
// "previous" and "next" step through the tiles in the wall's order. Escape and a click outside close it.
async function initGallery() {
  const wall = $('#wall'), ins = $('#inspector');
  if (!wall || !ins) return;
  let m;
  try { m = await (await fetch('data/gallery/manifest.json')).json(); } catch (e) { console.warn('gallery unavailable', e); return; }
  const base = 'data/gallery';
  for (const s of m.samples) {
    const b = el('button', 'tile', wall);
    b.type = 'button';
    const f = el('img', '', b);
    f.src = `${base}/${s.b}`;
    f.alt = `${s.label}, ${m.right}`;
    f.loading = 'lazy';
    const t = el('img', 'alt', b);                             // the reference shows under the pointer
    t.src = `${base}/${s.a}`;
    t.alt = '';
    t.loading = 'lazy';
    b.addEventListener('click', () => open(s));
  }
  const cmp = $('.cmp', ins), A = $('.cmp-a', ins), B = $('.cmp-b', ins), place = initCompare(cmp);
  let current = null;
  function open(s) {
    current = s;
    $('.ins-title', ins).textContent = s.label;
    $('.ins-meta', ins).textContent = s.meta || '';
    A.src = `${base}/${s.a}`;
    B.src = `${base}/${s.b}`;
    A.alt = `${s.label}, ${m.left}`;
    B.alt = `${s.label}, ${m.right}`;
    $('.cmp-tl', ins).textContent = m.left;
    $('.cmp-tr', ins).textContent = m.right;
    $('.legend', ins).innerHTML = (m.legend || []).map((t) => `<span><i style="background:${t.color}"></i>${t.name}</span>`).join('');
    place(50);
    if (!ins.open) ins.showModal();
    ins.scrollTop = 0;
  }
  const step = (d) => open(m.samples[(m.samples.indexOf(current) + d + m.samples.length) % m.samples.length]);
  $('.ins-prev', ins).addEventListener('click', () => step(-1));
  $('.ins-next', ins).addEventListener('click', () => step(1));
  $('.ins-close', ins).addEventListener('click', () => ins.close());
  ins.addEventListener('click', (e) => {                      // a click on the dimmed page around the dialog closes it
    const r = ins.getBoundingClientRect();
    if (e.target === ins && (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom)) ins.close();
  });
}

export function initPage() {
  initBar();
  initReveal();
  initFolds();
  const hero = $('.stage .cmp');
  if (hero) initCompare(hero);
  initGallery();
}

// node touch.js [width]   real touch gestures on a phone viewport, printed as PASS / FAIL lines; exits 1 if any fails.
//
// Screenshots cannot show that a gesture is swallowed. A `touch-action` on a canvas once blocked the sideways swipe
// of its scroll wrapper and fired `pointercancel` half-way through a lasso, so "draw a region" became a tap on
// phones. These checks send touches through the browser's input pipeline (CDP Input.dispatchTouchEvent), so
// `touch-action`, passive listeners and scrolling behave as on a phone:
//
//   scroll    a vertical swipe that starts on each interactive figure still scrolls the page
//   divider   a sideways drag on each divider (.cmp-range) moves it, and does not scroll the page
//   tap       a tap on each selector in TAP leaves the state that TAP_OK says (default: a tap on the first gallery
//             tile opens the dialog)
//   drag      a steep and a flat drag across each element in DRAG complete: pointerup arrives, pointercancel never
//
// FIGS (default 'canvas, .cmp, [data-chart]') names the interactive figures. DRAG (default '[data-drag]') names the
// elements that own a drag gesture (a lasso, a pan); they are left out of the scroll check, since a drag and a page
// scroll cannot start from the same place. Width defaults to 390. See _browser.js for URL, READY, SETTLE, PW_FILE.
// Rebuilt from the description of the original checks, whose code was lost; tested on the starter page only.
const { launch, open, wait, usage } = require('./_browser.js');
usage(__filename);
const W = +(process.argv[2] || 390);
const FIGS = process.env.FIGS || 'canvas, .cmp, [data-chart]';
const DRAG = process.env.DRAG || '[data-drag]';
const TAP = process.env.TAP || '#wall .tile';
const TAP_OK = process.env.TAP_OK || "document.querySelector('dialog[open]') !== null";
let fails = 0;
const check = (name, ok, detail = '') => { if (!ok) fails++; console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`); };

async function gesture(cdp, pts, ms = 16) {
  const at = ([x, y]) => [{ x: Math.round(x), y: Math.round(y), id: 1, radiusX: 4, radiusY: 4, force: 1 }];
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: at(pts[0]) });
  for (const q of pts.slice(1)) { await wait(ms); await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: at(q) }); }
  await wait(ms);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await wait(450);
}
const line = (a, b, n = 14) => Array.from({ length: n + 1 }, (_, i) => [a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]);

(async () => {
  const browser = await launch();
  const { page: p, logs } = await open(browser, W, 844);
  const cdp = await p.target().createCDPSession();
  await wait(1200);
  const n = await p.evaluate((q) => document.querySelectorAll(q).length, FIGS);
  if (!n) console.log(`NOTE  no element matches FIGS (${FIGS})`);

  // ---- a vertical swipe that starts on a figure still scrolls the page
  const stuck = [];
  for (let i = 0; i < n; i++) {
    const box = await p.evaluate((q, k, drag) => {
      const e = document.querySelectorAll(q)[k];
      if (!e.offsetParent || e.closest('details:not([open]), dialog:not([open])') || e.matches(drag)) return null;
      e.scrollIntoView({ block: 'center' });
      const r = e.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + r.height / 2, h: r.height, name: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '') };
    }, FIGS, i, DRAG);
    if (!box) continue;
    await wait(500);
    const y0 = await p.evaluate(() => scrollY);
    const d = Math.min(220, box.h * 0.4);
    await gesture(cdp, line([box.x, box.y + d / 2], [box.x, box.y - d / 2]));
    const y1 = await p.evaluate(() => scrollY);
    if (y1 - y0 < 20) stuck.push(`${box.name} moved ${Math.round(y1 - y0)} px`);
  }
  check('a vertical swipe that starts on any figure scrolls the page', !stuck.length, stuck.join('; '));

  // ---- a sideways drag on a divider moves it and leaves the page where it was
  const dividers = await p.evaluate(() => [...document.querySelectorAll('.cmp-range')].filter((r) => r.offsetParent && !r.closest('details:not([open]), dialog:not([open])')).length);
  for (let i = 0; i < dividers; i++) {
    const r = await p.evaluate((k) => {
      const e = [...document.querySelectorAll('.cmp-range')].filter((x) => x.offsetParent && !x.closest('details:not([open]), dialog:not([open])'))[k];
      e.scrollIntoView({ block: 'center' });
      const b = e.getBoundingClientRect();
      return { x: b.left, y: b.top + b.height / 2, w: b.width, v: +e.value };
    }, i);
    await wait(500);
    const y0 = await p.evaluate(() => scrollY);
    await gesture(cdp, line([r.x + r.w * 0.5, r.y], [r.x + r.w * 0.8, r.y]));
    const after = await p.evaluate((k) => ({ v: +[...document.querySelectorAll('.cmp-range')].filter((x) => x.offsetParent && !x.closest('details:not([open]), dialog:not([open])'))[k].value, y: scrollY }), i);
    check(`divider ${i + 1}: a sideways drag moves it and does not scroll the page`, after.v > r.v + 10 && Math.abs(after.y - y0) < 8, `${r.v} to ${after.v}, page moved ${Math.round(after.y - y0)} px`);
  }

  // ---- a drag along an element that owns a drag gesture completes
  const drags = await p.evaluate((q) => document.querySelectorAll(q).length, DRAG);
  for (let i = 0; i < drags; i++) {
    const r = await p.evaluate((q, k) => {
      const e = document.querySelectorAll(q)[k];
      if (!e.offsetParent) return null;
      e.scrollIntoView({ block: 'center' });
      window.__ev = [];
      for (const t of ['pointerdown', 'pointercancel', 'pointerup']) e.addEventListener(t, () => window.__ev.push(t), { once: false });
      const b = e.getBoundingClientRect();
      return { x: b.left, y: b.top, w: b.width, h: b.height };
    }, DRAG, i);
    if (!r) continue;
    const bad = [];
    for (const [name, a, b] of [['steep', [0.45, 0.15], [0.55, 0.85]], ['flat', [0.15, 0.45], [0.85, 0.55]]]) {
      await p.evaluate(() => { window.__ev = []; });
      await wait(300);
      await gesture(cdp, line([r.x + r.w * a[0], r.y + r.h * a[1]], [r.x + r.w * b[0], r.y + r.h * b[1]], 20));
      const ev = await p.evaluate(() => window.__ev);
      if (!ev.includes('pointerup') || ev.includes('pointercancel')) bad.push(`${name}: ${ev.join(' ')}`);
    }
    check(`${DRAG} ${i + 1}: a steep and a flat drag both complete without pointercancel`, !bad.length, bad.join('; '));
  }

  // ---- a tap selects, and the selection stays
  const tap = await p.evaluate((q) => { const e = document.querySelector(q); if (!e) return null; e.scrollIntoView({ block: 'center' }); const b = e.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; }, TAP);
  if (tap) {
    await wait(500);
    await p.touchscreen.tap(tap.x, tap.y);
    await wait(700);
    check(`a tap on ${TAP} leaves the expected state, and it stays`, await p.evaluate(TAP_OK), TAP_OK);
  } else console.log(`NOTE  nothing matches TAP (${TAP})`);

  console.log(logs.length ? 'CONSOLE:\n' + logs.join('\n') : 'console clean');
  if (logs.length) fails++;
  console.log(fails ? `${fails} FAILED` : 'all passed');
  await browser.close();
  process.exit(fails ? 1 : 0);
})();

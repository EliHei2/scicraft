// node shot.js <width> <height> <out-prefix> <selector|top|y=NNN> [...]
//
// Viewport screenshots of the page with each target scrolled into view. A target is a CSS selector, the word "top",
// or a scroll offset "y=600". Add "open:" before a selector to click it first (a closed row's summary, a tile):
//   node shot.js 1440 900 /tmp/site top '#results' 'open:#table > summary' y=2400
// Look at every shot with the Read tool before saying a layout is done: the audit finds measurable faults, not ugly ones.
// See _browser.js for URL, READY, SETTLE, PW_FILE.
const { launch, open, wait, usage } = require('./_browser.js');
usage(__filename);
const [W, H, prefix, ...targets] = process.argv.slice(2);
if (!targets.length) { console.error('usage: node shot.js <width> <height> <out-prefix> <selector|top|y=NNN> [...]'); process.exit(2); }

(async () => {
  const browser = await launch();
  const { page, logs } = await open(browser, +W, +H, { dpr: +W < 600 ? 2 : 1 });
  await wait(1200);
  let k = 0;
  for (let t of targets) {
    const click = t.startsWith('open:');
    if (click) t = t.slice(5);
    if (t === 'top') await page.evaluate(() => window.scrollTo(0, 0));
    else if (/^y=\d+$/.test(t)) await page.evaluate((y) => window.scrollTo(0, y), +t.slice(2));
    else {
      const found = await page.evaluate((q, c) => {
        const e = document.querySelector(q);
        if (!e) return false;
        const r = e.getBoundingClientRect();
        window.scrollTo(0, scrollY + r.top - Math.max(70, (innerHeight - r.height) / 2));
        if (c) e.click();
        return true;
      }, t, click);
      if (!found) { console.log(`not found: ${t}`); continue; }
    }
    await wait(click ? 3400 : 2600);
    const f = `${prefix}_${W}_${String(k++).padStart(2, '0')}.png`;
    await page.screenshot({ path: f });
    console.log(f);
  }
  if (logs.length) console.log('console:\n  ' + logs.join('\n  '));
  await browser.close();
})();

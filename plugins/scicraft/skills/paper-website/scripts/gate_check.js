// node gate_check.js [width]   end-to-end check of a password-gated build (gate.py), local or deployed.
//
//   URL=http://127.0.0.1:8770/ PW_FILE=pipeline/.beta_password node gate_check.js 1440
//
// The gate itself: a wrong password is refused with a message, the right one unlocks, a reload unlocks again from
// the browser's memory. Then the unlocked page, the way a co-author sees it: every chart drew (name and element
// count), every image loaded with its width, the favicon answers, the gallery tile count, the figure count, and no
// failed request and no console error. Every line of output passes through the same mask as everything else
// (24-character lowercase names, the shape of the secret folder, print as <secret>); the password is never printed.
// Serve dist/ for a local run: python3 serve.py 8770 dist.
// The page counts as unlocked when the password field is gone and READY (default: the page has a <main>) is true. Exits 1 on any failure.
// Generalized from the site's own gate test; tested on a gated build of the starter page.
const fs = require('fs');
const path = require('path');
const { launch, wait, URL, usage } = require('./_browser.js');
usage(__filename);
const W = +(process.argv[2] || 1440);
const READY = process.env.READY || "document.querySelector('main') !== null";
const UNLOCKED = `!document.getElementById('pw') && (${READY})`;          // the sign-in field is gone and the page is ready
const mask = (s) => String(s).replace(/[a-z0-9]{24}/g, '<secret>');
let fails = 0;
const check = (name, ok, detail = '') => { if (!ok) fails++; console.log(mask(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`)); };

(async () => {
  if (!process.env.PW_FILE) { console.log('set PW_FILE to the password file of the build'); process.exit(2); }
  const PW = fs.readFileSync(path.resolve(process.env.PW_FILE), 'utf8').trim();
  const browser = await launch();
  const p = await browser.newPage();
  const errs = [];
  p.on('pageerror', (e) => errs.push('pageerror ' + e.message));
  p.on('console', (m) => { if (m.type() === 'error') errs.push('console ' + m.text()); });
  p.on('requestfailed', (r) => errs.push(`failed ${r.url()}`));
  p.on('response', (r) => { if (r.status() >= 400) errs.push(`http ${r.status()} ${r.url()}`); });
  await p.setViewport({ width: W, height: W < 600 ? 844 : 900, isMobile: W < 600, hasTouch: W < 600 });
  await p.goto(URL, { waitUntil: 'load' });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) { /* private mode */ } });
  await p.reload({ waitUntil: 'load' });

  // ---- the gate
  check('the sign-in page shows a password field', !!(await p.$('#pw')));
  check('the sign-in page asks robots to stay out', await p.evaluate(async () => { try { const r = await fetch('robots.txt'); return r.ok && /Disallow:\s*\//.test(await r.text()); } catch (e) { return false; } }));
  await p.type('#pw', 'not-the-password-' + Date.now());
  await p.keyboard.press('Enter');
  await wait(2500);
  const refused = await p.evaluate(() => ({ still: !!document.getElementById('pw'), msg: (document.getElementById('msg') || {}).textContent || '' }));
  check('a wrong password is refused with a message', refused.still && refused.msg.trim().length > 0, `"${refused.msg.trim()}"`);
  await p.$eval('#pw', (e) => { e.value = ''; });
  await p.type('#pw', PW);
  await p.keyboard.press('Enter');
  let unlocked = true;
  await p.waitForFunction(UNLOCKED, { timeout: 60000 }).catch(() => { unlocked = false; });
  check('the right password unlocks the page', unlocked);
  if (!unlocked) { console.log(mask(errs.join('\n'))); await browser.close(); process.exit(1); }

  // ---- the unlocked page, walked to the end so that everything lazy has loaded
  await p.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true; }));
  for (let y = 0; ; y += 600) {
    const max = await p.evaluate(() => document.documentElement.scrollHeight - innerHeight);
    await p.evaluate((yy) => window.scrollTo(0, yy), Math.min(y, max));
    await wait(150);
    if (y >= max) break;
  }
  await wait(2000);
  const s = await p.evaluate(async () => {
    // lazy images below the fold may still be waiting: ask for every one now and wait until each is decoded or failed
    for (const i of document.images) i.loading = 'eager';
    await Promise.race([Promise.all([...document.images].map((i) => (i.src ? i.decode().catch(() => null) : null))), new Promise((r) => setTimeout(r, 15000))]);
    const icon = document.querySelector('link[rel~="icon"]');
    let iconOk = null;
    if (icon) { try { iconOk = (await fetch(icon.href)).ok; } catch (e) { iconOk = false; } }
    return {
      charts: [...document.querySelectorAll('[data-chart]')].map((d) => `${d.dataset.chart}:${d.querySelectorAll('svg *').length}`),
      images: [...document.images].map((i) => ({ src: i.currentSrc || i.src, w: i.naturalWidth, ok: i.complete && i.naturalWidth > 0, lazy: i.loading === 'lazy' })),
      iconOk, tiles: document.querySelectorAll('#wall .tile').length, figures: document.querySelectorAll('figure').length,
    };
  });
  if (s.charts.length) check('every chart drew', s.charts.every((c) => +c.split(':')[1] > 10), s.charts.join(' '));
  else console.log('NOTE  no [data-chart] element on the page');
  const broken = s.images.filter((i) => !i.ok && i.src);
  check('every image loaded', !broken.length, broken.length ? broken.map((i) => i.src.split('/').pop()).join(' ') : `${s.images.length} images, widths ${[...new Set(s.images.filter((i) => i.src).map((i) => i.w))].slice(0, 8).join(' ')}`);
  check('the favicon answers', s.iconOk !== false, s.iconOk === null ? 'no favicon link' : '');
  console.log(`INFO  ${s.tiles} gallery tile(s), ${s.figures} figure(s)`);

  // ---- a reload unlocks from memory
  await p.reload({ waitUntil: 'load' });
  let again = true;
  await p.waitForFunction(UNLOCKED, { timeout: 30000 }).catch(() => { again = false; });
  check('a reload unlocks from memory', again);

  // the browser asks for /favicon.ico by itself when a page names no icon (a sign-in page built without --icon)
  const bare = errs.some((e) => e.includes('/favicon.ico'));
  const rest = errs.filter((e) => !e.includes('/favicon.ico') && !(bare && /status of 404/.test(e) && !/https?:/.test(e)));
  if (bare) console.log('NOTE  a page names no icon, so the browser asked for /favicon.ico (build the gate with --icon)');
  check('no failed request and no console error', !rest.length, rest.slice(0, 8).join(' | '));
  console.log(fails ? `${fails} FAILED` : 'all passed');
  await browser.close();
  process.exit(fails ? 1 : 0);
})();

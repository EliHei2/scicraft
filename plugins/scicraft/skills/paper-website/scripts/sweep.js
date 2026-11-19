// node sweep.js [width ...]   every interactive figure driven through its timeline and swept by the pointer; exits 1
// on any console error, page error or failed request.
//
// A figure that plays, scrubs or answers the pointer can throw at one moment of its timeline or at one spot of its
// canvas that no screenshot visits. For each figure (FIGS, default 'canvas, [data-chart]') and each width (default
// 1440 and 390) this script:
//   1. if SEEK is set, calls it at STEPS evenly spaced moments (default 60) from 0 to 1. SEEK is a JS function body
//      with `el` (the figure) and `t` (0 to 1) in scope, for example SEEK='el.__fig && el.__fig.seek(t)';
//   2. moves a real pointer over a 12 by 6 grid of the figure, then out of it;
//   3. collects what the console reported while it did so.
// Run it again after every fix. See _browser.js for URL, READY, SETTLE, PW_FILE.
// Rebuilt from the description of the original check, whose code was lost; tested on the starter page only.
const { launch, open, wait, usage } = require('./_browser.js');
usage(__filename);
const widths = process.argv.slice(2).map(Number).filter(Boolean);
const FIGS = process.env.FIGS || 'canvas, [data-chart]';
const SEEK = process.env.SEEK || '';
const STEPS = +(process.env.STEPS || 60);

(async () => {
  const browser = await launch();
  let bad = 0;
  for (const W of widths.length ? widths : [1440, 390]) {
    const { page: p, logs } = await open(browser, W);
    if (process.env.OPEN !== '0') await p.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true; }));
    const n = await p.evaluate((q) => document.querySelectorAll(q).length, FIGS);
    let seeks = 0, moves = 0;
    for (let i = 0; i < n; i++) {
      const box = await p.evaluate((q, k) => {
        const e = document.querySelectorAll(q)[k];
        if (!e.offsetParent) return null;
        e.scrollIntoView({ block: 'center' });
        const r = e.getBoundingClientRect();
        return { x: r.left, y: r.top, w: r.width, h: r.height };
      }, FIGS, i);
      if (!box || box.w < 4 || box.h < 4) continue;
      await wait(400);
      if (SEEK) {
        for (let s = 0; s <= STEPS; s++) {
          try {
            await p.evaluate((q, k, t, body) => { const el = document.querySelectorAll(q)[k]; new Function('el', 't', body)(el, t); }, FIGS, i, s / STEPS, SEEK);
          } catch (e) { logs.push(`figure ${i + 1} at t=${(s / STEPS).toFixed(3)}: ${e.message.split('\n')[0]}`); }
          seeks++;
          if (s % 10 === 0) await wait(30);
        }
      }
      for (let gy = 0; gy < 6; gy++) for (let gx = 0; gx < 12; gx++) {
        await p.mouse.move(box.x + (gx + 0.5) * box.w / 12, box.y + (gy + 0.5) * box.h / 6);
        moves++;
      }
      await p.mouse.move(box.x - 20, box.y - 20);
      await wait(120);
    }
    console.log(`${W}px: ${n} figure(s), ${seeks} timeline step(s), ${moves} pointer position(s)`);
    for (const l of logs) console.log('  ' + l);
    bad += logs.length;
    await p.close();
  }
  await browser.close();
  console.log(bad ? `${bad} problem(s)` : 'clean');
  process.exit(bad ? 1 : 0);
})();

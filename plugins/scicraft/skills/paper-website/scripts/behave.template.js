// node behave.js [width]   behaviour checks of the page, printed as PASS / FAIL lines; exits 1 if any fails.
//
// Copy this file into the site's pipeline/ (as behave.js) and grow it with the site: every bug that is fixed gets a
// check, every rule the author sets gets a check. Run it at a desktop width and at a phone width, on the local page
// and again on the deployed one (URL=https://... PW_FILE=pipeline/.beta_password node behave.js 390).
// The generic checks below hold for any page built from the starter; project checks go where marked.
// See _browser.js for URL, READY, SETTLE, PW_FILE.
const { launch, open, walk, wait, usage } = require('./_browser.js');
usage(__filename);
const W = +(process.argv[2] || 1440);
let fails = 0;
const check = (name, ok, detail = '') => { if (!ok) fails++; console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`); };

// Words and marks the page may not show. Extend it with the author's rules (statistics wording, retired names).
const BANNED = [/·|•/, / \| /, /\b(TODO|lorem ipsum)\b/i];

(async () => {
  const browser = await launch();
  const { page: p, logs, mobile } = await open(browser, W);

  // ---- the first screen: the mark large beside the name, small in the bar after a scroll; nothing over the name
  await p.evaluate(() => window.scrollTo(0, 0));
  await wait(1700);
  const top0 = await p.evaluate(() => {
    const m = document.getElementById('mark'), s = document.querySelector('.mast-mark'), h = document.querySelector('.mast h1');
    if (!m || !s || !h) return null;
    const a = m.getBoundingClientRect(), b = s.getBoundingClientRect(), c = h.getBoundingClientRect();
    // the first words in the masthead, in reading order, must be the name: no eyebrow, tagline or claim before it
    const first = [...document.querySelectorAll('.mast *')].find((e) => !e.children.length && e.textContent.trim() && e.offsetParent);
    return { mark: [a.left, a.top, a.width].map(Math.round), slot: [b.left, b.top, b.width].map(Math.round), beside: a.right <= c.left + 1, small: m.offsetWidth, nameFirst: !!first && h.contains(first), firstWords: first ? first.textContent.trim().slice(0, 40) : '' };
  });
  if (top0) {
    await p.evaluate(() => window.scrollTo(0, 500));
    await wait(500);
    const top1 = await p.evaluate(() => { const a = document.getElementById('mark').getBoundingClientRect(); return { w: Math.round(a.width), top: Math.round(a.top) }; });
    await p.evaluate(() => window.scrollTo(0, 0));
    await wait(400);
    check('the mark stands large beside the name at the top and is small in the bar after a scroll', top0.mark.join() === top0.slot.join() && top0.mark[2] > top0.small + 8 && top0.beside && top1.w === top0.small && top1.top < 24,
      `at the top ${top0.mark.join(' ')}, after a scroll ${top1.w} px wide at y ${top1.top}`);
    check('nothing stands over the name', top0.nameFirst, top0.nameFirst ? '' : `first words: "${top0.firstWords}"`);
  }

  // ---- the divider of the first screen moves by the keyboard
  if (await p.$('.stage .cmp-range')) {
    await p.focus('.stage .cmp-range');
    const before = await p.$eval('.stage .cmp-range', (r) => +r.value);
    await p.keyboard.press('ArrowRight');
    await p.keyboard.press('ArrowRight');
    const after = await p.evaluate(() => ({ v: +document.querySelector('.stage .cmp-range').value, pos: document.querySelector('.stage .cmp').style.getPropertyValue('--pos') }));
    check('the divider moves by the arrow keys', after.v > before && after.pos === `${after.v}%`, `${before} to ${after.v}`);
  }

  // ---- every closed row opens on a click of its line, and what it holds is drawn
  const folds = await p.evaluate(async () => {
    const pause = (ms) => new Promise((r) => setTimeout(r, ms));
    const out = [];
    for (const d of document.querySelectorAll('details.fold')) {
      const was = d.open, s = d.querySelector('summary');
      s.scrollIntoView({ block: 'center' });
      s.click();
      await pause(350);
      out.push({ id: d.id, was, open: d.open, h: Math.round(d.getBoundingClientRect().height) });
    }
    return out;
  });
  check(`${folds.length} rows start closed and each opens on a click of its line`, folds.every((f) => !f.was && f.open && f.h > 100), folds.map((f) => `${f.id}:${f.h}`).join(' '));

  // ---- one pass down the page with every row open
  await p.evaluate(() => window.scrollTo(0, 0));
  await walk(p, 600);
  await wait(1500);
  const state = await p.evaluate(() => ({
    charts: [...document.querySelectorAll('[data-chart]')].map((d) => `${d.dataset.chart}:${d.querySelectorAll('svg *').length}`),
    hidden: document.querySelectorAll('[data-rv]:not(.in)').length,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    text: document.body.innerText,
    labels: [...document.querySelectorAll('[aria-label], [alt], [title]')].map((e) => `${e.getAttribute('aria-label') || ''} ${e.getAttribute('alt') || ''} ${e.getAttribute('title') || ''}`).join(' '),
    dead: [...document.querySelectorAll('a[href^="#"]')].map((a) => a.getAttribute('href')).filter((h) => h.length > 1 && !document.getElementById(h.slice(1))),
    placeholders: (document.body.innerText.match(/\[[^\]\n]{3,60}\]/g) || []).length,
  }));
  check('every chart is drawn', state.charts.length > 0 && state.charts.every((c) => +c.split(':')[1] > 10), state.charts.join(' '));
  check('everything that rises has risen, and nothing reaches past the right edge', state.hidden === 0 && state.overflow === 0, `hidden ${state.hidden}, overflow ${state.overflow}`);
  const banned = BANNED.filter((re) => re.test(state.text) || re.test(state.labels)).map(String);
  check('none of the banned words or marks is on the page', !banned.length, banned.join(' '));
  check('every link inside the page has a target', !state.dead.length, state.dead.join(' '));
  if (state.placeholders) console.log(`NOTE  ${state.placeholders} bracketed placeholder(s) are still on the page`);

  // ---- a term's definition appears under a real pointer and leaves with it
  const term = await p.evaluate(() => { const e = document.querySelector('[data-chart] [data-term]'); if (!e) return null; e.scrollIntoView({ block: 'center' }); return true; });
  if (term) {
    await wait(1200);                                              // the tooltip leaves on any scroll, so the page must be at rest
    const at = await p.evaluate(() => { const r = document.querySelector('[data-chart] [data-term]').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; });
    await p.mouse.move(at[0] - 70, at[1] - 70);
    await p.mouse.move(at[0], at[1], { steps: 6 });               // a real pointer: a synthetic event is undone by where the pointer last rested
    await wait(400);
    const on = await p.evaluate(() => { const t = document.querySelector('.term-tip'), r = t.getBoundingClientRect(); return { on: t.classList.contains('on'), words: t.textContent.length, inside: r.left >= 0 && r.top >= 0 && r.right <= document.documentElement.clientWidth }; });
    await p.mouse.move(at[0] - 160, at[1] - 260, { steps: 6 });
    await wait(300);
    const off = await p.evaluate(() => !document.querySelector('.term-tip').classList.contains('on'));
    check('pointing at a term shows its definition, inside the screen, and it leaves with the pointer', on.on && on.words > 10 && on.inside && off, JSON.stringify(on));
  }

  // ---- a link that changes while the page is open opens the row it points into
  const hop = await p.evaluate(async () => {
    const pause = (ms) => new Promise((r) => setTimeout(r, ms));
    const rows = [...document.querySelectorAll('details.fold[id]')];
    if (!rows.length) return null;
    rows.forEach((d) => { d.open = false; });
    location.hash = `#${rows[rows.length - 1].id}`;
    await pause(500);
    return { open: rows[rows.length - 1].open, others: document.querySelectorAll('details.fold[open]').length };
  });
  if (hop) check('a link that changes while the page is open opens its row', hop.open && hop.others === 1, JSON.stringify(hop));

  // ---- the gallery: a click opens the comparison over the page; previous and next wrap around; Escape closes
  if (await p.$('#wall .tile')) {
    const gal = await p.evaluate(async () => {
      const pause = (ms) => new Promise((r) => setTimeout(r, ms));
      const d = document.getElementById('inspector'), tiles = [...document.querySelectorAll('#wall .tile')], title = () => d.querySelector('.ins-title').textContent;
      const out = { tiles: tiles.length, openAtStart: d.open };
      tiles[0].click();
      await pause(500);
      const r = d.getBoundingClientRect(), a = d.querySelector('.cmp-tl').getBoundingClientRect(), b = d.querySelector('.cmp-tr').getBoundingClientRect();
      out.first = { open: d.open, title: title(), locked: getComputedStyle(document.documentElement).overflowY === 'hidden', inside: r.left >= 0 && r.top >= 0 && r.right <= innerWidth + 0.5 && r.bottom <= innerHeight + 0.5,
        apart: a.right <= b.left || b.right <= a.left || a.bottom <= b.top || b.bottom <= a.top,
        under: d.querySelector('.ins-head').getBoundingClientRect().top >= d.querySelector('.cmp').getBoundingClientRect().bottom - 0.5 || d.querySelector('.ins-head').getBoundingClientRect().left >= d.querySelector('.cmp').getBoundingClientRect().right - 0.5 };
      d.querySelector('.ins-prev').click();
      await pause(250);
      out.prev = title();
      d.querySelector('.ins-next').click();
      d.querySelector('.ins-next').click();
      await pause(250);
      out.next = title();
      return out;
    });
    await p.keyboard.press('Escape');
    await wait(400);
    const closed = await p.evaluate(() => !document.getElementById('inspector').open && getComputedStyle(document.documentElement).overflowY !== 'hidden');
    check('the gallery starts with nothing open, and a click on a tile opens the comparison over the page', !gal.openAtStart && gal.first.open && gal.first.locked && gal.first.inside, JSON.stringify(gal.first));
    check('in the dialog the two labels never meet and the title is never under the picture', gal.first.apart && gal.first.under);
    check('previous and next walk the wall around its ends, and Escape closes', gal.prev !== gal.first.title && gal.next !== gal.first.title && gal.next !== gal.prev && closed, `${gal.prev} / ${gal.first.title} / ${gal.next}`);
  }

  // ---- project checks: the numbers on the page, the paper's sentences, the viewer, anything that once broke
  // check('the pretraining block prints the paper's five numbers', ...);

  // ---- the end of the page
  await p.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await wait(600);
  const end = await p.evaluate(() => ({ p: +getComputedStyle(document.getElementById('bar')).getPropertyValue('--p'), footerInMain: !!document.querySelector('main footer, main .foot') }));
  check('the bar shows progress at the end of the page, and the footer is outside the main part', end.p > 0.98 && !end.footerInMain, JSON.stringify(end));

  console.log(logs.length ? 'CONSOLE:\n' + logs.join('\n') : 'console clean');
  if (logs.length) fails++;
  console.log(fails ? `${fails} FAILED` : 'all passed');
  await browser.close();
  process.exit(fails ? 1 : 0);
})();

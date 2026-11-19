// node audit.js [width ...]   layout audit of the page at each viewport width (default 320 390 768 1024 1440)
//
//   overflow   elements that reach past the right edge of the page
//   orphans    blocks of text whose last line holds one short word, or is far shorter than the block
//   wraps      labels that must stay on one line and broke
//   split      a number that ended a line while its unit started the next ("45 / µm")
//   lone       a grid whose last row holds a single item
//   groups     a name and its superscript (GROUPS, default '.authors .au, [data-group]') split across two lines
//
// OPEN=1 opens every <details> first, so what sits in closed rows is audited too. Run it both ways.
// ONELINE and TEXT override the selectors below. See _browser.js for URL, READY, SETTLE, PW_FILE.
const { launch, open, walk, wait, usage } = require('./_browser.js');
usage(__filename);
const widths = process.argv.slice(2).map(Number).filter(Boolean);
const ONELINE = process.env.ONELINE || '.top-nav a, .top-cta, .tag, .stats dt, .soon-list b, .soon-list em, .chips button, .ch-toggle button, [data-oneline]';
const TEXT = process.env.TEXT || 'main p, main li, main dd, main figcaption, main h2, main h3, .mast p, .mast h1, summary, footer p';
const GROUPS = process.env.GROUPS || '.authors .au, [data-group]';

(async () => {
  const browser = await launch();
  let bad = 0;
  for (const W of widths.length ? widths : [320, 390, 768, 1024, 1440]) {
    const { page, logs } = await open(browser, W);
    if (process.env.OPEN) await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true; }));
    await walk(page);
    await wait(900);
    const r = await page.evaluate((ONELINE, TEXT, GROUPS) => {
      const vw = document.documentElement.clientWidth;
      const name = (e) => `${e.tagName.toLowerCase()}${e.id ? '#' + e.id : ''}${e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).join('.') : ''}`;
      const clipped = (e) => { for (let a = e.parentElement; a; a = a.parentElement) { const o = getComputedStyle(a).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') return true; } return false; };
      const shown = (e) => e.offsetParent && !e.closest('[hidden]') && !(e.closest('details:not([open])') && e.tagName !== 'SUMMARY');
      const linesOf = (node) => {
        const range = document.createRange();
        range.selectNodeContents(node);
        const lines = [];
        for (const q of [...range.getClientRects()].filter((x) => x.width > 1)) {
          // rects on one line overlap vertically by more than half of the smaller one
          const l = lines.find((x) => Math.min(x.bottom, q.bottom) - Math.max(x.top, q.top) > 0.5 * Math.min(x.bottom - x.top, q.height));
          if (l) { l.left = Math.min(l.left, q.left); l.right = Math.max(l.right, q.right); l.top = Math.min(l.top, q.top); l.bottom = Math.max(l.bottom, q.bottom); } else lines.push({ top: q.top, bottom: q.bottom, left: q.left, right: q.right });
        }
        return lines.sort((a, b) => a.top - b.top);
      };
      const over = [];
      for (const e of document.querySelectorAll('body *')) {
        const q = e.getBoundingClientRect();
        // what sits in a closed <details> keeps its layout in current browsers but is not drawn: it is audited with OPEN=1
        if (q.width && q.right > vw + 1 && !clipped(e) && !e.closest('details:not([open]) > :not(summary)') && getComputedStyle(e).position !== 'fixed') over.push(`${name(e)} right=${Math.round(q.right)}`);
      }
      const orphans = [], split = [];
      for (const e of document.querySelectorAll(TEXT)) {
        if (!shown(e) || e.querySelector('p, li, dd, details, figure, canvas, table')) continue;
        const lines = linesOf(e);
        if (lines.length > 1) {
          const widest = Math.max(...lines.map((l) => l.right - l.left)), last = lines[lines.length - 1].right - lines[lines.length - 1].left;
          const tail = e.textContent.trim().replace(/\s+/g, ' ').split(' ').slice(-3).join(' ');
          if (last < 0.14 * widest || last < 46) orphans.push(`${name(e)} lines=${lines.length} last=${Math.round(last)}/${Math.round(widest)} "…${tail}"`);
        }
        // a number and its unit on different lines (an ordinary space between them; a no-break space keeps them together)
        const walker = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
        for (let n = walker.nextNode(); n; n = walker.nextNode()) {
          for (const m of n.textContent.matchAll(/(\d[\d.,]*) (µm|mm|cm|nm|km|ms|GB|MB|kB|px|[MBk]\b|%)/g)) {
            const a = document.createRange(), b = document.createRange();
            a.setStart(n, m.index); a.setEnd(n, m.index + m[1].length);
            b.setStart(n, m.index + m[1].length + 1); b.setEnd(n, m.index + m[0].length);
            const ra = a.getClientRects()[0], rb = b.getClientRects()[0];
            if (ra && rb && Math.abs(ra.top - rb.top) > 4) split.push(`${name(e)} "${m[0]}"`);
          }
        }
      }
      const wraps = [];
      for (const e of document.querySelectorAll(ONELINE)) {
        if (!shown(e)) continue;
        const node = [...e.childNodes].find((n) => n.nodeType === 3 && n.textContent.trim());       // its own words, not what it carries
        if (node && linesOf(node).length > 1) wraps.push(`${name(e)} "${node.textContent.trim().slice(0, 40)}"`);
      }
      const lone = [];
      for (const g of document.querySelectorAll('*')) {
        if (getComputedStyle(g).display !== 'grid' || g.children.length < 4 || !shown(g)) continue;
        const kids = [...g.children].filter((k) => k.offsetParent), tops = kids.map((k) => Math.round(k.getBoundingClientRect().top));
        const rows = [...new Set(tops)];
        if (rows.length > 1 && tops.filter((t) => t === rows[rows.length - 1]).length === 1 && tops.filter((t) => t === rows[0]).length > 2) lone.push(`${name(g)}: ${kids.length} items, the last row holds one`);
      }
      // an author's name and its marks break only as one group ("affiliations go to the second line for one name")
      const groups = [];
      for (const e of document.querySelectorAll(GROUPS)) {
        if (!shown(e)) continue;
        const tops = [...e.getClientRects()].filter((q) => q.width > 0.5).map((q) => Math.round(q.bottom));
        if (new Set(tops).size > 1 && Math.max(...tops) - Math.min(...tops) > 6) groups.push(`${name(e)} "${e.textContent.trim().slice(0, 40)}"`);
      }
      return { pageW: document.documentElement.scrollWidth, over: over.slice(0, 12), orphans, split, wraps, lone, groups };
    }, ONELINE, TEXT, GROUPS);
    const show = (k, v) => `${k}: ${v.length ? '\n  ' + v.join('\n  ') : 'none'}`;
    console.log(`\n===== ${W}px: page ${r.pageW} wide\n${show('overflow', r.over)}\n${show('orphans', r.orphans)}\n${show('wraps', r.wraps)}\n${show('split', r.split)}\n${show('lone', r.lone)}\n${show('groups', r.groups)}${logs.length ? '\nconsole:\n  ' + logs.join('\n  ') : ''}`);
    bad += r.over.length + r.orphans.length + r.wraps.length + r.split.length + r.lone.length + r.groups.length + logs.length;
    await page.close();
  }
  await browser.close();
  console.log(bad ? `\n${bad} finding(s)` : '\nclean');
  process.exit(bad ? 1 : 0);
})();

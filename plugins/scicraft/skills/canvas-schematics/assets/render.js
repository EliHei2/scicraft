#!/usr/bin/env node
/* Headless-browser renderer for one canvas schematic: a PNG at full device resolution
 * (canvas.toDataURL) and a PDF whose page is exactly (W/10) x (H/10) mm, because the
 * canvas is laid out at 10 logical px per mm.
 *
 * Needs Node 18 or later and puppeteer, installed next to this file:
 *     npm install            (reads package.json in the same folder)
 *
 * Usage:
 *     node render.js <html> <out-basename> <W> <H> [out-dir] [--check] [--timeout MS]
 *     node render.js figure.html figure 1830 1040 ../figures --check
 *     node render.js "preview.html?region=b" prev_b 428 948 regions/out
 *
 * <html> and [out-dir] are resolved against this file's folder unless absolute.
 * W and H are logical px (for a preview: region w + 48, h + 48).
 * --check  print every text drawn under 5 pt (18 px) and every pair of overlapping
 *          text boxes, recorded by LIB.text; exit 2 if any is found.
 * Exit codes: 0 rendered (and clean), 1 render failed, 2 check found problems.
 */
const path = require('path');
const fs = require('fs');

function usage(code) {
  const head = fs.readFileSync(__filename, 'utf8').split('*/')[0];
  console.log(head.replace(/^#!.*\n/, '').replace(/^\/\* ?|^ \* ?/gm, ''));
  process.exit(code);
}

const argv = process.argv.slice(2);
if (argv.includes('--help') || argv.includes('-h') || argv.length < 4) usage(argv.length < 4 && !argv.includes('--help') && !argv.includes('-h') ? 1 : 0);
const CHECK = argv.includes('--check');
let TIMEOUT = 300000;
const ti = argv.indexOf('--timeout');
if (ti >= 0) { TIMEOUT = parseInt(argv[ti + 1], 10); argv.splice(ti, 2); }
const pos = argv.filter(a => !a.startsWith('--'));
const [htmlArg, out, wArg, hArg, outDirArg] = pos;
const W = parseInt(wArg, 10), H = parseInt(hArg, 10);
if (!(W > 0 && H > 0)) { console.error('W and H must be positive integers (logical px)'); process.exit(1); }

let puppeteer;
try { puppeteer = require('puppeteer'); }
catch (e) { console.error('puppeteer not found. Run `npm install` in ' + __dirname + ' (package.json is there).'); process.exit(1); }

const HERE = __dirname;
const [htmlFile, query] = htmlArg.split('?');
const htmlPath = path.isAbsolute(htmlFile) ? htmlFile : path.resolve(HERE, htmlFile);
if (!fs.existsSync(htmlPath)) { console.error('no such page: ' + htmlPath); process.exit(1); }
const OUT_DIR = outDirArg ? (path.isAbsolute(outDirArg) ? outDirArg : path.resolve(HERE, outDirArg)) : path.resolve(HERE, 'out');
fs.mkdirSync(OUT_DIR, { recursive: true });

(async () => {
  const browser = await puppeteer.launch({ headless: true, protocolTimeout: TIMEOUT });
  const page = await browser.newPage();
  const problems = [];
  page.on('pageerror', err => { problems.push('PAGEERROR ' + err.message); console.log('PAGEERROR:', err.message); });
  page.on('console', msg => { if (msg.type() === 'error') { problems.push('CONSOLE ' + msg.text()); console.log('CONSOLE:', msg.text()); } });
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  const url = 'file://' + htmlPath + (query ? '?' + query : '');
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 60000 });
  await page.waitForFunction("document.getElementById('done-flag') && document.getElementById('done-flag').style.display === 'block'", { timeout: 60000 });
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 800));

  const fontOk = await page.evaluate(() => document.fonts.check('400 18px "Helvetica Neue"'));
  if (!fontOk) console.log('WARNING: Helvetica Neue is not installed here; text was set in a fallback face and will measure differently.');

  const dataUrl = await page.evaluate(() => document.getElementById('c').toDataURL('image/png'));
  const png = path.join(OUT_DIR, `${out}.png`);
  fs.writeFileSync(png, Buffer.from(dataUrl.split(',')[1], 'base64'));
  const dims = await page.evaluate(() => { const c = document.getElementById('c'); return [c.width, c.height]; });

  let report = null;
  if (CHECK) report = await page.evaluate(() => (window.LIB && LIB.checkText) ? LIB.checkText() : null);
  const regionErrors = await page.evaluate(() => window.__RENDER_ERRORS || []);

  await page.evaluate((du) => {
    const img = document.createElement('img');
    img.src = du; img.style.width = '100%'; img.style.height = '100%'; img.style.display = 'block';
    document.body.innerHTML = ''; document.body.style.margin = '0'; document.body.appendChild(img);
  }, dataUrl);
  await page.evaluate(() => new Promise(r => { const i = document.querySelector('img'); if (i.complete) r(); else i.onload = r; }));
  const pdf = path.join(OUT_DIR, `${out}.pdf`);
  await page.pdf({ path: pdf, width: `${(W / 10).toFixed(2)}mm`, height: `${(H / 10).toFixed(2)}mm`,
    printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 }, pageRanges: '1' });

  console.log(`wrote ${png}  (${dims[0]} x ${dims[1]} px)`);
  console.log(`wrote ${pdf}  (${(W / 10).toFixed(1)} x ${(H / 10).toFixed(1)} mm)`);
  let bad = problems.length + regionErrors.length;
  regionErrors.forEach(e => console.log('REGION ERROR:', e));
  if (CHECK) {
    if (!report) { console.log('CHECK: no text records (core_lib.js not loaded?)'); bad++; }
    else {
      console.log(`CHECK: ${report.n} text items; ${report.small.length} under 18 px; ${report.overlaps.length} overlapping pairs`);
      report.small.forEach(s => console.log(`  SMALL ${s.px} px: "${s.str}"`));
      report.overlaps.forEach(o => console.log(`  OVERLAP at ${o.at[0]},${o.at[1]}: "${o.a}" x "${o.b}"`));
      bad += report.small.length + report.overlaps.length;
    }
  }
  await Promise.race([browser.close().catch(() => {}), new Promise(r => setTimeout(r, 500))]);
  process.exit(CHECK && bad ? 2 : (problems.length || regionErrors.length ? 1 : 0));
})().catch(e => { console.error(e); process.exit(1); });

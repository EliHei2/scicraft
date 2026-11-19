// Shared by audit.js, shot.js and behave.template.js: finds puppeteer-core and Chrome, opens the page at a viewport,
// signs in at a password gate when one is there, and waits until the page says it is ready.
//
// Environment:
//   URL        the page (default http://127.0.0.1:8765/)
//   READY      a JS expression that is truthy once the page can be checked (default: the document has loaded).
//              A page with a WebGL viewer usually needs its own, e.g. READY='window.viewer && window.viewer.ready'
//   SETTLE     a JS statement run once after READY, e.g. to stop an autoplay: SETTLE='window.viewer.stop()'
//   PW_FILE    a file holding the password of a gated build; it is typed into PW_SEL (default #pw) and never printed
//   PUPPETEER  path of the puppeteer-core module, if it is not installed under the working directory or ./pipeline
//   CHROME     path of the Chrome binary, if it is not in a usual place
const fs = require('fs');
const path = require('path');

function findPuppeteer() {
  if (process.env.PUPPETEER) return require(process.env.PUPPETEER);
  const roots = [process.cwd(), path.join(process.cwd(), 'pipeline'), __dirname];
  try { return require(require.resolve('puppeteer-core', { paths: roots })); } catch (e) {
    throw new Error('puppeteer-core not found. Install it once in the site folder: (cd pipeline && npm i puppeteer-core), or set PUPPETEER=/path/to/node_modules/puppeteer-core');
  }
}
function findChrome() {
  const places = [process.env.CHROME, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'];
  const hit = places.find((p) => p && fs.existsSync(p));
  if (!hit) throw new Error('Chrome not found; set CHROME=/path/to/chrome');
  return hit;
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const URL_ = process.env.URL || 'http://127.0.0.1:8765/';

// The GPU flags let WebGL run headless on a Mac (Metal). They are harmless where there is no WebGL.
async function launch() {
  return findPuppeteer().launch({ executablePath: findChrome(), headless: 'new',
    args: ['--no-sandbox', '--enable-gpu', '--use-gl=angle', '--use-angle=metal', '--ignore-gpu-blocklist', '--hide-scrollbars'] });
}

// Opens one page. `logs` collects console problems, page errors and failed requests as they happen.
async function open(browser, width, height, { dpr } = {}) {
  const page = await browser.newPage();
  const logs = [];
  page.on('console', (m) => { if (!['log', 'debug', 'info', 'verbose'].includes(m.type())) logs.push(`${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => logs.push(`pageerror: ${e.message}`));
  page.on('response', (r) => { if (r.status() >= 400 && !r.url().includes('favicon')) logs.push(`http ${r.status()} ${r.url()}`); });
  const mobile = width < 600;
  await page.setViewport({ width, height: height || (mobile ? 844 : 900), deviceScaleFactor: dpr || 1, isMobile: mobile, hasTouch: mobile });
  await page.goto(URL_, { waitUntil: 'load' });
  const sel = process.env.PW_SEL || '#pw';
  if (process.env.PW_FILE && await page.$(sel)) {
    await page.type(sel, fs.readFileSync(process.env.PW_FILE, 'utf8').trim());
    await page.keyboard.press('Enter');
  }
  await page.waitForFunction(process.env.READY || 'document.readyState === "complete"', { timeout: 60000 });
  if (process.env.SETTLE) await page.evaluate(process.env.SETTLE);
  return { page, logs, mobile };
}

// Walks down the page so that everything that appears on scroll has appeared.
async function walk(page, step = 500, pause = 140) {
  for (let y = 0; ; y += step) {
    const max = await page.evaluate(() => document.documentElement.scrollHeight - innerHeight);
    await page.evaluate((yy) => window.scrollTo(0, yy), Math.min(y, max));
    await wait(pause);
    if (y >= max) break;
  }
}

// `node <script> --help` prints the comment block at the top of the script and exits.
function usage(file) {
  if (!process.argv.includes('--help') && !process.argv.includes('-h')) return;
  const head = [];
  for (const l of fs.readFileSync(file, 'utf8').split('\n')) { if (!l.startsWith('//')) break; head.push(l.replace(/^\/\/ ?/, '')); }
  console.log(head.join('\n'));
  process.exit(0);
}

module.exports = { launch, open, walk, wait, usage, URL: URL_ };

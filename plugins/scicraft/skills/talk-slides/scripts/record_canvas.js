#!/usr/bin/env node
// Record a canvas figure of a web page frame by frame, exactly on its own timeline: no screen capture and no
// real-time playback. For each frame the page runs your code that sets the figure to time t, then the canvas is
// saved as OUT_DIR/NNNNN.png (transparent where the canvas is). A run resumes after the last frame already written,
// because a headless recording under machine load times out ("Runtime.callFunctionOn timed out").
//
//   node record_canvas.js URL OUT_DIR --set-time "<JS using t and canvas>" [--selector canvas] [--fps 30]
//        [--seconds N] [--width 1440] [--height 1000] [--scale 1.78] [--wait-for "<JS expression>"]
//        [--before "<JS run once>"] [--chrome PATH] [--timeout-ms 60000]
//   node record_canvas.js --help
//
// URL is a served local copy of the site (python3 -m http.server 8765 --bind 127.0.0.1 in the copy's folder).
// Patch the copy, never the site (references/motion.md section 5). --set-time is the body of a function of t
// (seconds) and canvas (the element --selector finds); it may return a promise. Example for a figure object that
// exposes its own clock:
//     --set-time "const st = canvas.closest('figure').stage; st.t = t; st.render(1/30);"
// --wait-for is polled until true before recording (for example "window.figureReady === true"). --before runs
// once after that (scroll the figure into view, stop its own animation loop). --seconds is required; frames are
// 0 .. round(seconds x fps), so the last frame is the finished drawing.
//
// Then composite the frames on the deck's ground, crop, and encode with the recipe of references/motion.md
// section 4. Record one figure at a time; the local test server is often single-threaded.
//
// Needs Node 18 or later and puppeteer-core (npm install puppeteer-core, or NODE_PATH pointing at a node_modules
// that has it) plus a Chrome or Chromium binary: --chrome PATH, else $CHROME, else the usual install locations.
// Exit status 1 on a missing canvas, a page error during recording, or no browser.
'use strict';
const fs = require('fs');
const path = require('path');

function usage(code) {
  const src = fs.readFileSync(__filename, 'utf8').split('\n');
  const doc = src.filter((l, i) => i > 0 && l.startsWith('//')).map((l) => l.replace(/^\/\/ ?/, ''));
  console.log(doc.join('\n'));
  process.exit(code);
}

function parse(argv) {
  const a = { selector: 'canvas', fps: 30, width: 1440, height: 1000, scale: 1920 / 1080, timeoutMs: 60000, pos: [] };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    const v = () => { if (i + 1 >= argv.length) { console.error(`${k} needs a value`); process.exit(2); } return argv[++i]; };
    if (k === '-h' || k === '--help') usage(0);
    else if (k === '--selector') a.selector = v();
    else if (k === '--set-time') a.setTime = v();
    else if (k === '--fps') a.fps = Number(v());
    else if (k === '--seconds') a.seconds = Number(v());
    else if (k === '--width') a.width = Number(v());
    else if (k === '--height') a.height = Number(v());
    else if (k === '--scale') a.scale = Number(v());
    else if (k === '--wait-for') a.waitFor = v();
    else if (k === '--before') a.before = v();
    else if (k === '--chrome') a.chrome = v();
    else if (k === '--timeout-ms') a.timeoutMs = Number(v());
    else if (k.startsWith('--')) { console.error(`unknown option ${k}`); process.exit(2); }
    else a.pos.push(k);
  }
  if (a.pos.length !== 2 || !a.setTime || !(a.seconds > 0)) {
    console.error('usage: node record_canvas.js URL OUT_DIR --set-time "<JS>" --seconds N   (--help for more)');
    process.exit(2);
  }
  [a.url, a.out] = a.pos;
  return a;
}

function findChrome(given) {
  const cands = [given, process.env.CHROME,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    'C:/Program Files/Google/Chrome/Application/chrome.exe'].filter(Boolean);
  return cands.find((p) => fs.existsSync(p));
}

(async () => {
  const a = parse(process.argv.slice(2));
  let puppeteer;
  try { puppeteer = require('puppeteer-core'); } catch (e) {
    console.error('puppeteer-core not found: npm install puppeteer-core, or set NODE_PATH to a node_modules that has it');
    process.exit(1);
  }
  const chrome = findChrome(a.chrome);
  if (!chrome) { console.error('no Chrome or Chromium found: pass --chrome PATH or set CHROME'); process.exit(1); }
  fs.mkdirSync(a.out, { recursive: true });
  const n = Math.round(a.seconds * a.fps);
  const done = fs.readdirSync(a.out).filter((f) => /^\d{5}\.png$/.test(f)).map((f) => parseInt(f, 10));
  let start = 0;
  while (done.includes(start)) start++;                     // first missing frame; a resumed run fills from there
  if (start > n) { console.log(`all ${n + 1} frames already in ${a.out}`); return; }
  if (start > 0) console.log(`resuming at frame ${start} of ${n}`);

  const browser = await puppeteer.launch({ executablePath: chrome, headless: 'new',
    args: ['--hide-scrollbars', '--mute-audio', '--ignore-gpu-blocklist'] });
  let failed = null;
  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(a.timeoutMs);
    page.on('pageerror', (e) => { failed = failed || e.message; console.error('pageerror', e.message); });
    await page.setViewport({ width: a.width, height: a.height, deviceScaleFactor: a.scale });
    await page.goto(a.url, { waitUntil: 'load', timeout: a.timeoutMs });
    if (a.waitFor) await page.waitForFunction(a.waitFor, { timeout: a.timeoutMs });
    if (a.before) await page.evaluate((code) => (new Function(code))(), a.before);
    const size = await page.evaluate((sel) => {
      const c = document.querySelector(sel);
      return c && c.getContext ? [c.width, c.height] : null;
    }, a.selector);
    if (!size) throw new Error(`no canvas matches ${a.selector}`);
    console.log(`canvas ${size[0]} x ${size[1]} px; check this against the size the slide needs (a canvas may cap its pixel ratio)`);
    for (let i = start; i <= n; i++) {
      const b64 = await page.evaluate(async (sel, code, t) => {
        const canvas = document.querySelector(sel);
        await (new Function('t', 'canvas', code))(t, canvas);
        return canvas.toDataURL('image/png').slice(22);
      }, a.selector, a.setTime, i / a.fps);
      const tmp = path.join(a.out, '.partial.png');           // write, then rename: a killed run leaves no half frame
      fs.writeFileSync(tmp, Buffer.from(b64, 'base64'));
      fs.renameSync(tmp, path.join(a.out, String(i).padStart(5, '0') + '.png'));
      if (failed) throw new Error(`page error at frame ${i}: ${failed}`);
    }
    console.log(`${a.out}: frames ${start} to ${n} written (${n + 1} in all, ${a.fps} fps, ${a.seconds} s)`);
  } catch (e) {
    console.error(String(e.message || e));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();

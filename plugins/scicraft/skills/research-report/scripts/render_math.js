#!/usr/bin/env node
// Render a list of TeX snippets to standalone SVG strings with MathJax 3 (no browser, no CDN).
//
// Usage: node render_math.js IN.json OUT.json
//   IN.json  : [{"tex": "a^2+b^2", "display": true}, ...]
//   OUT.json : ["<svg ...>...</svg>", ...]   (same order and length)
//
// Needs the npm package mathjax-full@3.2.2, found through NODE_PATH, e.g.
//   npm install --prefix ~/.cache/report-mathjax mathjax-full@3.2.2
//   NODE_PATH=~/.cache/report-mathjax/node_modules node render_math.js in.json out.json
// build_report.py sets NODE_PATH itself from --mathjax-dir.
// Exit code 2 if a snippet fails to parse; the failing snippets are printed.

const fs = require('fs');

if (process.argv.length < 4 || process.argv.includes('--help')) {
  console.log('usage: node render_math.js IN.json OUT.json  (needs mathjax-full@3.2.2 on NODE_PATH)');
  process.exit(process.argv.includes('--help') ? 0 : 1);
}

let mj;
try {
  mj = {
    mathjax: require('mathjax-full/js/mathjax.js').mathjax,
    TeX: require('mathjax-full/js/input/tex.js').TeX,
    SVG: require('mathjax-full/js/output/svg.js').SVG,
    liteAdaptor: require('mathjax-full/js/adaptors/liteAdaptor.js').liteAdaptor,
    RegisterHTMLHandler: require('mathjax-full/js/handlers/html.js').RegisterHTMLHandler,
    AllPackages: require('mathjax-full/js/input/tex/AllPackages.js').AllPackages,
  };
} catch (e) {
  console.error('mathjax-full not found on NODE_PATH: ' + e.message);
  process.exit(3);
}

const adaptor = mj.liteAdaptor();
mj.RegisterHTMLHandler(adaptor);
// fontCache "none": every SVG carries its own glyph paths, so each one can be pasted anywhere on its own.
const doc = mj.mathjax.document('', {
  InputJax: new mj.TeX({ packages: mj.AllPackages.filter((p) => p !== 'bussproofs') }),
  OutputJax: new mj.SVG({ fontCache: 'none' }),
});

const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = [];
const bad = [];
items.forEach((it, i) => {
  const node = doc.convert(it.tex, { display: !!it.display });
  const svg = adaptor.innerHTML(node);
  if (/data-mjx-error|merror/.test(svg)) bad.push(`#${i}: ${it.tex}`);
  out.push(svg);
});
fs.writeFileSync(process.argv[3], JSON.stringify(out));
if (bad.length) {
  console.error('TeX errors in ' + bad.length + ' snippet(s):\n  ' + bad.join('\n  '));
  process.exit(2);
}
console.log(`rendered ${out.length} snippet(s)`);

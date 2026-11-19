// node render.js -> fig2.png, fig2.pdf
const puppeteer = require('/opt/legacy-figs/node_modules/puppeteer');
const path = require('path');
(async () => {
  const b = await puppeteer.launch({ headless: 'new' }); const p = await b.newPage();
  await p.setViewport({ width: 1830, height: 1000, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(__dirname, 'figure.html'));
  await p.waitForFunction("document.getElementById('done-flag').style.display === 'block'");
  const du = await p.evaluate(() => document.getElementById('c').toDataURL('image/png'));
  require('fs').writeFileSync(path.resolve(__dirname, 'fig2.png'), Buffer.from(du.split(',')[1], 'base64'));
  await p.pdf({ path: path.resolve(__dirname, 'fig2.pdf'), width: '1830px', height: '1000px' });
  await b.close();
})();

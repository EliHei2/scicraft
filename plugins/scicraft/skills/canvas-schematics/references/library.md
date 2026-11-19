# The core library, the packs and the region contract

## Contents

1. Project layout
2. The region contract
3. Core library (`core_lib.js`)
4. Loading packs
5. Previews and the master render

## 1. Project layout

Copy from the skill's `assets/` into a `code/` folder beside the paper's figures:

```
figN/
├── code/
│   ├── core_lib.js        assets/core_lib.js
│   ├── pack_arch.js       assets/pack_arch.js      (architecture figures)
│   ├── pack_bio.js        assets/pack_bio.js       (cells, tissue)
│   ├── layout.js          assets/layout_template.js
│   ├── scene.js           assets/scene_template.js (only for a shared biological scene)
│   ├── main.js            assets/main_template.js
│   ├── figure.html        assets/figure_template.html
│   ├── preview.html       assets/preview_template.html
│   ├── render.js          assets/render.js
│   ├── package.json       assets/package.json      then: npm install
│   ├── regions/region_<id>.js
│   ├── data/panel_<id>.js window.PANEL_<ID> = {...}, written by _prep/
│   └── _prep/             scripts that turn real data or real code output into data/*.js
├── ref_crops/orig_<id>.png  per-region targets cut from a reference
├── SPEC.md                  assets/spec_template.md, filled in
├── PROVENANCE.md            one row per data file
└── figN.pdf, figN.png       the deliverable
```

`npm install` reads `package.json` and installs puppeteer with its own Chrome (about 150 MB once).
On a machine that already has Chrome for Testing, `PUPPETEER_SKIP_DOWNLOAD=1 npm install` and set
`PUPPETEER_EXECUTABLE_PATH` to that binary.

## 2. The region contract

One coherent canvas, split into region functions over one shared library. The library is the
single style lever: "if it can't be slidy, the agents can't be slidy."

```js
function drawRegion_b(ctx, W, H, R) { ... }   // R is the LAYOUT.REGIONS entry
```

- `ctx` arrives translated to the region's origin; draw in local `[0,0]..[W,H]`.
- Use only `PAL`, `FONT`, `LIB`, `SCENE` and data globals (`PANEL_B`). No hex, no rgb(), no font
  string, no literal font size.
- Never call `setTransform`, resize the canvas or touch `#done-flag`.
- Never draw the panel letter or title; `main.js` draws them in the band above the rect.
- Stay inside `[0,0]..[W,H]`. The preview harness draws the rect as a faint dashed frame so bleed shows.
- Read the existing region code before changing it. Never guess at coordinates.

`main.js` sizes the canvas to `W x S` by `H x S`, applies `setTransform(S, 0, 0, S, 0, 0)`, draws each
region inside `try`, records region errors in `window.__RENDER_ERRORS`, draws letters, titles and
spine arrows (`STRUCT.flow`), then shows `#done-flag`.

## 3. Core library (`core_lib.js`)

| Group | Names | Notes |
|---|---|---|
| tokens | `PAL.ink inkSoft line flow leader guide rule paper halo greyPt ok err highSim lowSim`, `PAL.rank5`, `PAL.delta`, `PAL.deltaPrinted` | all text in `PAL.ink`, never `inkSoft`; `highSim` `#FF9500` and `lowSim` `#5AC8FA` for warm and cold edges; `ok` solid and `err` dashed for positive and negative edges |
| type | `FONT.LETTER L1 L2 L3 FLOOR family mono` and weights | 29, 25, 21, 18 px (letter 8.2 pt); mono for code tokens only |
| units | `LIB.mm(v)`, `LIB.pt(v)` | logical px from mm or pt |
| randomness | `LIB.rng(seed)` | linear congruential, deterministic; one seed per scene, shared by every panel |
| ramps | `LIB.ramp(stops, t)`, `LIB.rank` (continuous), `LIB.rank5` (five steps), `LIB.delta`, `LIB.deltaPrinted`, `LIB.lerp`, `LIB.alpha` | `ramp` takes even stops or `[pos, hex]` pairs |
| text | `LIB.text(ctx, str, x, y, {size, weight, align, baseline, color, italic, mono, maxWidth})`, `LIB.measure`, `LIB.math(ctx, x, y, segs, size, align)` | every call records its box for `render.js --check`; `math` segs are `{t, sub, italic}` |
| lines | `LIB.line`, `LIB.arrow(ctx, x1, y1, x2, y2, {color, lw, head, dash})`, `LIB.elbow(..., 'hv' or 'vh', opt)` | one filled head shape everywhere |
| containers | `LIB.frame` (flat, no shadow option), `LIB.roundRectPath`, `LIB.clipRect`, `LIB.badge` | |
| tables | `LIB.colorBar` (table-as-bars idiom), `LIB.heatmap(ctx, x, y, cw, ch, rows, cols, v(r,c), {cmap, gap, stroke, printed})`, `LIB.strip` | `printed(r,c)` writes values in cells, ink chosen by luminance |
| points | `LIB.points(ctx, pts, {r, c, halo})` | radius 3.0 by default, white halo 1.3 px |
| legend | `LIB.legend(ctx, x, y, items, {horizontal})` | shapes `dot square block line dash ring` |
| audit | `LIB.checkText(tol)` | text under the floor and overlapping text boxes |

Color rules carried by the tokens:

- **Two color systems never touch.** Compared categories are saturated; metadata is pastel; inside a
  matrix the ramp is neutral and the text black.
- **The same sequential ramp as the data figures**: `#F1F6FF #C7DCFF #8FB9FF #4D97FF #003FBD`.
- **Signed matrices**: `PAL.delta` (`#2166AC #F7F7F7 #D55E00`) when no values are printed. When values
  are printed, use `PAL.deltaPrinted`, blue to red with a white plateau between 0.43 and 0.57, because
  blue to orange is close to iso-luminant and reads flat. Emphasis by color is allowed only when the
  values are printed in the cells.

## 4. Loading packs

`figure.html` loads `core_lib.js`, then each pack, then `layout.js`, `scene.js`, data files, region
files and `main.js`, in that order. `LAYOUT.PACKS` (for example `['arch']` or `['bio', 'arch']`) tells
the preview harness which packs to load. Both packs can be loaded together; their names do not clash.

## 5. Previews and the master render

```bash
cd figN/code
node render.js "preview.html?region=b" prev_b <w+48> <h+48> regions/out --check
node render.js "preview.html?region=c&data=panel_c&scene=1" prev_c <w+48> <h+48> regions/out --check
node render.js figure.html figN 1830 <H> .. --check
```

`render.js` waits for `#done-flag`, then for `document.fonts.ready` and 800 ms more, writes the PNG
from `canvas.toDataURL` (W x S by H x S px) and a one-page PDF of W/10 by H/10 mm, prints page errors
and console errors, and warns when Helvetica Neue is missing (the fallback face measures differently,
so labels that fit on one machine can clip on another). With `--check` it lists text under 18 px and
overlapping text boxes and exits 2. It does not see text covered by a shape drawn later; that needs
eyes. Name preview files by version (`prev_b_v3`) so a cached image never passes for a new one.

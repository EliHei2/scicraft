# Patterns: design tokens and code

Everything in sections 1 to 10 is in the starter (`assets/starter/public/`). Read this when you change it or need to
know why a piece is written the way it is. Section 11 is for large point layers and outlines (`scripts/pack_points.py`,
`scripts/build_masks.py`), 12 for figures that must stay images, 13 for TeX labels and 14 for method figures on
`assets/fx/`.

## Contents
1. Tokens and the section grammar
2. Text that never breaks badly
3. Rows that open
4. Charts, and the weight of a win
5. Definitions under the pointer
6. The divider and the gallery dialog
7. The mark that shrinks into the bar
8. Things that rise once
9. Phones
10. The builder: checked numbers and guards
11. Large data
12. A paper figure that must stay an image
13. TeX labels in canvas figures
14. Method figures on the fx engine

## 1. Tokens and the section grammar

```css
:root {
  --bg: #141416;  --ink: #f4f4f5;  --body: #d2d2d7;  --quiet: #8b8b93;  --rule: #2e2e34;  --link: #8cbcf3;
  --ours: #8ec9ff;      /* the paper's method: the one accent */
  --rival: #e69f00;     /* the strongest comparator, where one is named */
  --sans: 'Helvetica Neue', Helvetica, Inter, Arial, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
  --col: 1080px;  --gutter: 24px;  --bar: 60px;  --ease: cubic-bezier(.2, .7, .2, 1);
}
```

| Element | Setting in the starter |
|---|---|
| body text | weight 300, 18 px on 1.62 (16 px on phones); bold is 500 |
| name (`.mast h1`) | weight 500, `clamp(54px, min(7.2vw, 13vh), 104px)`, line 0.9, tracking -0.045em, white |
| subtitle | weight 300, 18 to 24 px, line 1.28 |
| section head (`h2`) | weight 500, 28 to 42 px, line 1.08, tracking -0.028em |
| opening statements, main claim | weight 300, 22 to 34 px, line 1.3; statements `#86868e`, the main claim in ink |
| claim (row line) | weight 500, 22 px, line 1.3 |
| big numbers | weight 300, 34 to 60 px, tracking -0.035em; the winning one 700 in the accent |
| captions, chart text | 13.5 px quiet; chart text 12.5 px, ticks 11.5 px, tabular figures |
| mono meta line | weight 400, 12 px |
| column, gutter | 1080 px, 24 px (16 px on phones) |
| bar | 60 px (50 px on phones), blurred ground after the first scroll, 1 px progress line in the accent |
| section rhythm | 136 px above a section (88 px on phones), hairline, 26 px, the head |
| radius, shadow | radius 999 px only on the call-to-action and "again" pills; shadows only on tooltip and dialog |
| chart colors | others `#5c5c64`, axis `#3a3a42` |

- The ground is the ground of the output renders. If the paper's pictures sit on white, flip the tokens; do not put
  dark pictures on a white page or the reverse.
- Three text colors only: `--ink` for names and claims, `--body` for sentences, `--quiet` for captions and labels.
  Text never wears a series color except the name of the paper's method next to its mark.
- **Every overlay contrasts with the ground it lands on.** On a dark page, outlines and structural marks are white
  ("black on black is not visible"); schematic boxes and spheres sit on a light plate with dark ink ("make the box
  ... background white"); real data stays on the dark ground.
- A section is `<section id>` with `.head` (hairline, `h2`, and `.meta`: one mono line holding a single fact) and,
  optionally, one `.lead` sentence. Weight comes from size and space; there are no boxes.
- Fonts are self-hosted woff2 (Inter and IBM Plex Mono, under the SIL Open Font License; the license texts ship
  beside them in `fonts/`). No font request leaves the page, which matters for a private preview. Helvetica Neue is
  commercial and is never shipped; it is used where the visitor has it.

## 2. Text that never breaks badly

```css
p, li, dd, dt, figcaption, h1, h2, h3, h4, summary { text-wrap: balance; }
.authors .au { white-space: nowrap; }
```

Browsers balance blocks of up to about six lines. For longer paragraphs bind the last two or three words with
`&nbsp;`. Bind every number to its unit (`45&nbsp;µm`, `12.5&nbsp;M`), also in text set by scripts (` `).
Wrap each author's name with its superscript in `<span class="au">`, so a name and its marks break as one group.
`audit.js` reports all three faults ("orphans", "split", "groups") at every width it is given.

## 3. Rows that open

Native `<details class="fold">`: keyboard, find-in-page and screen readers work without code. `page.js` adds three
things:

```js
function unfold(t) { for (let d = t.closest('details'); d; d = d.parentElement && d.parentElement.closest('details')) d.open = true; }
```

- on `toggle`, if the opened row does not fit under its line, the line glides to the top of the screen;
- a link into a closed row opens it: on load, on a click on any `a[href^="#"]`, and on `hashchange`;
- gliding uses `behavior: 'auto'` where `prefers-reduced-motion` is set.

`html { scroll-padding-top: calc(var(--bar) + 28px) }` already keeps targets clear of the bar. Do not also put
`scroll-margin-top` on targets: the two add up.

## 4. Charts, and the weight of a win

One wrapper for every chart:

```js
function chart(root, build, duration) {       // build(width, root) draws and returns frame(p), p in [0, 1]
  const draw = (p) => { root.textContent = ''; width = root.clientWidth; if (!width) { frame = () => {}; return; } frame = build(width, root); frame(p); };
  ...
  new ResizeObserver(() => { if (Math.abs(root.clientWidth - width) > 4) draw(played ? 1 : 0); }).observe(root);
  new IntersectionObserver(([e]) => { if (e.isIntersecting) play(); }, { threshold: 0.35 }).observe(root);
}
```

- Each chart is a function of the data that returns `(W, root) => frame`. It lays itself out for the width it is
  given, with a compact branch under about 560 px, and never relies on CSS to shrink it.
- It plays once (1300 ms, ease-out cubic, from 35% in view), redraws finished on resize, and honors reduced motion
  by drawing the final frame.
- Content of a closed `<details>` keeps its layout size in current browsers but is not drawn, so a chart in a closed
  row is built at load and plays when the row opens. The zero-width guard covers browsers where it has no size.
- Hover: the row under the pointer stays, the others dim; a tile shows its value and full names in `tipBox`.
- Scores are printed as the paper prints them (`.84`, `−.12` with a real minus, when the paper drops the leading zero).
- Start from the starter's three: bars from a baseline, a heat map of ranks, a heat map of the largest effect per
  row and column. Add a form only when the paper's own figure has it.

**The wins carry the weight** ("bigger boldness of big wins"):

- In heat maps and tables, first place is set in the heaviest weight (`.cell-t.top`, 700), and the rank tints rise in
  strength from third to second to first. The method's summary cells (mean rank, rating) can sit one size up.
- On a dark ground the best rank is the lightest tile. The starter's ramp, ranks 1, 2, 3, 4 to 7 and 8 or worse:
  fills `#b7d3f6 #5598e7 #256abf #184f95 #1c2029`, label inks `#0b1526 #fff #fff #c9d6ea #8b8b93`, an empty tile
  `#19191d`. The ramp was checked with the `dataviz` skill's validator; an earlier `#104281` failed its 2:1 contrast floor and
  was replaced. Ties take the next whole place (`Math.ceil`).
- Emphasis is allowed only because every value stays printed in its tile. The same weight goes to whichever method
  is first in a column, the paper's or a rival's.
- Other tiles take their ink from the tile's luminance (`inkOn`), so every value is readable.

## 5. Definitions under the pointer

Any element with `data-term="<name>"` (an SVG label, a table header) shows that term's line from
`results.json` (`tasks[].about`, `tasks[].metric`) in one shared tooltip (`termTips`). The builder writes those lines
from the paper and checks them against its text. Mark only elements that are terms: a stray `data-term` gives a help
cursor that leads nowhere.

## 6. The divider and the gallery dialog

- `.cmp` holds two images and a transparent `<input type="range">` over them; the range's value drives `--pos`. A
  drag, a tap and the arrow keys all work, and images inside never start the browser's own image drag.
- The range carries `touch-action: pan-y`: a sideways drag moves the divider, a vertical swipe still scrolls the
  page. Any other widget states which gesture it owns in the same way, and `touch.js` proves both gestures work.
- Its two labels sit in opposite corners (`.cmp-tl` top left, `.cmp-tr` bottom right) so they cannot overprint.
- The gallery's detail view is a native `<dialog>` opened with `showModal()`: focus is trapped and returned, Escape
  closes, `html:has(dialog[open]) { overflow: hidden }` locks the page. A click on the dimmed page closes it.
- On phones the dialog fills the screen and its grid needs `grid-auto-rows: max-content`, or the picture (which has
  `overflow: hidden`) collapses its row and slides over the title.

## 7. The mark that shrinks into the bar

The bar's image is the only mark. `.mast-mark` is an empty slot beside the name. On every scroll and resize:

```js
const reach = slot.top + scrollY - y0;                 // the scroll at which the slot's top meets the bar position
const t = clamp(scrollY / reach), e = t * t * (3 - 2 * t);
mark.style.transform = `translate(${x}px, ${y}px) scale(${k})`;     // from the slot's box at t = 0 to none at t = 1
```

`transform-origin: 0 0` on the image. Follow the slot for the first 1.4 s as well (the name rises in on load) and
after the fonts are ready.

## 8. Things that rise once

`[data-rv]` elements fade up 14 px when they come into view (opacity over .9 s, transform over 1 s, siblings
staggered 80 ms through `--d`). Keep it for headings, numbers and statements. Do not animate paragraphs of running
text, and never loop anything.

## 9. Phones

- A rule with two classes (`.stats.five`) beats a later one-class rule in a media query (`.stats`): give the phone
  layout its own two-class rule.
- A hidden absolutely positioned element can still widen the page; closed things are `display: none`.
- `img, svg { max-width: 100% }` shrinks an SVG wider than its box. A chart that must scroll sideways needs a
  `min-width` on its root inside `.scroll-x`; prefer a compact layout instead.
- Touch has no hover: whatever shows under the pointer needs a tap path (the dialog, a tap on a term).
- A canvas inside a sideways-scrolling wrapper must not carry a `touch-action` that blocks the wrapper's swipe or
  cancels its own drag: `touch-action: pan-y` on such a canvas fired `pointercancel` half-way through a lasso, so
  drawing a region became a tap on phones. Give the gesture to one owner and test it with `touch.js`.

## 10. The builder: checked numbers and guards

`assets/starter/pipeline/build_results.template.py` shows the shape:

```python
out = {...}                                   # only what the page draws
check_page(out)                               # every number and quoted sentence of index.html against records and TeX
for key in NOT_DRAWN: del out[key]            # checked, not shipped
```

`check_page` also holds the guards. Examples that earned their place: no p value above the author's threshold in
the page text, no "confidence interval" or "error bar" where the author's display rule bans them (the paper keeps every
interval; see section 3 of SKILL.md), no dot between phrases in any page source, no tagline
element, no citation block before the paper is citable, no retired name of a model variant (after a renaming, the
old name must leave no trace in text, charts, table, code and tests; sweep with grep, then add the guard). A guard
costs one line and saves a round with the author.

Keep six decimals in the JSON and round when printing: rounding twice can print `−.042` where the paper prints
`−.043`.

## 11. Large data

- Keep every file under the host's limit (GitHub rejects 100 MB and warns at 50): split big binaries at chunk
  boundaries and let the viewer fetch what the view needs by HTTP range.
- Pack coordinates and colors as small integers; ship images as WebP; lazy-load everything below the first screen.
- **Measure the deploy size against the host's time limit before the first push.** GitHub Pages stops a deploy
  after ten minutes; a 711 MB site timed out.

Shrinking a point layer for a static host (done once, 567 MB to 255 MB, the site from 711 MB to 408 MB):

1. List file sizes. One layer was 80% of the site.
2. Drop every field the viewer never reads (an identifier per point was the case).
3. Quantize positions to what a dot can show: a 4096 grid per chunk, points sorted by y and y stored as deltas, low
   and high bytes in separate planes (planar bytes compress far better).
4. Store color as RGB565 (mean error 1.6/255, never above 4/255 per channel).
5. `gzip -9` each chunk, and teach the viewer to unpack into the exact GPU layout it already draws. Steps 2 to 5 are
   `scripts/pack_points.py`:

   ```bash
   python3 scripts/pack_points.py pipeline/cache/<layer>.npz public/data/<layer> --tile 128 --grid 4096 --probe
   python3 scripts/pack_points.py pipeline/cache/<layer>.npz public/data/<layer> --tile 128 --grid 4096
   ```

   The input holds `x`, `y`, `r`, `g`, `b` and an optional `type` per point (`.npz` or `.csv`); `--tile` is the chunk
   side in the data's unit. In the page, copy `assets/unpack_points.js`: `loadIndex()` reads the tile index,
   `fetchChunk()` fetches one tile by HTTP range and gunzips it in the browser, and `unpackPoints(raw, n, grid)`
   writes planar `u16 x, u16 y, u8 r, g, b, type`, the layout the original viewer already drew. Color is rounded to
   RGB565, which keeps every channel within 4/255 (plain truncation errs by up to 8/255).
6. Keep the original outside `public/` (`pipeline/cache/`), so the repack can be redone.
7. **Shoot the same close-up at the finest zoom before and after and lay the two side by side.** Every reduction for
   size gets this picture ("same dots, same colours, same places") before it ships.

**Outlines of many objects** (cells in a tissue section were the case; clusters in an embedding or objects in a scan
work the same way) are traced from each object's own points, so the viewer needs no segmentation file and no polygon
library:

```bash
python3 scripts/build_masks.py pipeline/cache/points.npz public/data/masks --objects pipeline/cache/objects.npz
```

- Per object: a random share of its points (10% was enough to trace an outline), points farther than 25 units from
  the center dropped (strays made giant hulls), concave hull at ratio .42, closed by 1.1 units and shrunk by .22 so
  neighbors keep a dark seam, simplified, clipped to a 30 unit disc around the center, then triangulated by
  constrained Delaunay so the GPU draws the fill as plain triangles.
- Objects run in batches of 20,000 so memory stays flat. Vertices are stored as int16 offsets in 1/128 of a unit
  from their tile's center, with the object's color and type; `unpackMasks()` in `assets/unpack_points.js` reads them
  back. The defaults are in µm from the original; every one is a flag.
- An object with too few points, or a hull under 6 square units, becomes a small disc (radius 3.2); the script
  reports how many did. Look at the outlines over their points at the finest zoom before they ship.

## 12. A paper figure that must stay an image

Prefer drawing a figure natively from the records (SKILL.md section 3). A schematic that cannot be redrawn is
recolored for the ground by rule, never dropped on a white plate ("the background transparent and not white, don't
just copy paste"):

```bash
python3 scripts/darken_figure.py fig.pdf public/fig/method.png --width 2400 --override 0A3D66=8EC9FF
python3 scripts/darken_figure.py fig.pdf --extract-images pipeline/cache/fig_tiles      # data tiles, untouched
pdftocairo -svg fig.pdf fig.svg && python3 scripts/darken_figure.py fig.svg public/fig/method.svg
```

- The rule, in OKLab: neutral and pastel colors (chroma below .09) invert their lightness between the ground and an
  ink of L .93, with chroma times 1.15; saturated colors keep their hue, and one darker than L .55 is lifted to
  `.55 + (.55 − L) · .5`; pure white becomes the ground and turns transparent; `--override` maps the method's named
  colors to the page's.
- PyMuPDF renders with alpha and premultiplied samples; the script un-premultiplies before recoloring. In SVG it
  skips colors inside `<mask>` and keeps white glyphs on colored boxes white.
- An embedded image whose border ring is dark or see-through is kept exactly; an opaque one on a light ground is
  recolored like the page. **A data image is never recolored**: one pale data tile came out wrong, so data tiles are
  taken from the PDF as originals with their soft mask (`--extract-images`) and placed over the darkened schematic.
- Then look at every figure on the page ground.

## 13. TeX labels in canvas figures
14. Method figures on the fx engine

Method figures drawn on a canvas carry their mathematics as TeX glyph outlines, so a label is exact TeX at any size
and color with no font or image to load:

```bash
python3 scripts/tex_labels.py pipeline/labels.json public/data/tex.json --used-in public
```

- `labels.json` maps an id to TeX in text mode (`"loss": "$\\mathcal L$"`). Each label is typeset on its own tight
  page (article class, amsmath), and PyMuPDF reads back where each glyph outline sits. `pdftocairo` was tried first
  and rescales small pages slightly, which put glyphs in the wrong places.
- `--used-in` reads the page code for the ids it asks for, leaves out labels nobody asks for, and fails if the code
  asks for one that does not exist. The first real build held 141 labels.
- In the page, copy `assets/tex.js`: `await loadTex('data/tex.json')`, then `tex(ctx, id, x, y, { size, align,
  color })` on the canvas, `texBox(id, size)` for layout, and `upgradeTex()` for `[data-tex]` elements in running
  text, which keep their text for screen readers.

## 14. Method figures on the fx engine

Method figures run on `assets/fx/core.js` (with `parts.js` for plates, arrows, a data window with a scale bar and a
turnable sphere, and `fx.css`). Copy `assets/tex.js` to `public/tex.js` and `assets/fx/` to `public/fx/`;
`assets/fx/example.html` is a toy scene to start from.

- A scene is a list of steps, each with a caption from the paper (the `<ol class="fx-steps">` of the figure, which
  stays a readable list without script) and one `draw(ctx, s)` that is a function of the timeline time `s.t`.
- The engine plays once when the figure comes into view, rests on a finished frame before and after (nobody scrolls
  past an empty canvas), jumps on a step chip, skips to the end on a click, and shows finished frames under reduced
  motion. The loop runs only while something moves.
- It owns its pointer handling: a vertical swipe on the canvas scrolls the page, and a touch drag is kept from the
  browser only where the scene's `grabs(x, y)` claims it. This is the fix for the lasso that ended in
  `pointercancel` (section 9). With `grabs` removed from the example's lasso, `touch.js` reports the steep drag
  canceled again.
- It exposes `el.__fig.seek(u)` on each figure element, u from 0 to 1 over the whole timeline, which is the hook
  `sweep.js` needs: `SEEK='el.__fig && el.__fig.seek(t)' FIGS='figure.fx' node pipeline/sweep.js`.
- A drawing claims no more than the paper (one drawing showed four levels where the paper's table has three).

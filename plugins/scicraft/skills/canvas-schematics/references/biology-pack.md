# Biology pack (`pack_bio.js`)

For concept and method figures that show cells, tissue, molecules and masks: a few soft pastel
organic cells floating in white space, natural molecule scatter, dashed masks, very little text (a
short title, at most one subtitle in a light weight, a tiny legend). Use the pack whenever living
things are drawn; never draw them in matplotlib ("this is so bad").

## Cell types

Each type is `{fill, nuc, dot, bounds}`: soft fill, saturated nucleus, molecule color, darker outline.

| Token | fill | nuc | dot | bounds |
|---|---|---|---|---|
| `PAL.orange` | `#fadbb2` | `#ea9f37` | `#d66a2b` | `#c4621f` |
| `PAL.blue` | `#d9eefb` | `#3498db` | `#2980b9` | `#2980b9` |
| `PAL.green` | `#c1e1c1` | `#489e34` | `#2d911b` | `#1e6612` |
| `PAL.mustard` | `#fbf2d9` | `#f1c40f` | `#e1b12c` | `#b38822` |
| `PAL.teal` | `#d1efe8` | `#46a596` | `#138774` | `#0f6f5e` |
| `PAL.lav` | `#e4d5f0` | `#8e5db8` | `#6e3d9e` | `#5e2d8e` |
| `PAL.rose` | `#f8d9e6` | `#d83a73` | `#b62e5f` | `#9e2a55` |
| `PAL.excluded` | `#eceef0` | `#b4bbc2` | `#aeb5bd` | `#b4bbc2` |

Color means identity, never method. Map the figure's own type names to these in `SCENE.TYPES` and
keep the map fixed across all panels.

## Primitives

| Call | Does | Defaults |
|---|---|---|
| `LIB.cellShape(cx, cy, r, shape, seed, {sx, sy, rot})` | outline with character: `round`, `elong`, `spiky`, `irregular`, `lobed`, `blob` | few low-frequency lobes, Chaikin smoothed (never a gear) |
| `LIB.drawCell(ctx, pts, type, opt)` | fill, white spacing halo, colored outline | halo 8 px, outline 2.4 px |
| `LIB.drawNucleus(ctx, x, y, type, r)` | solid nucleus | about 0.3 of the cell radius |
| `LIB.drawDot(ctx, x, y, 3.0, color, {halo, errorBorder})` | molecule | radius 3.0 everywhere in a figure |
| `LIB.scatterIn(cx, cy, r, n, rng)` | n seeded points inside 0.62 r | |
| `LIB.drawMask(ctx, pts, color, lw, dash)` | dashed organic mask | gray, [8, 6], 2.5 px; errors `PAL.err`, [5, 4] |
| `LIB.clusterMask(pts, padding)` | organic polygon hugging a point cluster | 28 vertices, Chaikin x3 |
| `LIB.ghost(ctx, pts, color, opt)` | faint copy of an earlier panel's cell | fill alpha 0.10 (0.08 to 0.12 lighter), dashed outline alpha 0.30 |
| `LIB.colorByCluster(items, clusterOf, palette)` | color by cluster id | see below |
| `LIB.densityGlow(ctx, x, y, r, rgb, a0)` | the one allowed radial shading | density blobs only |

`assets/region_example_bio.js` shows a tissue scene with four call-outs and a 2 x 2 grid of cell-shape
vignettes; `assets/scene_template.js` is the shared scene.

## Habits that held up

- **Masks are organic polygons, never circles.** Use `drawMask` on a `cellShape` or a `clusterMask`.
- **One scene, every stage.** When panels show the same field at several steps (input, graph, output),
  draw it from `SCENE` so the cells and molecules are identical, from one seed. Never re-sample per
  panel or per zoom; crop the same field. Ghost the cells of an earlier panel behind a later one
  (`LIB.ghost`) so the reader sees it is the same place.
- **Color by cluster, never by discovery order.** Two separate pieces of one cluster must share its
  color; sequential assignment gave the second piece a new color and told the wrong story.
- **Colors stay consistent across all panels.** A molecule that is orange in panel one is orange in
  panel five; noise stays gray (`PAL.greyPt`).
- **Warm and cold edges**: high similarity `PAL.highSim` `#FF9500`, low `PAL.lowSim` `#5AC8FA`;
  positive edges solid `PAL.ok`, negative dashed `PAL.err`. The dash carries the difference.
- **Gentle breathing room.** Let cells sit and touch like tissue, with the white halo between them,
  and leave space around the group. An edge-to-edge tessellation reads as a texture.
- **Real images**: a dark field (`PAL.imgBg`), thin bright outlines carrying the type by outline
  color, small bright dots, a white scale bar rounded to a multiple of 5 um at its true length.
- **Keep a set's titles one size** and shorten them to fit.

## Spacing that avoided overlaps

From the legacy anti-overlap checklist, restated in tiers instead of the obsolete 75 px sizes:

- A rotated column header needs vertical clearance of about its length times the sine of its angle
  above the matrix origin.
- Stack legend items vertically, 1.3 times the line height apart, when a horizontal legend collides.
- Put before and after labels outside the plots they name, never inside.
- Offset a cell's type label above the cell by its radius plus about one L2 line.
- Set multi-line formulas at a line spacing of 1.3 times the font size or more.

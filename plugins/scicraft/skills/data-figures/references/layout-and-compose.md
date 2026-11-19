# Layout and composition

## The order of work

1. Write the figure's geometry: canvas width from the venue (`S.WIDTH_MM`), the letter band, row tops, each
   panel's x, y, w, h in mm, gaps. Keep it in one place that both panels and composer read: the composer's
   `layout.json`, or a `_prep/<fig>_geometry.py` module the panel scripts import and that writes the layout.
2. Render the mock-up: `python3 scripts/compose.py layout.json --mockup` draws each box (face `#E8EEF6`, edge
   `#3A3A3A`, 0.6 pt) with its letter, name and size in mm. Settle shared rows, full-width rows and aspect ratios
   before any data is drawn. Include the panel letters in the mock-up.
3. Draw each panel at exactly its box: `fig = S.fig_mm(w, h)`.
4. Compose, then look (`visual-qc.md`).

## Grid rules

- **Rows share a height; heights never form a patchwork.** A tall panel may span whole rows.
- **Panels of one kind share one axes box**, byte for byte: same figure size and same axes rectangle give data
  grids identical in size and position, with decorations in fixed margins around them. Divide a row evenly ("make
  a,b,c, e,f,g same size (divide width in 3)").
- **Align the plot areas**: match axes heights and center lines across a row; a bar panel beside an image tile gets
  an axes box equal to one tile, center-aligned. Titles center on the axes, not on the panel with its labels.
- **Spacing**: "not too little (like legends of panels of d) not too much (like a-b-c)". About 9 mm between columns
  on a 183 mm canvas with 26 mm boxes worked once labels moved into a shared legend.
- **Size a panel to its content**, not to a round number: left labels plus grid plus margin. Dead right margins
  were the most frequent layout complaint ("white space" appears 69 times in one month of prompts).
- **Nothing is cut.** Enlarge the page rather than shrink fonts: "make the page bigger as the top titles are going
  out! without relative drop of font sizes". Panels may overlap each other's empty margins.
- **Rotated tick labels need a bottom band sized to the longest label**; abbreviate only the one label that is far
  longer.
- **A long color-bar label wants a horizontal bar** under the grid; group-bracket labels must fit their span
  (shorten the words).
- **Panels in a row that share their rows** (heatmaps or bar strips over one method list) print the row labels on
  the left-most panel only, and the others take the same row grid. Repeated labels take width from every plot area
  and push dense matrices below a readable cell size.

## Coupled sizes

- Two panels at equal height filling width W with gap g, panel A of aspect a (width/height) beside a square B:
  `h = (W − g) / (a + 1)`, `w_A = h × a`, `w_B = h`. A shorter heatmap means a wider aspect means a smaller square
  partner; to really shrink, cut intrinsic overhead (an icon row, a title band).
- Two pre-made PDFs (for example two LaTeX tables) that must match: place both at one common scale
  `s = (usable_w − 2 × gutter − gap) / (w1 + w2)` of their natural widths, never each fitted to its own box; for equal
  heights typeset them to the same natural height (within about 2 pt). This is the one case where the composer
  scales, and it scales both by the same factor. Fitting each to its own box drew "b and c are different font sizes
  / different heights".

## Placement traps

- `S.axes_mm` measures y from the top; `fig.text` measures y from the bottom as a fraction. Mixing them threw a
  color-bar key to the opposite edge. Use `S.text_mm` or `y_frac = 1 − mm_from_top / H_MM`.
- `ax.set_title` centers on the axes box, which shifts with a wide left margin.
- `va="center"` sits row labels 0.14 to 0.18 mm high; `va="center_baseline"` lands within 0.01 mm.

## The composer

`scripts/compose.py` (PyMuPDF):

- Places each panel PDF at (x, y) mm at native size with `show_pdf_page(..., keep_proportion=True)`; never
  stretches, never rasterizes.
- Reports and exits 1 when a panel's PDF differs from its box by more than 0.2 mm (`--tol`), runs off the page, or is
  missing. A panel drawn at the wrong size is fixed in its own script.
- Stamps letters after all panels: panel PDFs may carry an opaque cell or image, and a letter stamped first was
  painted over ("a" and "c" clipped). Default position (x + 0.3, y + 4.2) mm, overridable per panel with `lx`, `ly`.
- Letter face: Helvetica Neue Bold extracted from the macOS collection, else the built-in Helvetica Bold, or any
  file given with `--letter-font` (use the host document's bold face). Where only a regular face exists, the older
  composer faux-bolded by stamping the glyph four times at offsets (0, 0), (0.2, 0), (0, 0.2), (0.2, 0.2) pt.
- Writes PDF (`garbage=4, deflate=True`), PNG at 600 dpi and an SVG with live text (subset prefixes removed, family
  and weight named, one start x per text run so a resized run reflows in Illustrator or Inkscape). `pdftocairo -svg`
  outlines every glyph: do not use it. Check the SVG in a WebKit renderer (`qlmanage -t` on macOS); MuPDF's own SVG
  reader drops clips and dashes.
- Draws no captions, titles or annotations of its own: those live in the panels and in `caption.md`.

## Panel scripts

Start from `assets/panel_template.py`:

- Docstring: what is plotted with the metric's definition and direction, the frozen table it reads, the spread
  statistic, and `Adapted from: <upstream script>`.
- At most about 150 lines (target 100). Aggregation and long plotting code go to `_prep/`. No chatty comments.
- `W_MM, H_MM` and the axes box come from the geometry; assert the invariants of the data being drawn.
- A variant (a shorter summary version) is selected by an environment variable, never by a copied script.
- Every panel script renders on synthetic records when no data is given (the template's demo mode; one rebuttal
  panel used a `SELFTEST=1` switch), so tick spacing and label overlap are checked before the real records arrive.
- One public script per panel. A shared renderer per chart form lives in a utilities module once a second figure
  needs it; consolidate it under a render-parity check (`visual-qc.md`).

## Patching a renderer you must not edit

When an upstream script draws the reference look and may not be changed:

1. A local `_prep/render_<name>.py` puts the upstream folder on `sys.path` and monkeypatches shared functions before
   importing the renderer.
2. It reads the renderer's source, string-replaces hard-coded literals, and runs
   `exec(compile(src, path, "exec"), module.__dict__)` in a fresh module; no upstream file is touched.
3. It sets `sys.argv` and calls the renderer's `main()`. Environment variables select variants.

To change one figure without touching a shared drawing function, post-process after it: iterate `ax.texts`, match
by content or color, then recolor or remove. Font sizes that the drawers read at draw time can be changed by
setting the source module's size globals before the call.

Patch a figure script by exact substring replacements that each assert one match. Line numbers shift with every
earlier edit, and a patch placed by counting lines once landed in the wrong function. After patching a script that
holds raw strings, parse it before rendering, because a broken raw string surfaces only at render time otherwise:

```bash
python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" panel.py
```

A rename is not done until every rendered surface is rebuilt: re-run each renderer and then the composer; grep the
rendered sources separately from the docs.

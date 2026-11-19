# Workflow, checks and failure modes

Figure-making as a disciplined loop: choose how much text belongs inside, draft, check
statically, compile, look at the render, repair the smallest defect, and check that the
figure says something true. The recipes live in the other references; this file owns the
process and the failures that compile cleanly but look or read wrong.

The QA discipline here (presentation modes, the render-and-inspect loop, the static
checker, the exact-versus-schematic gate, the bounded repair loop) uses ideas and
conventions learned from the Patrick-Healy/tikz-diagrams-skill; the text and the script
here are this skill's own (see THIRD_PARTY.md).

**Contents**
1. Presentation modes
2. The render-and-inspect loop
3. The theme smoke test
4. Static safety check
5. The "compiles but wrong" catalog
6. The exact-versus-schematic gate
7. Restyling a stock matplotlib plot
8. Bounded repair loop
9. Iterate with \input, deliver inlined
10. A minimal TeX tree
11. Self-check before delivering

---

## 1. Presentation modes

Decide first how much explanation belongs inside the figure. The mode sets label density,
never the palette or the geometry.

- **research** (the default for papers): direct labels, axis labels, terse glosses on the
  objects. No explainer boxes, no sentences. Interpretation goes in the caption.
- **teaching** (lecture slides, tutorials): one sentence of guidance is allowed, clear of
  the key comparison and with room around it.
- **compact** (multi-panel figures, appendix grids): direct labels only, no notes, no
  framed boxes.

Produce paired teaching and research variants only when asked, with identical geometry.

## 2. The render-and-inspect loop

A `.tex` that compiles is not a finished figure. The compiler cannot see overlap,
clipping, crowding or a mislabeled curve.

```
draft -> static check -> compile -> render PNG -> LOOK -> repair smallest defect -> re-render
```

One command does the first four steps and writes a versioned PNG:

```bash
python3 scripts/render_figure.py fig.tex                 # -> fig_v01-1.png, then fig_v02-1.png ...
python3 scripts/render_figure.py fig.tex --theme serif   # the other theme, same source
```

By hand, the same steps are:

```bash
python3 scripts/check_tikz_safety.py fig.tex
pdflatex -interaction=nonstopmode -halt-on-error fig.tex
pdftoppm -png -r 170 fig.pdf fig_v03
```

Then open the PNG and look for: overlapping text, labels or arrowheads clipped at the
edge, a blank or 12 x 12 pt page, cramped glosses, an accent doing two jobs, an arrow
whose direction misstates the flow, text smaller than its neighbors, a hue that is not in
the palette. Fix one thing, render again, look again. Versioned names matter: a cached
viewer once showed an old PNG and a fix was reported that had not landed.

For a frame deck, render every page and look at the first, a middle and the last frame
(`render_figure.py` prints the three paths and fails when frame sizes differ).

When the user is judging a look (a density field, a palette, a shape), show the PNG every
turn. They cannot judge a description.

## 3. The theme smoke test

After any edit to the preamble, compile this body in both themes and look at both PNGs
side by side. It touches the font switch, the palette, the block and token grammar and
the operator stack.

```latex
\begin{tikzpicture}[base]
  \node[block] (a) {Encoder $f_\theta$};
  \node[block accent, right=10mm of a] (b) {Predictor};
  \draw[flow] (a) -- (b);
  \tokenrow{(0,-1.2)}{tokenvis}{4}{4.4mm}
  \tokenrow{(1.8,-1.2)}{masktoken}{2}{4.4mm}
  \node[panel] at (-1.2,0.9) {a};
  \opstack{(5.5,0)}{$\mathcal{E}_\phi$}
  \fill[contrast] (4,-1.2) circle (2pt); \fill[accent] (4.3,-1.2) circle (2pt);
\end{tikzpicture}
```

```bash
for t in minimal serif; do python3 scripts/render_figure.py smoke.tex --theme $t; done
python3 scripts/render_figure.py smoke.tex --family cm
```

## 4. Static safety check

`scripts/check_tikz_safety.py` (standard library only) runs before every compile.
Errors: a body without the preamble, a preamble with no body, unpositioned edge labels,
long node labels without `text width`, unbalanced environments or braces,
`plot[smooth cycle]` coordinates joined by `--`, `\newpage` in a standalone file, a
`\foreach` variable that shadows a TeX macro. Warnings: `rand` without a seed, a frame
deck without a locked bounding box.

```bash
python3 scripts/check_tikz_safety.py fig.tex
python3 scripts/check_tikz_safety.py figures/        # every .tex below the folder
python3 scripts/check_tikz_safety.py --strict fig.tex
```

It complements looking at the render and never replaces it.

## 5. The "compiles but wrong" catalog

- **Empty 12 x 12 pt PDF.** A body was compiled without the preamble. Build preamble plus
  body as one file.
- **Edge labels on the line.** `\draw (a) -- node {x} (b);` drops the label onto the
  arrow. Use `node[above]`, `node[midway, right=4pt]` or a separate node.
- **Clipped at the border.** Labels, arrowheads, braces or rings near the edge are cut by
  the standalone crop. `border=6pt` helps; raise it or move the element in.
- **Connectors through text.** End arrows at anchors (`(a.north)`) so they stop at the
  box edge.
- **Crowding.** Remove words (switch toward compact mode) before shrinking type.
- **Long node text wraps unpredictably.** Give it `text width` and `align=center`.
- **`\foreach` variable clashes.** `\o` is a letter, `\c` and `\d` are accents, `\fi` is a
  TeX primitive. Use `\x \y \k \n \ff`.
- **The figure moves on every compile.** `rand` and `rnd` reseed each run. Call
  `\pgfmathsetseed{N}` before the loop, or generate the points in Python with a seed.
- **"Cannot parse this coordinate".** `plot[smooth cycle] coordinates {...}` needs points
  separated by spaces, never by `--`.
- **"Unknown operator 'a'".** An inline `\foreach` with `\pgfmathsetmacro` concatenated
  numbers before `and` in `ellipse (rx and ry)`. Compute the radii in Python and emit them.
- **Frame jitter.** Each frame of a deck is cropped to its own content, so a moving
  element shifts the crop. Put `\path[use as bounding box] (...) rectangle (...);` first
  in every frame, sized to the largest extent.
- **A marker swallowed by its curve.** Draw a white halo under it:
  `\fill[white] (p) circle (r+2pt)` then `\fill[accent] (p) circle (r)`.
- **Digits in the wrong font.** A node outside `[base]` falls back to the document
  family. Give it `font=\figfont...`.
- **Rounding shown raw.** `\tt` printed as 0.59999; use
  `\pgfmathprintnumber[fixed,precision=1]{\tt}`.

## 6. The exact-versus-schematic gate

Visual plausibility is not correctness. For any figure with curves, distributions,
thresholds, scaling laws, geometry or measured brackets, decide first whether it is
**exact** (generated from stated equations, data or coordinates) or **schematic** (a
qualitative sketch).

| | Exact | Schematic |
|---|---|---|
| geometry | plotted from the function, the data file or the code's output | hand-placed, clearly qualitative |
| ticks and numbers | real values | none that look measured |
| fitted lines, brackets, gaps | measure the real object | none |
| a density drawn as exact | integrates to 1 | no such claim |
| caption | names the source | says "schematic" or "illustrative" if in doubt |

Checks before delivering: do labels attach to the right curve or region? Are ours and the
baseline in the right places? Does the accent mean the same thing in every panel? Would a
careful reader infer a stronger numerical claim than the records support? If the math
cannot be specified, treat the figure as schematic and do not invent precise-looking
geometry.

## 7. Restyling a stock matplotlib plot

Stock matplotlib output has a fixed fingerprint; each tell maps to one corrective.

| matplotlib tell | Corrective |
|---|---|
| all four spines | `spare axis`: left and bottom only, `clip=false` |
| dashed grid on both axes | one faint horizontal grid (`ymajorgrids, grid style={mist!50, line width=0.3pt}`) or none |
| tab10 blue, orange, green | `accent`, `contrast`, `slate` (`c1` to `c3`) |
| solid markers of about 6 pt | `mark size=1.2pt`, or no markers on a smooth curve |
| framed legend inside the data | frameless (set by `spare axis`), in a corner of empty space, or inline labels |
| DejaVu Sans labels beside CM math | the theme's one family for text and math |
| no panel letters on a faceted row | bold lowercase `a b c` per `groupplot` cell (`plots_curves.md`, section 10) |

Data panels that belong in matplotlib (a results figure assembled with other matplotlib
panels) go to the `data-figures` skill.

## 7b. A raster tile inside a vector figure

A raster tile placed inside a vector figure (a field map, a dense scatter, a heatmap image) is rendered at
twice its print size (`SUP = 2`) and placed at print size. Text then stays at one size across the figure and
the tile stays sharp. Quote marker areas in printed pt² and draw them with `s = area * SUP**2`: without the
factor every marker prints at a quarter of its intended area. Contrast and floor settings for field tiles are
in the sibling `embedding-maps` skill.

## 8. Bounded repair loop

On a compile or visual failure:

1. Read the exact error or name the specific visual defect.
2. Find the smallest source region responsible.
3. Patch only that region.
4. Re-run the exact check that failed.
5. Continue from the current source; never rewrite the whole figure.

**Two strikes.** If the same class of failure survives two focused repairs, step back:
the figure needs to be simplified or split, not patched a third time.

## 9. Iterate with \input, deliver inlined

While iterating on generated geometry, keep it in separate files and pull them in with
`\input{frag_L1.tex}`, so a regenerated fragment takes effect. Appending a generated body
once (`cat body.tex >> fig.tex`) freezes a copy and later regenerations silently do not
apply. At delivery, inline every `\input` (the generator scripts do this with
`--preamble`), copy the file to an empty folder, compile it there, and deliver that file:
a figure that needs files the user does not have is not delivered.

Generated density figures can reach about 0.5 MB of coordinates. That prints crisply;
mention it so the size is no surprise.

## 10. A minimal TeX tree

On a full TeX Live the preamble compiles as is. On a minimal tree (a "basic" scheme) a
bare compile can fail for reasons that are not recipe bugs:

- `! LaTeX Error: File 'standalone.cls' not found.` (also `preview.sty`);
- `! Font ... Metric (TFM) file not found.` for the URW Helvetica (`phvr8t.tfm`) or URW
  Palatino faces;
- a TikZ library the figure loads is missing (historically `shadows.blur`, no longer used).

Two ways forward. Install the missing pieces (`tlmgr install standalone preview` and the
URW base-35 fonts), or place them by hand in the user tree and run `mktexlsr` when
`tlmgr` cannot write. Or check the geometry alone with `\def\figfamily{cm}`, which needs
no URW fonts: it proves the colors, styles and layout but not the final typeface, so the
typeface still has to be checked on a full tree. Do not conclude that the preamble is
broken.

`animate.sty` is optional and often missing; check with `kpsewhich animate.sty`. The
default animation path needs no extra package (`animation.md`).

## 11. Self-check before delivering

A figure is done when:

- the safety check passes and the file compiles with zero errors (`render_figure.py`
  prints the overfull-box and missing-character counts; both should be 0);
- the PNG is not blank and has been looked at, in every theme or font it will ship in;
- no overlapping words, no clipped labels or arrowheads, nothing in the title band;
- one visual grammar, one accent meaning, whitespace where it was crowded;
- quantitative content is marked exact or schematic per section 6;
- generated geometry came from the real code or data with a fixed seed, and the numbers
  the figure shows match its `facts.json`;
- a frame deck has a locked bounding box and its first, middle and last frames were
  looked at, with no label shown before it is true;
- the inlined `.tex` compiled in an empty folder;
- the `.tex` and `.pdf` are handed back (the PNG is only a preview), with one line on
  what was not checked.

Record the outcome of the design pass in one word: keep, simplify, split or redo. A
figure that tries to be two figures (an architecture and a results plot) is split.

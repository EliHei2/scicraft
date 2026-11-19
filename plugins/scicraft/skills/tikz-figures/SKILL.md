---
name: tikz-figures
description: Draws publication TikZ and PGFPlots figures for papers (architecture and method diagrams, teacher-student and other training schematics, distributions and fields, graphs and trees, multiscale zoom panels, plots from records, frame-deck animations) from one preamble with a theme switch, compiled and looked at as PNG. Use it whenever a figure will be drawn in TikZ or PGFPlots, even when the user only says "make Figure 1", "draw my architecture", "redo this schematic in LaTeX", "the boxes overlap", "this looks like a slide", "the tree is fake" or "camera-ready is Friday". It holds the locked minimal 4-tone sans theme and a serif option, the block, token-row, depth-stack and connector grammar, the exact-versus-schematic gate, generators that emit geometry from real code with fixed seeds, a safety checker and a render script, and tested recipes. For matplotlib data panels use data-figures; for HTML-canvas schematics and tissue cartoons use canvas-schematics, or tissue-figures from the biology plugin.
---

# tikz-figures

How to make a TikZ or PGFPlots figure that a demanding author accepts: a flat, sparse
vector figure in one locked style, whose geometry is real and whose render was looked at.
Distilled from a year of architecture, concept and overview figures for machine-learning
and spatial-data papers, and from two earlier figure skills merged here. Most rules are
something the author asked for or threw out, so each comes with its reason. Where the
author of the figure at hand says otherwise, they win.

> **PRIME DIRECTIVE: draw the real object in the locked style, and look at the render
> before calling it done.** Geometry comes from equations, data or the method's own code,
> or it is plainly schematic. Every figure is compiled, rendered to PNG and inspected.

Three failures cost the most time. Guard against them from the first minute:

1. **The cramped circuit and the slide.** A hand-laid architecture figure that "overlaps,
   looks ugly, and does not show what the model is", or one dressed as a slide (titles as
   sentences, gray subtitles, shadows, pills, banners). Budget whitespace first, keep text
   near zero, use the grammar (sections 3 and 4).
2. **Fake geometry.** A hand-drawn tree ("some random tree"), a partition that does not
   match what the code computes, a zoom whose levels are re-sampled. Generate it from the real
   code with a fixed seed (section 6).
3. **Calling it done unseen, or restyling what was not asked.** A cached PNG fooled one
   check; a font flipped between morning and evening; several things "improved" at once.
   Render to versioned PNGs, change the smallest thing asked, decide the font once
   (sections 2 and 7).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The host document**: its body font and math font (sans, Palatino, Times with Computer
  Modern math), the column width the figure prints at (an ICLR text block is 396 bp; a
  journal column is about 89 mm, a full page width about 183 mm).
- **The paper's other figures**, in any tool. A new figure joins their family.
- **A reference figure**, if the author named one ("plot like Figure 4 of that paper",
  "copy that architecture style"). Reproduce it first (aspect ratio within about 2%, same
  arrangement and idioms), polish second.
- **The real code and data** behind every tree, partition, graph, point cloud, curve.
- **What the figure must show**: the one mechanism or claim, in a sentence. A figure that
  needs two sentences is two figures.

**An ML architecture or method figure is vector, and this skill is its default home.** A plot library
drawing the boxes was rejected ("no python!! this is tikzzzzzzz"). The sibling `canvas-schematics` skill
draws an architecture figure only when the user asks for canvas. The author later preferred Typst for figures
and typesetting; this package ships no Typst recipes, so say that when a user asks for Typst.

Do not draw new figures where the job is to place the author's existing ones (a book
chapter, a talk built from the paper): crop and place theirs, and say when nothing fits.

Work in a folder per figure:

```
figures/<figure>/
├── <figure>.tex       preamble + body: the delivered source
├── gen_<figure>.py    only if geometry is generated (section 6)
├── frag/, facts.json  generated fragments and the numbers they carry
└── <figure>_vNN-1.png versioned previews (never delivered)
```

## 1. One preamble, two themes

Copy `assets/preamble.tex` verbatim as the top of the figure file; the body (one
`tikzpicture`) goes before `\end{document}`. Two switches at its top:

| Switch | Values | Default |
|---|---|---|
| `\figtheme` | `minimal` (sans, 4 tones: dark blue, light blue, mustard gold, grays), `serif` (Palatino, black outlines, blue family, one red) | `minimal` |
| `\figfamily` | `auto`, `sans` (helvet + sansmath), `serif` (mathpazo), `cm` (Computer Modern via lmodern) | `auto` |

Set them per build without editing: `pdflatex "\def\figtheme{serif}\input{fig.tex}"`, or
`python3 scripts/render_figure.py fig.tex --theme serif`. Every color and style keeps one
name in both themes, so a body switches without edits. `references/themes.md` has every
hex value, the line weights and the table of renamed tokens.

## 2. Font and palette

- **The minimal theme is the default** for machine-learning figures: sans text and sans
  math, which is most of what makes a figure read as a modern ML paper instead of LaTeX
  defaults. The author called their figure in this look "the best I made myself".
- **Match the figure's math to the paper's math; this overrides the default.** A venue
  paper with Computer Modern math (Times text and CM math, as in ICLR, NeurIPS and ICML
  templates) gets `\figfamily{cm}`: the author's latest submitted paper figures moved from
  Helvetica to the TeX font for this reason, and that was final. A Palatino book or report
  gets the serif theme. Sans stays for preprints, sans hosts and stand-alone figures.
- **Decide the font once, record it in the project notes, never flip back.** A switch
  from Helvetica to the TeX font and back cost a full round on every figure.
- **One accent, one meaning.** `accent` (#2B50AA) is the protagonist; `contrast` (gold
  #B8860B in minimal, red #F2545B in serif) is its one foil: held-out, target, masked.
  Structure is `ink` and grays. If a third saturated hue appears, delete it.
- **The contrast means the same thing in every figure of the paper.** Recolor a diverging
  map onto the blue ramp so gold is not spent on a colormap.
- **An ordinal index is a lightness ramp** (`ramp1` to `ramp8`, or `navy!28` to
  `navy!100`), never a categorical palette: depth, time, stage, scale.
- **Style is the second channel**: solid observed, dashed predicted, dash dot
  extrapolated; at most three edge relations, more go to a legend keyed by line style.
- **Flat**: no gradients, no drop shadows, no 3-D unless the data are 3-D. Depth is an
  offset faded copy. One radial `\shade` for a density blob is the only exception.
- **Emphasis only where the values carry it.** Making a baseline pale is allowed where it
  is weak in the numbers; "the right answer to 'make it paler' is usually 'scope it to
  where it's real'".

## 3. The grammar

Every architecture and method figure is built from a small vocabulary, all defined in the
preamble (`references/grammar.md` has the table and compiled snippets):

| Element | Style or macro |
|---|---|
| module, the one focal module | `nnblock` / `block`, `nnblock accent` / `block accent` |
| sub-layer inside a block | `nnlayer` |
| token rows, visible, held-out | `\tokenrow{(x,y)}{style}{n}{gap}` with `token`, `tokenvis`, `masktoken` |
| repetition and heads | `\nnstack`, `\StackBox` (2 to 3 faded copies, count on a brace) |
| a module shared by k inputs | `\opstack` (back copies send gray `agg`, front sends black `spine`) |
| data flow, support flow, weight copy | `nnarrow`/`flow`, `flowfaint`/`agg`, `emaarrow` (dashed slate) |
| zoom or cross-panel connector | `frustum` (`ink!45`, 0.4 pt, dashed) |
| a panel of real geometry | `frame` (`ink!85`, 0.6 pt, rounded 2 pt) |
| neighborhood, partition, tree | `egoring`, `egospoke`; `celledge`; `tnint`, `tnleaf`, `tedge`, `tpath` |

Canonical compositions, each a compiled recipe in `grammar.md`: the transformer block,
the teacher-student two-rail layout (context encoder over visible tokens, predictor with
gold mask queries, EMA target encoder with stop-gradient, rails meeting at a latent
loss), the mechanism inset, the scale spine, the kNN ego ball, the partition and its
tree, and tabular-model glyphs (suggested, not yet tested in real work).

- **Standard components are drawn in the field's convention.** Rotary position encoding is RoPE with its
  rotation sign, layer normalization is its own block apart from the feed-forward block, K parallel copies
  are an offset stack.
- **A mechanism is drawn as the code computes it.** A k-nearest-neighbor graph capped by a radius is a
  different drawing from k neighbors inside a radius. Check each drawn mechanism against the code.

## 4. Layout and text

- **Text near zero.** Panel titles are a bare symbol or a noun phrase of at most 4 words,
  never a sentence. Glosses on objects are at most 3 words. No caption prose, banners,
  arrow narration or paragraph glosses inside the image; at most one boxed core equation.
- **Panel letters** bold lowercase, no period, top left, aligned (`panel` style).
- **Never drop content while decluttering.** Remove words and chrome, keep every model
  component; "show really high level, not every detail but a sign of every step".
- **A mechanism figure makes the mechanism obvious**: draw the operation with labeled
  operands (Q, K, V into the score, then the output), plus one small inset for the one
  component a reader cannot guess. Vague arrows were rejected.
- **Domain-neutral vocabulary in a general method figure**: points, elements, regions,
  features. Domain words belong only in the domain panel.
- **Only defined symbols.** Drop every symbol the figure does not need. Keep the losses, parameters and
  operators the text names, and define each in a one-line legend inside the figure. No illustrative numbers
  ("don't give numerical examples like 0.69"): a value appears only when it is the real one.
- **Whitespace**: more than 40 to 45% of the canvas white in concept and overview figures.
  An architecture overview instead fills its canvas with the model ("more meat"), still
  with nothing overlapping. Data points in an architecture figure stay neutral.
- **One reading direction** (left to right, or bottom to top), joined by thin dashed
  connectors. Two to four clean panels beat eight cramped ones.
- **Text at print size.** Build the figure at the width it prints and include it at that
  width, so the preamble's `\figL`, `\figM` and `\figS` print at 7, 6 and 5 pt. Three tiers (7 pt titles
  and block names, 6 pt labels, 5 pt ticks and tags, nothing under 5 pt after scaling) plus the 8 pt panel
  letter, the same as in every figure medium (the sibling skill, `data-figures/references/style-tokens.md`). If a label does not fit, shorten
  it or give it room; never shrink it.
- **Nothing lies over anything by accident.** Edge labels are positioned nodes; arrows end
  at anchors; a skip connection passes behind the box it bypasses.

## 5. The exact-versus-schematic gate

Decide for every curve, distribution, bracket and coordinate which side it is on.

| | Exact | Schematic |
|---|---|---|
| source | equations, the records (`table {file.csv}`), the code's output | hand-placed |
| ticks, numbers, fitted lines, brackets | real, measuring the real object | none that look measured |
| caption | names the source and what bands mean (std over 3 seeds, a 95% interval) | says "schematic" when in doubt |

Plot values are read from record files, never typed into the `.tex`. A showcase example
(a window, a sample, an ego point) is chosen by a stated rule, recorded in `facts.json`,
and checked to be no artifact. A weak or contradicting result is shown as it is or moved
to the appendix with its number, never redrawn to look better. Details and checks:
`references/workflow_qa.md`, section 6.

## 6. Generated geometry and deterministic randomness

- **Generate every structural element from the real code.** A `gen_<figure>.py` imports
  the method's own function, runs it on a fixed-seed input, and writes TikZ fragments
  plus `facts.json` with every number shown. Two inputs when needed: a hero set (about
  230 points) for density, a toy set (about 50 points) for trees a reader follows.
- **One point field, nested crops.** Each zoom level is a crop of the same field. Do not
  thin the points of a level whose neighbors are computed on the full field, or a
  neighbor appears from nowhere.
- **Density is a KDE drawn as three nested filled bands** (relative levels 0.10, 0.36,
  0.66 at opacity 0.22, 0.42, 0.72, core last), never flat region fills ("political map")
  and never a blurred mask ("smeared paint").
- **Seeds everywhere.** `\pgfmathsetseed{N}` before any `rand` loop; seeded generators in
  Python with the seed in `facts.json`. Prefer emitted coordinates for a kept figure.

```bash
python3 scripts/density_zoom.py --out zoom/ --preamble assets/preamble.tex          # seeded synthetic field
python3 scripts/density_zoom.py --points field.csv --out zoom/ --preamble assets/preamble.tex
python3 scripts/tikz_emit.py --out frags/ --preamble assets/preamble.tex            # partition + its tree
```

`density_zoom.py` needs numpy, scipy and contourpy (installed with matplotlib); the other
scripts use the standard library. `references/generators.md` has the pattern and the
emitter API; `references/multiscale_density_zoom.md` the zoom rules.

## 7. Workflow

1. **Pick the mode** (research, teaching, compact; papers are research) and state the
   one thing the figure shows.
2. **Write** `<figure>.tex` = preamble verbatim + one `tikzpicture[base]`. Pull recipes
   from the references (section 9). Generated geometry goes in with `\input{frag/...}`
   while iterating.
3. **Check, compile, render** in one command (safety check, pdflatex with
   `-halt-on-error`, log read for errors, overfull boxes and missing characters, PNG at
   170 dpi under the next version number, blank-page and frame-size checks):

```bash
python3 scripts/render_figure.py figures/<figure>/<figure>.tex
python3 scripts/check_tikz_safety.py figures/        # the static check alone, on a folder
```

4. **Look at the PNG.** Overlap, clipping, crowding, a stray hue, an accent doing two
   jobs, an arrow that misstates the flow, black boxes where a glyph is missing.
5. **Repair the smallest defect**, re-render, look again. **Two strikes**: if the same
   class of defect survives two focused repairs, simplify or split the figure instead of
   patching a third time.
6. **Show the PNG every turn** when the author is judging a look; they cannot judge a
   description. Make the change asked, not several. Get sign-off stage by stage (layout,
   then density, then zoom), and confirm feel words ("cloudy", "brown not gold") with a
   quick choice of options.
7. **Deliver**: inline every `\input`, compile the file in an empty folder, hand back the
   `.tex` and `.pdf` (the PNG is a preview), and the generator with `facts.json` if any.

Process and failure catalog: `references/workflow_qa.md`. A figure that matters for
several days can take a design tournament of independent drafts judged against the spec
(`figure-development`).

- **When the house style keeps producing output the author rejects, stop iterating on it and copy one named
  exemplar.** Take a panel the author drew, or one figure of a named paper, as the theme. Build one concept
  per panel, compile each to PDF and PNG, and archive the failed attempts when restarting. Three weeks of
  schematic rounds converged only after this switch.
- **After every edit a fresh reader renders the figure** and reports overlaps and undefined symbols before
  the author sees it.

## 8. Animation

Most moving figures are better as a static row of panels; animate only when motion is the
argument (a point descending a loss surface, message passing spreading, a diffusion
sweep, a build-up). The default is a frame deck: add `multi=tikzpicture` to the class
options, write one `\Frame{k}` macro, loop `\foreach \ff in {0,...,N}{\Frame{\ff}}`, and
lock the bounding box in every frame (`\path[use as bounding box] ...`), or frames jitter.
`render_figure.py deck.tex --dpi 150` renders every page, fails if frame sizes differ and
prints the first, middle and last frame to look at. A label that asserts something
("converged") appears only in frames where it is true. Pacing: a highlight holds about
0.5 to 1 s, a new structure 1 to 1.5 s, the final state 1.5 to 3 s. GIF assembly needs
ffmpeg, ImageMagick or gifsicle; `references/animation.md` has the commands, the recipes,
the optional `animate` and beamer paths.

## 9. Recipes by figure type

| Figure | Reference |
|---|---|
| any architecture or method figure: grammar, transformer, teacher-student, mechanism, scale spine | `references/grammar.md` |
| pipelines, U-Net, action loop, multi-input model, routers, skips, operator pipeline | `references/architectures.md` |
| curves from a CSV with std bands, scaling laws, bars, scatter, boxplots, faceted rows | `references/plots_curves.md` |
| Gaussians, densities, loss landscapes, optimal transport, trajectories, vector fields | `references/distributions_fields.md` |
| graphs, message passing, plate models, Markov chains, equivariance, decision trees | `references/graphs_geometry.md` |
| equations, braces, arrows to terms, commutative diagrams, small tables in a figure | `references/math_layout.md` |
| multiscale density zoom with a kNN ego ball | `references/multiscale_density_zoom.md` |
| moving figures | `references/animation.md` |
| proteins, molecules, cells, tissue glyphs, embedding overlays (biology tier) | `references/bio_objects.md` |

## 10. Check before anything is handed over

1. `check_tikz_safety.py`: no errors; every warning understood (a seedless `rand` is a
   bug in a kept figure).
2. `render_figure.py`: exit 0, 0 overfull boxes, 0 missing characters, no blank page, equal
   frame sizes for a deck. Run it in every theme or font family the figure ships in.
3. The inlined `.tex` compiles in an empty folder.
4. **Look** at every PNG at full size: nothing overlaps or clips, no black glyph boxes,
   one accent meaning, the contrast used only for its role, text no smaller than the
   tiers, whitespace where it was crowded, panel letters aligned.
5. Every number in the figure and caption matches the records or `facts.json`; every
   schematic element is marked schematic; every color and dashed line is named in the
   caption.
6. After any change to the preamble or to a reference file: `compile_snippets.py` exits 0 (every recipe in
   every theme), and the renders of the changed recipes were looked at.
7. Say in one line what was not checked (for example: "compiled on pdflatex only; the
   serif theme was not rendered"; "the generator ran on synthetic data, not on the real
   field").

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a hand-laid architecture figure with overlapping parts | "overlaps, looks ugly, and does not show what the model is" | grid-aligned grammar, whitespace budgeted first, "delete and align" |
| slide styling: sentence titles, gray subtitles, shadows, pills, numbered badges, banners | (read as slides) | bare letters, titles of 4 words or fewer, flat blocks |
| a hand-drawn tree; a partition that did not match the code | "some random tree" | the partition and its tree generated by the real code |
| re-sampling points per zoom level | (a fake zoom) | one field, nested crops |
| flat region fills; a blurred mask | "political map", "smeared paint" | KDE with three nested bands |
| a globe graticule on a density domain | users "push back hard" | a few hairline ellipses at low opacity, or none |
| the serif house style forced on ML figures (indigo, Palatino, coral, teal) | (rejected for the author's figures) | the minimal 4-tone sans theme; serif as an option |
| taxonomic pastels per block type, a third or fourth hue | "only different tones of blue/grey and dead brown-mustard" | grays, blue ramp tints, one gold contrast |
| a graphical-abstract header with a gray sub-question and section numbers | "cut out grey text, it's unnecessary" | a title of 4 words or fewer, or none |
| "converged" shown on every frame | (a label before it is true) | the semantic-edge-frame check |
| vague arrows labeled "attention" | the mechanism must be obvious | the operation with labeled operands and one inset |
| a 12 pt rule for schematic text on a 3200 px canvas | superseded | three tiers at print size, 5 pt floor |
| a font that flipped between Helvetica and the TeX font | (a day lost) | decide once, record, keep |
| the figure body compiled alone | (a blank 12 x 12 pt PDF) | the safety check |
| `rand` without a seed | (the figure moved each compile) | `\pgfmathsetseed` and emitted coordinates |
| an old PNG mistaken for a fix | (a cached preview) | versioned PNG names |
| a plot library drawing the boxes of an architecture figure | "no python!! this is tikzzzzzzz" | vector TikZ built from the grammar |
| labels at 8 pt, ticks at 6 pt and panel letters at 12 pt beside data panels set in 7, 6 and 5 pt | (two type scales in one paper) | `\figL`, `\figM`, `\figS` and an 8 pt letter, as in every figure medium |
| shaded nuclei, three shaded blobs in one picture | (the theme allows one shaded density blob) | flat fills with a hard edge; one shaded blob per figure |
| panel titles whose baselines moved with their descenders | (found on inspection) | a fixed text height and depth in the title and note styles |

## Reference files

- `references/themes.md`: the two switches, every color by role and theme, color rules, line weights and text tiers, renamed tokens, adding a theme.
- `references/grammar.md`: the element table and compiled compositions (transformer, teacher-student, mechanism, scale spine, ego ball, tabular glyphs).
- `references/architectures.md`: pipeline, container, attention, U-Net, loops, routers, skips, radial callouts, operator pipeline.
- `references/plots_curves.md`: plots from record files, bands, scaling laws, bars, faceted rows, serif-look axes.
- `references/distributions_fields.md`: densities, landscapes, transport couplings, trajectories, fields, serif-look transport recipes.
- `references/graphs_geometry.md`: graphs, message passing, plates, Markov chains, equivariance, trees.
- `references/math_layout.md`: equations and annotations inside figures.
- `references/multiscale_density_zoom.md`: the zoom cascade rules behind `density_zoom.py`.
- `references/generators.md`: generating geometry from real code, seeds, emitting TikZ, `facts.json`.
- `references/animation.md`: frame decks, motion recipes, assembly commands, the design gates.
- `references/workflow_qa.md`: the loop, the smoke test, the safety checks, the failure catalog, the gate, a minimal TeX tree, the self-check.
- `references/bio_objects.md`: biology-tier glyphs and their figure-local fills.
- `scripts/compile_snippets.py`: compiles every recipe of the reference files in every theme; run it after any
  change to the preamble or to a reference file.
- `THIRD_PARTY.md`: what is credited as inspiration (no third-party code is included).

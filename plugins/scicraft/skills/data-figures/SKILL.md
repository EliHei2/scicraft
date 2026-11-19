---
name: data-figures
description: Builds publication data panels in matplotlib in one house style and composes them into figures at exact millimeters, for any venue (NeurIPS, ICLR, Nature, a book). Use it whenever a paper needs a plotted result, even when the user does not name the skill. Typical requests are "make the benchmark heatmap", "plot the ablation", "accuracy vs. inference time", "Elo/rank plot", "forest plot of the effects", "scaling curve", "learning curves", "fix this figure, it looks like AI", "fonts are wrong in the PDF", "the numbers don't match the table", "camera-ready is Friday". It ships a style module that works out of the box (true print size, 7/6/5 pt tiers, embedded TrueType fonts, role palette), a panel template, a composer, a QC script, the chart-form catalog with retired forms and their reasons, and the honest-encoding rules (IQR, bars from zero, shared scales, failure marks). For schematics use canvas-schematics or tikz-figures; for embedding maps embedding-maps; for statistics stats-reporting.
---

# data-figures

How to make the data panels of a paper so that the lead author signs them off without a round of corrections. This
was distilled from about a year of figure work on a benchmark paper, a foundation-model rebuttal and a book, where
roughly 40 figure cycles of 100 to 300 prompts each settled what the author accepts and what they throw out. Most
rules below are something they asked for more than once or something they rejected on sight. Where the author of the
paper at hand says otherwise, they win: record it in the panel map (section 9) and follow it.

> **PRIME DIRECTIVE: a figure is a result. Draw each panel at its printed size from frozen numbers with one script,
> in the house style, and do not hand it over before you have opened the rendered PNG yourself.**
> "If it can't regenerate from raw data with one command, it's an assertion, not a finding."

The failure to fear is the figure that "looks like a slide": gray subtitles, notes inside the plot, a legend inside
the axes, boxes and badges, a fourth font size, the own method drawn bigger. The author spots it in a second ("this
is not a slide, it's a paper figure!") and stops trusting the rest. Section 11 lists what was thrown out.

Three failures cost the most time. Guard against them from the first minute:

1. **Re-deriving a look that already exists.** When the author points at a reference figure, rerun its script and
   change only what was asked. Re-implementing it was "the #1 source of rework" (section 1).
2. **Scaling panels at assembly.** A panel drawn at one size and shrunk in the composer changes every font size and
   breaks the grid. Draw each panel at its box size from the mock-up (section 3).
3. **A number that disagrees with another place.** A value in a figure that differs from the master table or the
   caption "reads as an error". One metric implementation, one master table, an assert in the panel (section 7).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The venue and its text width** (`WIDTH_MM` in the style module: 89 and 183 mm for Nature, 139.7 mm for the
  ICLR and NeurIPS text, 82.5 and 171.5 mm for ICML, 165.1 mm for A4 with 2.2 cm margins), and the font of the host
  document (section 2).
- **The reference figures**: the two or three accepted figures of this paper or of the author's last one. They are
  the style source; the library's defaults never are. Open them before drawing anything.
- **The frozen numbers** behind every panel, the master table they come from, and the canonical run of each
  method. Ask "which version is this?" before computing anything.
- **Manuscript names**: the display name of every method, dataset and metric. Internal IDs never print.
- **The message of each panel in one sentence.** "What's the message of this supp figure in one sentence?" If
  nobody can say it, the panel is not ready to draw.

Then work in the figure repository layout the project uses. If there is none, use this one (the sibling skill
`project-structure` has the full contract):

```
code/figure_N/panel_<letter>_<name>.py    one public script per panel, at most about 150 lines
code/figure_N/_prep/                       aggregation, cached heavy steps, the figure's geometry module
data/figure_N/                             small frozen tables the panels read
figures/figure_N/panels/                   <name>.pdf .png .svg per panel
figures/figure_N/                          layout.json, the composed figure, caption.md
PANEL_MAP.md                               one row per panel: source, status, Synced flag, retired forms
```

## 1. Reproduce before you polish

- **Rerun the generator of a reference figure, then change only what was asked.** "find the latest proper figure
  and just copy-paste exactly as is ... then I will tell you what minimal changes to polish". Adapted copies drift
  (arrows became the words "high/low", icons faded).
- **Port with a minimal diff**: style import, data path, save path. No renames, helpers or clean-up. If the port
  looks different from the original, the diff was too large: revert and re-minimize.
- **Patch a shared renderer without editing it**: a thin wrapper that monkeypatches or string-replaces literals and
  `exec`s the source into a fresh module, parameterized by environment variables (`references/layout-and-compose.md`).
- **Make the smallest change asked and show the PNG every turn.** The author corrects in factors ("1.2x", "0.8x",
  "a tad" = about 1.1x). Apply exactly that factor to exactly the named elements and nothing else.
- **Version every layout** (`_v2`, `_v3`, or keep alternates in `figures/alt/`) so "go back to the previous one"
  costs a command. Retired files move to `_archive/`, never deleted.

## 2. The style module

Copy `assets/figstyle.py` into the project once and import it from every panel. No rcParams, hex colors or font
sizes anywhere else; about 30 scripts setting their own was the drift symptom that caused Type 3 fonts.

```python
import figstyle as S
S.apply()                                   # S.apply(font="cm-sans") for a LaTeX-default host
fig = S.fig_mm(89, 55)                      # the page will be exactly 89 x 55 mm
ax = S.axes_mm(fig, 12, 6, 70, 40)          # x, y from the TOP-left, w, h in mm
S.despine(ax)
S.save_panel(fig, "figures/fig1/panels", "b_ablation")    # .pdf + .png (600 dpi) + live-text .svg
```

What it fixes, each with the failure behind it (all numbers in `references/style-tokens.md`):

- **True printed size.** Panels are drawn at their final mm, so 5 pt prints as 5 pt. A render-scale fudge (14.6 pt
  labels on a big canvas, shrunk later) is the retired legacy route.
- **Three text tiers plus the letter: 7 pt titles, 6 pt axis labels, 5 pt ticks and annotations, 8 pt bold
  lowercase letters.** 5 pt is the floor. A subtitle is a lighter weight, never a fourth size. If text does not
  fit, give the panel more room before touching a font. `S.apply(scale=1.1)` scales all tiers together.
- **All text black (`#000000`), spines and ticks `#111111`.** Only a hero label may take its series color.
- **Despined axes**: no top or right spine, ticks outward, no grid. Compact panels: spine 0.5 pt, tick width
  0.4 pt, length 1.8 pt (`despine(ax)`); large panels 0.9, 0.9, 3.4 (`weight="large"`).
- **Fonts embedded as TrueType** (`pdf.fonttype 42`) and **SVG text kept live** (`svg.fonttype "none"`). Without
  it the PDFs carried Type 3 fonts and a co-author found "in illustrator, all the text is paths".
- **A registered font with a fallback chain**: Helvetica Neue, Helvetica, Arial, Liberation Sans, Nimbus Sans,
  DejaVu Sans. matplotlib silently falls back to DejaVu unless the macOS collection is registered, and indexes only
  the first face of a `.ttc`, so `fontweight="bold"` renders regular: use `S.bold_font(size)`.
- **Never `bbox_inches="tight"`.** The composer places panels at fixed mm and needs page size equal to figure size.
- **Transparent ground.** Panels and composed figures save with `transparent=True` (`save_panel` does it), which
  prints as white on the page. Never a dark ground in print: "don't do any black, always do transparent
  backgorund". Slide and web versions are recolored from the same source (the sibling skill `design-system`).
- **Role palette.** `HERO #0072B2`, `RIVAL #E69F00`, every other comparator `OTHER #A8A8AD`, `BASELINE #6E6E73`;
  hero variants share its hue (`HERO_ALT #0A3D66` diamond, `HERO_PRIOR #8DBEDD` open marker). `FAIL #D6321E` is the
  one saturated red and means only "did not complete". More series take Okabe-Ito hues.
- **Ramps.** `RANK5` single-hue blue for ranks (`#F1F6FF` to `#003FBD`, best darkest); `DIVERGING` blue to red
  through a wide white plateau for signed values; single-hue sweep ramps for ordered parameters.

**The font follows the host document.** Helvetica-family sans is the default. For a paper typeset in default
LaTeX, `S.apply(font="cm-sans")` matches `\sffamily` (the author rejected Helvetica twice for such a figure) and
`font="cm-serif"` matches a Computer Modern body; `font="serif"` takes Palatino-like faces for a serif host.
Computer Modern has no bold sans and maps the micro sign to a grave accent: write `$\mu$m`, and pass the composer a
bold face of the host with `--letter-font`. After any font switch, render every special glyph once and look.

## 3. Lay out before you draw

- **Mock up first.** Write `layout.json` (the one geometry source for panels and composer), then
  `python3 scripts/compose.py layout.json --mockup` draws one labeled box per panel on the real canvas. Settle
  rows, widths and aspect ratios there.
- **Regular mosaic.** Panels in a row share a height; a tall panel may span whole rows, but "never patchwork
  heights". Panels of the same kind get identical axes boxes; divide the row width evenly.
- **Align the plot areas, not the label boxes.** Match axes heights and centers across a row; center titles on the
  axes box. Keep the numbers in one geometry module that panels and composer both import.
- **Draw each panel at its box size.** "make the panels form the first place so that they have those bespoken
  proportions." The composer reports any panel whose PDF differs from its box by more than 0.2 mm.
- **Matched panels share one scale**, one y range and one color range. Two panels fitted each to its own box drew
  "b and c are different font sizes".
- **Dense panels get a full-width row.** "Dense panels fail by compression before they fail by colour." Split a
  row before you shrink it.

Details, the coupled-width formulas and the origin trap: `references/layout-and-compose.md`.

## 4. Choose the chart form

The data's shape picks the form; the figure's job picks the mix. The catalog with recipes and every retired form is
`references/chart-forms.md`. The forms in use:

| Claim | Form |
|---|---|
| who wins across many tasks or datasets | rank heatmap: `RANK5` steps, rank printed in every cell, mean rank and first places, groups bracketed |
| one score per method, with spread over units | thin vertical bars from 0, median with an IQR whisker, dashed reference from the hero bar |
| two competing scores | trade-off scatter: better corner top-right, faint dashed diagonal, same marker size for all, direct labels |
| effects of removing parts (ablation) | forest of paired differences with a zero line, or a signed heatmap with values printed |
| a rating with its uncertainty | Elo dot with its value printed, a thin rank-range box beside each row; the bootstrap IQR goes in the appendix table |
| cost against scale | resource lines on log axes snapped to decades, failures as a red x in a strip above, lines cut at failures; a run-time comparison between methods at one scale stays linear |
| a score over training | learning curves: straight segments between evaluated steps, a band across seeds |
| the per-unit distribution itself | solid IQR box, thin white median line, capped whiskers, no outlier points |
| rank of each method over many datasets | rank plot (`S.rank_plot`): methods by mean rank, deterministic jitter, a short mean tick |
| many curves of one kind (per seed, per pair) | thin faded lines behind a bold pointwise median |
| a null result | paired-change forest: shift per condition against a ±1 SD band of the reference, largest change printed |

- **One chart family per figure, few panels, values plotted rather than ranks** where values exist. A figure with
  six chart types reads like an analysis dump.
- **When asked for "nicer", polish the existing form.** Do not invent a new encoding.
- **Rebuild a weak panel in the grammar of the panel the author praised.** "the heat map one is super cool ... the
  ablation and the other figure are quite underwhelming ... just a line plot": the neighbors became matrix and
  sorted-bar panels. One result is shown in one panel only; keep the earlier design in `figures/alt/`.
- **Straight lines between measured points.** "it should be a line not a spline!!!" Never fit a model the points
  cannot carry: three points and a floored zero gave a fitted line that matched no point.
- **No log axis for a score whose differences matter.** It made one metric look "like [it] only gives 2 values".
  After any "no log" instruction, grep every script for `set_xscale|set_yscale|loglog|symlog|semilog` and convert each hit.

## 5. Draw it honestly

Emphasis is allowed only where the values are printed or plotted to scale. Full rules: `references/honest-encoding.md`.

- **Spread of units is an IQR**: median with the 25th to 75th percentile of per-unit values (per seed, fold,
  dataset). "please don't do CI, do IQR, you know the deal!" Never pair a mean with an IQR whisker (a skewed mean
  sits outside it; `tradeoff_scatter` refuses). Figures carry the adjusted p by default. A 95% CI is drawn only
  where the size of an estimate is the claim (a forest of paired losses) or a reviewer asked, labeled as a CI; a
  rating panel shows no interval and its bootstrap IQR goes to the appendix table. Never relabel one as the other.
- **Bars start at 0 on a linear axis and the axis line starts and ends on a tick** (`method_bars` does both and
  refuses a last tick below the tallest whisker). A narrow fraction band may be zoomed only with the reference line
  drawn and the range stated.
- **The same marker size and line width for every compared method.** "let the results speak." The hero is told
  apart by color, by being drawn last and by a bold label in its color; a thin dashed line at its value lets
  readers compare.
- **Only completed full runs are drawn.** A run on a subset counts as not run. A failure gets a method-colored dot
  struck by a red x with the cap in the key ("out of memory (<cap>, OOM) or out of time (<limit>, OOT)"); a value never
  recorded is a gap in the line, because "a bare dot up there would read as a datum".
- **Every method has the same points.** If one value is unrecoverable, drop that dataset for every method and say
  so; the deliverable for a missing number is a fetch list, not a new glyph ("don't make it weird"). A value that
  cannot exist (a heatmap cell, an impossible run) takes the figure's one `MISSING` hatch, defined in the key.
- **Color never carries meaning alone and every color is in a key.** One canonical color per category label
  across the whole paper; categorical systems for metadata never share hues with the method palette.
- **Heatmap color mode is a deliberate choice, kept across the paper**: `rank` steps, per-column `minmax`, or
  per-column rank against a reference. Color may be shaped (white plateau, min-max anchoring) only with the
  values printed in the cells.

## 6. Label, title, legend

Details and the label-placement recipes: `references/labels-and-legends.md`.

- **No prose on the figure and no gray type.** Notes, n, filters and caveats go to the caption. "a figure that
  argues with itself in 6 pt gray is a figure nobody reads."
- **Titles are one short line naming the quantity**, or nothing: "if you have informative y label you don't need a
  title." Names are manuscript names; no internal IDs, run names, hardware or tool names ("no one knows about your
  internals").
- **Units compact, in the label**: `No. samples (M)` with ticks 50/100/200, `×10³` in the label, not on each tick.
  Show the better direction with `S.label_dir(ax, "score", "up")`: an up arrow typed into a rotated y label points
  left on the page, so the helper writes the arrow in the label's reading direction. Look at it in the render.
- **Label marks directly; a legend only when a series recurs.** Small scatters use `compass_place` (fixed 4.5 pt
  gap, no leaders, deterministic; markers, error bars, placed labels and the axes frame are obstacles); dense clouds
  use `repel_labels` (adjustText recipe). Verify at 2 to 3x zoom.
- **A recurring series is named once, in a shared legend outside every plot** (`S.legend_mm`): circle markers,
  below or right of the panels it keys, left-aligned, no wider than them. Six inline names in each of ten 21 mm
  boxes forced 5 pt type and collisions.
- **Check glyph coverage before using a symbol**, and guard `pd.isna` so an empty cell never prints "nan".

## 7. Numbers that match

- **One metric implementation, imported everywhere; one master table; figures read from it.** Before sharing,
  diff every number in captions, text and supplementary panels against it. The supplement marks the main figure's
  default with a dashed line.
- **Assert the claim on the data you draw**, in the panel: a rank column is a permutation of 1..N at every level,
  the adjusted p is below .05 when the label says significant, every method has n units. Numbers in captions are
  generated from the frozen data or asserted against it at build time (the sibling skill `paper-code-parity`).
- **Treat a surprising result as a bug until shown otherwise**: proportions that do not sum to 1, two analyses with
  identical numbers, a mirrored pattern, a value outside its range.
- **Never publish a statistic computed on partial data.** Scripts draw only datasets complete for every method;
  print the n behind every correlation.

## 8. Compose

```bash
python3 scripts/compose.py figures/fig2/layout.json              # fig.pdf, fig.png (600 dpi), fig.svg (live text)
python3 scripts/compose.py figures/fig2/layout.json --mockup     # boxes only
```

- Panels are placed at native size from their vector PDFs (`keep_proportion`, never stretched, never rasterized).
- **Letters are stamped last** so an opaque panel never paints over them: bold lowercase, one size per paper, on the
  baseline of the panel titles (letter at x + 0.3 mm, title at x + 3.8 mm, both 4.2 mm below the panel top).
- Captions live in `caption.md`; the composer draws only letters.
- Every edit ships PDF and PNG in place; the live-text SVG is regenerated with every edit once a submission set exists (see `figure-development`). Name files
  after their manuscript figure number. Back up outputs before re-composing on a full disk.

## 9. Record

- `PANEL_MAP.md`: one row per panel with its source script, upstream reference, status (`draft`/`final`) and a
  `Synced` flag. Fold lessons into shared guidelines or this skill only in a batch when the author says "update
  docs", never per panel.
- Record every retired form in the panel map with its reason, so no later agent brings it back.
- Keep a table of the plotted values next to each figure for co-authors.

## 10. Check before anything is handed over

In this order (`references/visual-qc.md` has the full list and the review loop):

1. Rerun every panel script and the composer from a clean shell. Read the warnings.
2. `python3 scripts/check_panel.py figures/fig2/panels/*.pdf --figure figures/fig2/fig2.pdf --figure-width 183 --ban banned.txt`:
   the figure's page size (panels keep their own sizes), embedded TrueType fonts (no Type 3, no DejaVu fallback), the 5 pt floor, at most 3 text sizes
   besides letters (4 warns), no gray text, nothing off the page, no overlapping horizontal text, no banned word.
3. `pdffonts figure.pdf`: every font `emb yes`.
4. **Open the composed PNG and look**, then render crops at 900 to 1200 dpi of every dense region: no clipped
   tick, label or letter; no label on a dot or whisker; direction arrows point the right way on the page; letters
   visible but not dominant; rows aligned; legends
   outside; every color in a key; no wasted white space; rank and color direction match the metric direction.
5. Compare against the reference figures side by side. "just give me output if you can convince yourself that
   this figure is better than the original I gave you."
6. Diff every printed number against the master table.
7. Say what was not checked: labels on rotated text, color-blind safety of any color outside the shipped palette,
   whether the SVG opens correctly in the co-author's editor.

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| gray subtitles, notes and n inside the plot | "this is not a slide, it's a paper figure! no long text" | black text, everything else in the caption |
| a legend inside the axes | "legend never inside plot!!" | a shared legend outside, or direct labels |
| boxes, cards, badges on a data figure | "don't use that stuff on it the boxes" | bare panels on white |
| a fourth or fifth font size | "maximum 4 levels of font size. 3 even better." | 7/6/5 pt tiers |
| panels rescaled in the composer | "do not rescale panels only for the main figure" | each panel drawn at its box size |
| a reference plot re-implemented | "just copy-paste exactly as is" | its own script rerun, then a minimal diff |
| 95% and 99% CI whiskers for spread | "CI is too long!", "please don't do CI, do IQR" | median with the 25th to 75th percentile |
| the own method drawn bigger or thicker | "don't make [our] point bigger!", "let the results speak" | same size; color, z-order, bold label |
| splines through measured points | "it should be a line not a spline!!!" | straight segments |
| a fitted trend through three points | the fit "floated free of every plotted point" | the measured points joined |
| dense dot plots | "it's not obvious what they say" | volcano panels or heatmaps with values |
| a new "meaningful" heatmap for a working plot | "no meaning and so much text" | the existing form, polished |
| beeswarms and big median blobs | "small lines instead of big blob for the median" | light jitter and a short median tick |
| dotted reference lines | "hyphened lines not dotted" | thin dashed lines |
| horizontal bar plots | "no horizontal one please!!" | thin vertical bars |
| log axis on a score | it "looks like [it] only gives 2 values" | linear axis with a scale factor |
| hollow "not recorded" marks and a taller strip | "don't make it weird" | the old layout and a fetch list |
| estimates and subset runs drawn as points | "otherwise that's a non-ran" | full runs only; red x for failures |
| a filled radar with per-axis scaling | "drop the fill" | a rank radar on one scale, no fill |
| a 2D good-corner summary | it crowned a degenerate method | per-dataset bars |
| inline names on every curve of ten panels | rejected on sight | one shared legend |
| Type 3 fonts and outlined SVG text | "in illustrator, all the text is paths" | `pdf.fonttype 42`, live-text SVG |
| `bbox_inches="tight"` | composed panels landed in the wrong place | page size equal to figure size |
| matplotlib concept schematics | "this is so bad" | data panels only; schematics in canvas-schematics |
| hollow boxes and CI whiskers on box plots | "make them solid with white line as median", "do normal boxplots please iqr + median" | solid IQR box, white median line |
| a CI line on every Elo rating | "CI is ugly and not uniform with p-value" | the rating dot with its value; bootstrap IQR in the appendix |
| per-fold boxes marked "ns" for a null result | "a weak vis" | paired-change forest against a ±1 SD band |
| a lollipop stem from the axis origin | the stem reads as the value when the axis does not start at 0 | a dot, or a filled matrix cell |

## Reference files

- `references/style-tokens.md`: every size, line width, color, ramp and font setting, and the host-font switch.
- `references/chart-forms.md`: the forms in use with recipes and numbers (also box plots, composition bars,
  per-item curves, tile grids, null results), and the retired forms with reasons. Read it before drawing any form.
- `references/honest-encoding.md`: spread, axes, shared scales, failures, emphasis, the integrity line.
- `references/labels-and-legends.md`: titles, names, units, the two label placers, legends, glyph coverage.
- `references/layout-and-compose.md`: mock-up, geometry module, grid alignment, the composer, the wrapper pattern.
- `references/visual-qc.md`: the scripted gates, the look list, the adversarial review loop, render parity.

Scripts and assets (Python 3.9 or later, matplotlib, numpy, PyMuPDF; fontTools and adjustText optional):

- `assets/figstyle.py`: the style module (apply, mm geometry, palette roles, ramps, tick ladder, labels, bars, scatter,
  rank plot, transparent save). `python3 figstyle.py` runs its self-test.
- `assets/panel_template.py`: a working panel script (ablation bars, median and IQR over seeds) with [bracketed]
  places to edit.
- `scripts/compose.py`: layout JSON to composed PDF, PNG and live-text SVG, or a mock-up.
- `scripts/check_panel.py`: the scripted QC gate for panel and figure PDFs.
- `scripts/demo_panels.py`: three demo panels (rank heatmap, trade-off scatter, rank plot) from seeded synthetic
  numbers and their layout; run it once to see the house style.

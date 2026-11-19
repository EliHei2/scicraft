# Figures in a report

Report figures are paper figures. Panel making, palettes and the plotting library belong to `data-figures`; this
file sets what a report adds.

## 1. Style

- Open the manuscript's latest accepted figures before drawing anything, and import the paper's own style module
  and plotting helpers. Copy the numbers they use (bar width in mm, panel height, three text sizes, tick count).
  In the source report: 2.7 mm per bar, 23.4 mm panel height, text at 7, 6 and 5 pt, legends at 6 pt, three ticks
  per axis.
- One script per panel, each importing one shared config that fixes the run, the parameter setting and the colors.
  A figure audit found the "same" method was a different run in different panels; one config module fixed it.
- Colors carry identity only where identity is the encoding. In the source report: the own method a circle,
  competitors diamonds; metric names in ink when methods are compared; when metrics are the compared items, each
  metric family takes its own color and the y label matches. Diagnostics in light gray (`#B4BBC4`).
- **The metric-defense case.** When the report defends a metric and the panels compare metrics, the defended metric
  and its variants take the hero color, the rival metric family the rival color, every other metric gray
  (`#8E8E93`). The y label takes its family's color, so a panel with no title still says which family it shows. The
  axis line, ticks and every other piece of text stay ink. This was asked for three times in one defense report
  ("the main metric and its variants in the hero blue, the competitor's family in the competitor green"). The color
  tokens are in the sibling skill, `data-figures/references/style-tokens.md`.
- A glyph the font lacks (an up or down arrow) is drawn with mathtext (`$\downarrow$`).

## 2. True size

The builder sizes each raster figure at its physical width: width in px divided by the dpi stored in the file,
times 25.4, in mm. CSS turns mm into screen and print size with one variable: `--mm: 4.95px` on screen and
`--mm: 0.96mm` in print. So a 60 mm panel prints at 57.6 mm on A4 and every figure shares one scale.

- Save every PNG with its dpi (`savefig(..., dpi=400)` stores it). A PNG without dpi is sized at `--default-dpi`
  (400) and the builder warns.
- Size panels for the report at the paper's widths (89 mm single column, 183 mm double).
- `--no-true-size` turns this off for screenshots and photos.

## 3. Numbering

- Main figures R1, R2 ... in the order they are first cited; supplementary S1, S2 ... in their own section after
  the main text. The prefixes keep report figures apart from the paper's figure numbers.
- About 10 main figures. "keep the top 10 most striking one". The rest go to the supplement with a one-line
  pointer where they left.
- `check_report.py` fails when captions are out of order or a cited figure does not exist, and warns when a main
  figure is never cited.
- After moving figures, read the label order page by page in the PDF.

## 4. Captions

In this order, in full sentences:

1. **Bold first sentence: "Figure R3. <the claim the figure shows>."**
2. What is on each axis and in what unit.
3. What each mark, line and color is (or "legend at right").
4. n, the statistic, and its spread: median with 25th to 75th percentile (IQR), never a confidence interval.
5. Which run and which settings, and any filter or subset applied. A reader's question once exposed that a
   caption did not say an analysis was limited to a subset.
6. Where the provenance matters: "our implementation of the recipe in paper X" or "the authors' package, run as
   coded".

## 5. Axes and plot types

| Situation | Rule | What went wrong without it |
|---|---|---|
| naming the quantity | on the y axis, no panel title; the y label in its family's color when metrics are compared | "name it on the y not on the title" |
| a score whose differences matter | linear axis with a factor (x 10^-5) | on log10 a metric looked two-valued |
| run time or memory between methods at one scale | linear | "to see real diffs" |
| a scaling curve over decades of input size | log axes snapped to decades | the row is owned by the sibling skill `data-figures` (its chart table); repeated here so the two cases are not confused |
| same quantity under two conditions | square box, identical limits and ticks, x = y line drawn | the bisector was not obvious |
| two different metrics against each other | each axis fit to its own data | shared ranges "make the vis weird" |
| a rank plot | at every x, ranks 1 to N each held by exactly one item; assert it in the script | overlaid experiments left empty and doubled ranks |
| a head-to-head claim | one x-y scatter of A's score against B's on the same items | bar panels left the claim "vague" |
| robustness | ranks across score versions on the real outputs | rank changes under injected error were rejected |

After any "no log" instruction, grep every figure script for `set_xscale|set_yscale|loglog|symlog|semilog` and fix
every hit; one appendix panel was missed the first time.

## 6. Figure QC

- Render, open the PNG, fix collisions, render again.
- Tile changed panels into one contact sheet and look at it.
- Scan each PNG for ink touching its edges (a clipped label).
- Measure text boxes for overlap when labels change (matplotlib `get_window_extent` on every text artist).
- Check the input files of any figure an agent made (row counts, which datasets and methods): one agent left mock
  renders at a real output path.

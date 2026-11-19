# Chart forms

The forms the author uses now, each with the recipe that made it pass, and the forms they retired, each with its
reason. One renderer per form per paper: two bar implementations in one figure family drifted until they no longer
"read 1:1".

Three rules hold for every form:

- **Redesign a weak panel in the grammar of the panel the author already likes.** When one figure was praised ("the
  heat map one is super cool") and its neighbors were called "quite underwhelming ... just a line plot", the
  neighbors were rebuilt as a heat matrix and a sorted-bar panel. Never show one result in two panels: a two-panel
  ablation figure whose panels repeated each other ("a and b are redundant") became one matrix plus one bar panel.
  When the figure carries every value of a table, drop the table and point to the figure. Keep the earlier design
  in `figures/alt/`.
- **One method keeps one color in every panel of a figure.** "if you color on one side then color other side": a
  method colored in one panel and gray in its neighbor reads as two methods.
- **Highlight the comparators that carry the story, never the baseline.** One color per highlighted comparator, its
  name in the same color, every other method in light gray (`OTHER`). A highlight on a raw-input baseline was
  removed because it drew the eye to the baseline sitting at rank 2.

## Contents

1. Rank heatmap (benchmark matrix)
2. Signed heatmap (ablation table, effect sizes)
3. Method bars
4. Trade-off scatter, and a grid of trade-off tiles
5. Head-to-head scatter
6. Rank plot and rank radar
7. Elo or rating plot with rank range
8. Forest plot, and paired differences across many conditions
9. Null result
10. Resource and scaling curves
11. Learning curves
12. Volcano grid
13. Box plots
14. Composition bars
15. Many per-item curves
16. Diverging bar for a signed quantity
17. Density contours
18. Pairwise lower-triangle heatmap
19. Retired forms

## 1. Rank heatmap

The answer to "who wins across many tasks". Worked example: `scripts/demo_panels.py`, function `heatmap`.

- Draw on `S.canvas_mm(fig)`: one axes over the whole figure in mm with y down, cells drawn as rectangles. Fixed
  mm cells keep rows aligned with neighboring panels.
- Cells about 6 mm wide and 2.9 mm tall carry a 5 pt rank. Fill with `S.rank_color(rank)`: 1, 2, 3, 4 to 7, 8 and
  worse map to the five `RANK5` steps (ties take the next whole place). White text on the darkest step only.
- Print the value in every cell. A cell that cannot exist takes the figure's one `MISSING` hatch, defined in the
  key; the demo prints `n/a` on `BAND`, which serves as that one glyph when no hatch is used. One missing glyph per
  figure: "do not mix NA, blanks, and hatches in one figure".
- Summary columns after a 1 mm gap: mean rank (two decimals), first places, top-3 places.
- Bracket task groups above the column heads (0.35 pt lines with 1.1 mm end caps, label in a gap). Keep a title
  plus bracket within one text-tier band, at most 4 mm: it creeps tall fast.
- Group rows by what methods are (for example by pretraining type) with a thin `GUIDE` rule and a rotated 5 pt label;
  sort within groups by mean rank. The hero row is bold in the hero color.
- Put a short head over the row-label column that says what the rows are (methods, interventions, datasets). A
  heatmap with unnamed rows drew "the rows have no annotation, is it the intervention? ... make it clear".
- Start the row labels at the panel's left edge and size the label column to the longest label (measure it with
  the renderer, as `demo_panels.py` does), so no white band opens left of the labels; one heatmap was sent back for
  "so much white space on left".
- Keep the gap between a row label and its first cell the same constant in every figure of the paper; measure it
  in mm on the render.
- Rotated column heads that rise above the title band get a fixed abbreviation map in the panel script, and the
  caption spells each abbreviation out.
- Dataset or platform icons go in a row under the matrix at full opacity; faded icons were rejected. The reference
  method's own column prints `ref.` instead of a dash, because a dash read as a missing value.
- Rank a column only where at least two methods were measured. Assert that ranks at each column are a permutation
  of 1..N before drawing.
- Metric direction goes in the title with an arrow (`S.ARROW_UP`); the color direction must match it.

## 2. Signed heatmap

Effect of each intervention against the full model, per task.

- Rows are interventions named concretely in at most 4 words, written "−X", not "w/o X". Columns are task names,
  never task codes. The full model is the reference row, last and uncolored.
- Color is size and direction, scaled per column to its largest absolute shift, symmetric around zero; the caption
  says "colour is size and direction". Significance is a star after the value, never bold alone.
- Use `DIVERGING` with values printed. A green to red version was used for one ML rebuttal table; it is not safe
  for red-green color blindness, so use it only on request and only with values printed.
- A long tail of low-ranked rows may collapse into one gray "N other methods" row (it removed 28% empty area in one
  table).

## 3. Method bars

One score per method with its spread. `S.method_bars`; working example `assets/panel_template.py`.

- Thin vertical bars, about a third of the slot, no border, lightened series color, hero first. "use the white
  space ... thinner bars".
- Bars start at 0; the y axis carries 3 to 4 ticks and its line starts and ends on a tick; no x axis line and no x
  ticks; names label the bars, tilted (about 30°) when crowded, the same tilt across sibling panels. Abbreviate the
  one long label rather than change orientation.
- Whisker: 25th to 75th percentile of per-unit values; the bar is the median. Never a mean bar with an IQR whisker.
- A dashed reference line starts at the hero bar and runs across the others at the hero's value.
- No numbers on bars when the axis has ticks (the latest of several reversals); a panel read by its exact values
  prints them at the bar ends and drops the tick labels instead, never both. Numbers stay on stacked composition
  bars, with percentages.
- Pick the y tick step from {1, 2, 2.5, 5} x 10^k so that 3 to 4 ticks cover the data: `S.nice_axis(0, top)`
  returns those ticks, ready for `method_bars(yticks=...)`. A hard-coded step ladder that stopped at 500 drew an
  axis of 0 to 10,000 for a bar of about 1,700.
- In a benchmark without an own method, order methods by the plotted statistic, best first, and keep that order in
  every sibling panel. A difference that matters gets its own difference panel; the bar axis still starts at 0.
- Log bars only for values spanning decades: range from positive values only, power-of-ten ticks
  (`S.log_decades`), no error bars, and the bar top must equal the value (a baseline offset once made log bars too
  tall so the hero reference sat below the bar top).
- A few methods with one score each were once drawn as horizontal bars with the hero on top, value at the bar end
  and a bracket from hero to rival with the effect ("+41%, p<..."). The author later asked for vertical bars every
  time ("no horizontal one please!!"); use vertical unless told otherwise.

## 4. Trade-off scatter, and a grid of trade-off tiles

Two competing scores, one point per method. `S.tradeoff_scatter`; worked example `demo_panels.py`, function `scatter`.

- Flip an axis so the better corner is top-right (less error = up). A faint dashed diagonal toward that corner;
  "better" arrows go inside the axis labels ("← FPR", "↑ TPR"), never as a free arrow on the plot.
- Every method at the same marker size. The hero is drawn last, its label bold in its color. Statistics such as ρ
  go to the caption.
- Error bars are IQR deltas; the limits include them so no whisker is cut.
- Labels: `label="compass"` (default; each label's nearest edge 4.5 pt from its point, no leaders; markers,
  whiskers, labels and the axes frame are obstacles). Give the panel room first: eight labeled points did not fit
  a 34 mm axes and needed 44 mm, then more headroom (`pad_frac=0.16`) once the axes was cut to 23 mm to sit on the
  neighboring heatmap's grid lines.
- Direction marks on rotated labels through `S.label_dir` (see `labels-and-legends.md`).
- A parameter sweep of the own method: points in a single-hue ramp joined by a straight line, the default marked
  and labeled "0.05 (default)" with a discrete legend.
- Identical x and y ranges and ticks only when x = y means something (one quantity under two conditions): square
  axes, drawn x = y line, an inset for the cluster at the origin. For metric against metric, each axis fits its data.
- **A grid of trade-off tiles** (one dataset per tile) keeps identical axes grammar in every tile, a star at each
  default, and sweep or dose arms as ordered points joined by straight lines. Place labels only after the axis
  limits are final: a label repel that ran before the limits widened left labels away from their points. When arm
  end points crowd one corner, name the arms in a legend block.

## 5. Head-to-head scatter

When the claim is "A beats B on the same items", plot A's score against B's per item. Clean items as open
circles, a band for B's range on clean items. For A against every other method, one panel per competitor with
point-and-line trajectories and Spearman ρ in each panel's emptiest corner.

## 6. Rank plot and rank radar

- Rank plot: `S.rank_plot(ax, ranks, methods)` (worked example `demo_panels.py`, function `rank_panel`). Methods on
  x sorted by mean rank (best left), y = rank with 1 at the top, small per-dataset dots with deterministic
  index-based jitter (reruns are identical), and a short horizontal tick at the mean rank. The ported renderer first
  used a big mean marker; its last version drew the short tick, in line with "small lines instead of big blob for
  the median". Every method gets the same dot size and tick width. The helper asserts that every dataset ranks
  every method exactly once (ties share the average place).
- Lines of rank across ordered conditions (scales, datasets): one experiment per panel; ranks 1..N each held once at
  every x. Overlaying lines from separate experiments left empty and doubled ranks. Assert it before saving:

  ```python
  for x, g in df.groupby("level"):
      assert sorted(g["rank"]) == list(range(1, len(g) + 1)), x
  ```

  A failed assert means separate experiments share an axis or ties were not broken.
- Rank radar: every axis on one scale (`RANK_SCALE_N`), so each vertex lands on its tick; a per-axis normalization
  drew a mean rank of 2.00 at r = 0.667 against a "2" tick at 0.750. No fill, thin equal lines, faint spokes, labels
  at about 1.15 times the radius. It is a closing gestalt, not a precise read.

## 7. Elo or rating plot with rank range

- Rows sorted by rating, one row order shared with the rank box beside it. Dot at the rating, the value printed in
  a right gutter, no interval line; the bootstrap IQR of each rating is printed in the appendix table and the
  caption points there. The axis states its anchor ("Elo (baseline = 1500)").
- Beside each row, a thin box of its rank over tasks: whiskers to the full range, box from the 25th to 75th
  percentile, white median tick, the range printed ("2 to 5"). This replaced a wide separate rank plot.
- A rating below the axis floor gets a small arrow at the floor, not a clipped mark.
- Row labels at `va="center_baseline"`: `center` placed them 0.14 to 0.18 mm above their rows.

## 8. Forest plot, and paired differences across many conditions

- Label gutter on the left (about 39 mm in a 71 mm panel), plot 30 mm wide, rows 1.85 to 2.15 mm apart.
- Point and its paired 95% CI over folds, a zero line, x ticks such as −.12 −.08 −.04 0 in the house number style,
  axis label "change in score when removed (95% CI over folds)".
- Assert on each row what the panel claims (the interval excludes zero, the estimate is negative, the row carries
  the claim label) before drawing it.
- One message: rows that need a different reading were dropped ("the panel shows one thing").
- The CI stays here because the size of a loss is the claim. This is the documented exception to the no-CI display
  default (the sibling skill `stats-reporting`, `stats-reporting/references/spread-and-intervals.md`).
- **Paired differences across many conditions**: one row per condition, the difference (method under test minus
  each competitor) with a block-bootstrap 95% CI, one color per competitor, a filled marker and an asterisk only
  where the CI excludes 0, open markers for ties, "n/a" for an unmeasured condition, and excluded strata in gray
  below a divider with the reason. The effect is shown by position only: per-method values printed again in three
  panels were removed as repetition. The sibling `stats-reporting/scripts/paired_tests.py` computes the shifts and
  intervals.

## 9. Null result

A null result is drawn as a paired-change forest: one dot per condition at the paired shift, a gray band of ±1 SD
of the reference's per-unit scores, one axis span shared by all panels, the largest change printed, the test and
smallest adjusted p in the caption.

- The dot is the paired shift of each perturbed run against the reference (a Hodges-Lehmann estimate in the source)
  over folds or seeds; the band is ±1 SD of the reference's per-fold scores, so the reader sees the change against
  natural variation.
- Give every panel the same span in SD units (±1.3 SD in the source), so one yardstick holds across tasks, and print
  the largest absolute shift per task as a percentage of that SD.
- No interval bars ("CI is ugly and not uniform with p-value"). At least 3 evenly spaced ticks per axis.
- An identity scatter was rejected because its weakest panel read as a failure. A task with too few folds to
  estimate the SD (4 in the source) was left out, and the caption says why.
- Give the panel script a self-test mode that draws the layout on synthetic per-fold scores (an environment switch
  or the template's demo records), so tick spacing and label overlap are checked before the real records arrive.

Per-fold "ns" boxes were replaced by this form (see the sibling `stats-reporting` skill).

## 10. Resource and scaling curves

- Log axes snapped to the bounding decades (`S.log_decades`) for a curve over decades of input size; units in the
  label (`No. samples (M)`), ticks 50/100/200. A run-time or memory comparison between methods at one scale stays
  linear "to see real diffs".
- The caption names the hardware each tool ran on and the kind of memory plotted. Label the axis "peak VRAM (GB)"
  or "peak RAM (GB)": an axis that mixed the two drew "do it VRAM or RAM not GPU and RAM".
- Take run time and memory from each tool's own run records or the scheduler logs, and recover missing ones from
  the cluster before drawing.
- Draw only full runs. Failures sit in a strip above the axes: one row per failing method, a method-colored dot
  struck by a red x (`FAIL`), nudged apart along x when two datasets are closer than 0.06 decades, with a hairline
  back to the true x. The key gives the caps verbatim, for example "out of memory (<cap>, OOM) or out of time
  (<limit>, OOT)".
- Lines are piecewise: consecutive points are joined only when no failure lies between them.
- A value that finished but was never recorded has no mark: a gap.
- Durations come from the scheduler's run time, never from clock strings without a date (day-long runs wrapped and
  came out exactly 24 h and 48 h short).
- A dataset with exactly 1,000,000 rows was a truncation; check row counts against the source.

## 11. Learning curves

Suggested, not yet tested in real work as a full recipe; each part comes from a rule that was tested elsewhere.

- Straight segments between the evaluated steps; no smoothing, no spline (section 4 of SKILL.md).
- Spread across seeds as a band from the 25th to the 75th percentile per step (`BAND`-style light fill of the
  series color), the median as the line. With fewer than 3 seeds, draw each seed as a thin line instead.
- Same line width for every compared run; the hero by color and z-order.
- Compare runs only at matched steps or matched data seen, and say which in the axis label.
- A run that diverged or was stopped keeps its line up to its last evaluated step and is reported in the caption;
  it is never dropped from the plot or the statistics.

## 12. Volcano grid

Replaced dense marker dot plots. Point size is the % of units expressing (100 − % for negatives), threshold lines
annotated with their values (p = 0.01, |log2FC| = 1 unless told otherwise), every selected item labeled with
`S.repel_labels`, adjusted p labels outside on the right, fold-change axis trimmed so outliers do not set it, and
1.2 times headroom above capped clusters so labels have a free band.

## 13. Box plots

Use a box only when the per-unit distribution is the claim; otherwise draw method bars.

- A solid box from the 25th to the 75th percentile in the series color, a thin white line at the median, whiskers
  with short end caps. No outlier points unless the caption discusses them.
- Every method gets the same box width and line weight. The caption says what the whiskers span.
- Hollow boxes were rejected ("make them solid with white line as median"), and so were CI whiskers ("do normal
  boxplots please iqr + median").

## 14. Composition bars

- Stacked bars for a composition are thin and vertical, with no x or y axis line.
- Label segments in black with their percentage; where a segment is too small, use a bracket or a short leader to a
  label outside.
- Legend entries follow the stack from top to bottom.

## 15. Many per-item curves

Per pair, per seed or per class, when the spread of curves is the point.

- Each item is a thin faded line (about 0.35 pt, alpha about 0.11) behind a bold pointwise median; the summary
  marker sits at the median. A smoothed mode collapsed three methods to one value and was replaced by the median.
- When two roles share a panel, color carries the class and line style carries the role: the focus series solid at
  about 1.35 pt, the de-emphasized series dashed at 0.8 pt with alpha 0.75. The same widths hold for every method.
- No minor ticks. In ML this is per-seed learning curves faded behind their median.

## 16. Diverging bar for a signed quantity

- Center the axis on the zero that has a physical meaning (a boundary, no change). The inside or negative side
  carries a faint shade, and each group shows its median with the IQR.
- An opaque derived fraction ("absorbed") was rejected in favor of the median signed distance.

## 17. Density contours

Draw a 2-D density as filled contours with no contour lines, 3 to 4 levels at most, darkest at the core. More levels
or outlined bands turned the panel into noise.

## 18. Pairwise lower-triangle heatmap

A symmetric pairwise statistic (attraction against avoidance between categories, correlation between metrics) shows
only the lower triangle with the diagonal. The upper half repeats the same numbers. A signed statistic takes
`DIVERGING` centered at its null value, with values printed.

## 19. Retired forms

| Form | Reason | Replacement |
|---|---|---|
| box or violin confidence rows | did not carry the claim; recorded as "do not re-add" | bars plus embeddings |
| dense marker dot plots | "it's not obvious what they say" | volcano grid |
| 2D good-corner summary of all methods | crowned a degenerate method | per-dataset bars |
| filled radar, per-axis scaling, magenta hero | values off their ticks; fill weights methods unequally | rank radar on one scale |
| rank dot-plot strips in a dense layout | dropped "for large, readable panels" | large panels |
| runs of near-identical rank-flow bump charts | added nothing over values | value plots; a rank flow only where the rank is the readout |
| beeswarm, big median blobs | "small lines instead of big blob for the median" | light jitter and a short median tick |
| continuous legend for a discrete sweep | "make it normal" | discrete legend, default starred |
| flipped y axis on a non-rank plot | "do not flip the y!" | natural orientation |
| background grid | "drop the background grid" | none, or a faint guide on bars |
| stars on the best bar | removed on request | the values speak |
| a pooled module column beside single features | apples beside oranges | per-feature panel, module claim in the text |
| a heatmap of rank stability | "no meaning and so much text" | the original rank flow |
| one multi-panel matplotlib figure (`subplots`) | panels could not be sized or moved apart | one script per panel and the composer |
| per-fold boxes marked "ns" for a null result | "a weak vis" | paired-change forest against a ±1 SD band (section 9) |
| a CI line on a rating | "CI is ugly and not uniform with p-value" | the rating dot with its value; bootstrap IQR in the appendix |
| lollipop stems from the axis origin | the stem length reads as the value even when the axis does not start at 0 | dots or filled matrix cells |
| a Z or p strip beside a main figure | test statistics are not a result a reader can read | an asterisk after the value, the exact adjusted p in the appendix table |
| a line plot of an ablation or sweep with no order worth reading | "quite underwhelming ... just a line plot" | a heat matrix with values in the cells |
| a big white-edged mean marker on a rank plot | "small lines instead of big blob for the median" | a short mean tick |

Record a retirement in the panel map with its reason in the same edit, so no agent brings it back.

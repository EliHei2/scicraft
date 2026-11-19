# Honest encoding

Choosing what a figure leads with is presentation. Changing what the records support is misreporting. This file
holds the rules that keep a data figure on the right side of that line, with the failure behind each. The sibling
skills `stats-reporting` (tests, thresholds) and `integrity-audit` (checking a whole paper) go further.

## Spread and uncertainty

- **Spread of units: median and IQR.** The bar or point is the median; the whisker runs from the 25th to the 75th
  percentile of per-unit values (per seed, fold, dataset, item). An IQR shows how units spread; a CI of the mean
  shrinks with n and hides the spread. The author asked for 99% CIs, found them "too long", and settled on the IQR;
  three months later the author had to repeat it. The caption says "Error bars, 25th to 75th percentile".
- **Never pair a mean with an IQR whisker**: a skewed mean sits outside its IQR. `S.tradeoff_scatter` raises an error
  when a point lies outside its interval. If only a mean and a CI are stored, draw no whisker and say so, or
  recompute from per-unit data. Never relabel a CI as an IQR.
- **Display default: the adjusted p and the IQR.** A 95% CI is drawn only where the size of an estimate is the
  claim (a paired difference over folds in a forest plot) or where a reviewer asked something a p value does not
  settle; write "95% CI over folds" on the axis or in the caption. A rating fitted on all data shows no interval on
  the figure; its bootstrap IQR is printed in the appendix table. The full tables keep every CI. Where only a 95%
  CI half-width existed, one figure drew an IQR-equivalent band of half-width times 0.6745/1.96, and said so.
- **After any instruction about spread, grep every panel script you touch** for interval whiskers (`errorbar`,
  `ci=`, `sem`, `bootstrap`) and convert each hit to median and IQR, or remove the whisker and say so in the
  caption. The IQR rule had to be given again three months after it was set, because older panels still carried
  CIs.
- **The bar or point shows the estimator the caption quotes.** A written review found bars at per-fold medians
  under a caption that quoted Hodges-Lehmann estimates; the bars were redrawn at the estimate. Name the estimator in
  the panel docstring and assert in the script that the drawn column is the one the caption names.
- **One spread statistic per strip.** Do not mix CI and IQR within one row of panels.
- **Error bars of neighboring groups must not overlap**; space the groups or thin the bars.

## Axes

- **Bars start at 0 on a linear axis.** A baseline at `vmin − 0.1 × span` made small differences look large; it was
  replaced by an honest zero. The bar top equals the value.
- **The axis line starts and ends on a tick** (`S.ticks_span`); 3 to 4 ticks; the last tick above the tallest
  whisker so nothing is cut.
- **A narrow band of a [0, 1] fraction may be zoomed** only with the reference line drawn and the range visible on
  the axis. Prefer a linear axis with a scale factor (×10⁻⁵ in the label) over a log axis for a score.
- **Set a range from the data, not from outliers**, and say in the caption if a point lies outside it.
- **A value near zero must not read as zero.** On a linear axis, put the scale factor in the label (×10⁻⁵) so the
  smallest method's bar or point stays visible above the baseline, and print its value where the bar is too short to
  read. Never floor a positive value to 0 for display: a display that implied one method's contamination "is 0" was
  rejected ("do it for 10^-5 or sth that does not imply that [its] contam is 0").
- **Matched panels share one scale.** Panels that are compared get one y range, one color range (clamped and
  symmetric for signed maps, never autoscaled per axes) and one tick set. "use the same ranges in all 3 ... that's
  the point." Panels that are not compared fit their own data.

## What is drawn

- **Only measured values.** A failure gets its own mark (a method-colored dot struck by a red x); a missing record
  is a gap, never a dot. Estimated points were once drawn hollow on dashed lines behind a flag; when the author
  chose to draw estimates as filled points, the caption had to say so.
- **A run on part of the data counts as not run.** Prove "full" from the output's extent, not from the folder name
  or a log line: a `full/` run that logged "All done!" covered a crop. One test used a 100 µm grid: more than 20% of
  tissue bins without any assigned item meant a subset. The ML form: a cell of the results table exists only for a
  completed run on the full evaluation set; partial or extrapolated numbers stay blank and go on a to-run list.
- **Parity.** Every method has the same points. "we have 8 datasets, each method should have 8 points." If a value
  is unrecoverable for one method, drop that dataset for every method and state it.
- **A gap is reported, not decorated.** The deliverable for a missing number is a fetch list (paths, log names,
  commands), not a new glyph or a taller strip.
- **What the figure displays is the object the analysis computed.** Masks from the polygons the metric used; points
  re-embedded after filtering, not dropped from an old embedding; color by independent truth, not by the method's
  own assignment.
- **A method or column appears only if it is scored in that panel or is its genuine reference.** A method kept "for
  contrast" implies a comparison that is not made.
- **The quantity is the global one.** "whatever you show in bars and stats it should be global." A hand-picked
  example window is paired with a statistic over the whole data, and picked by a stated criterion (a rank-only scan
  returns the best available example; hard thresholds can return nothing). Mark failures of the own method in an
  example the same way as everyone else's.
- **When the example must read at print size, rank the candidates that pass the gates by the size of the feature
  they show** (its extent, or the number of items in it). The clearest window can hold a feature too small to see
  once printed.
- **A map that colors each unit by a quantity uses exactly the per-unit quantity the text aggregates**, so the
  reported mean or median can be read off the map. Map the fill to the observed range (alpha 0 to 1 on min to max)
  and state the aggregate. A map whose colors did not match the reported mean was rebuilt ("explain to me why not red
  ~= mean contam for each fov").
- **No silent filtering or subsampling.** State one filter once in the caption and methods; a supplementary sweep
  of the filter marks the default. A subsample is for display only, never for statistics.

## Emphasis

- **Emphasis by color, order or size only where the values are printed or plotted to scale.** Shaping a diverging
  map (a wide white plateau, min-max anchoring) is legitimate because the numbers are in the cells.
- **Equal weight for compared methods.** Same marker size, line width and fill. "don't make [our] points or lines
  thicker than other for no reason. let the results speak." The hero is told apart by its color, by being drawn
  last, and by a bold label; a thin dashed line at its value helps comparison. Stars on the best bar were removed.
- **"Make method X look pale" is delivered only where it is true.** In one figure the effect was real only inside
  certain structures; restricting the computation to those regions, and naming the scope in the caption, was the
  honest form. "the right answer to 'make it paler' is usually 'scope it to where it's real', and that scoping IS
  the science."
- **A summary form that rewards a degenerate method is replaced, not explained away** (the 2D good-corner plot).
- **Report the artifact that makes a method look best for the wrong reason** in the caption.
- **Size encodes nothing unless it means something.** Uniform marker size; priority by z-order.
- **One visual channel per variable.** When color already encodes a category, drop the table column, legend row or
  arrow that repeats it ("if you show technology with color no need to have that column"). Use size or a mark for a
  value and color for a category, never both for one variable.
- **A loud color inflates its class.** When the author suspects an excess ("why so many?"), recompute the count by
  an independent path before changing anything, then check how salient the class's color is. In the source the
  excess was real, and a saturated lime made it look larger; a calmer hue fixed the
  impression without touching the data.
- **Pair a count of how bad a failure is with a rate of what was recovered** (false items introduced beside the
  share of true items found). Two forms of one number look like corroboration and are not.

## The integrity line

Requests under deadline pressure can push a figure toward a wanted outcome. None of them becomes a rule here. The
honest forms:

- Freeze metric definitions, thresholds and gates before comparing methods. When a choice was made after seeing
  results, record that openly next to the choice.
- When a result changes between versions, show the diff of settings (normalization, filter, test) and explain which
  change moved it. Never adopt a flipped result silently.
- Curating an example for display is presentation; curating the inputs to a statistic is not allowed.
- A setting that differs from the default is reported where the result is reported, in the caption.
- A placeholder or an interpolated value carries a distinct mark and a caption note until replaced by a measured one.
- A result that runs against the narrative stays on the figure, labeled, never as the headline, and never out of the
  record. A pending row prints "pending" and fills in on the next build.
- When asked to omit something, say what a reviewer would find, and offer neutral wording that keeps the fact.

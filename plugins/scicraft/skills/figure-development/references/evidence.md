# Evidence standards for comparison figures

A comparison figure (a benchmark table, an ablation, a scaling curve, a head-to-head on
examples) is an argument that one arm differs from another. Each standard below closed a hole
that a co-author, an audit or the author found in a figure that had already been drawn. The
general rule comes first, then the instance it came from, then the machine-learning form.

## Contents

1. Anchor to a valid reference
2. State the null and plot it
3. Use honest units of replication
4. Subsample identically, or not at all
5. Gate every arm identically
6. Keep the metric from crowning its own objective
7. Measured values only, with failure marks
8. Equal coverage per method
9. Controls that should and should not move
10. Effect sizes, ceilings and the label lottery
11. Domain restriction and comparable baselines
12. What is drawn equals what is counted
13. Pre-register before measuring
14. Requests to leave things out
15. The claim-audit workflow

## 1. Anchor to a valid reference

- **The reference must be able to see the quantity being measured.** An off-the-shelf
  segmenter that missed most items of one class was used as "truth" for that class; there
  was no truth to recover. It was replaced by a reference built from the raw
  signal that includes the class, and the old reference became one of the failing methods.
  ML form: a judge model or labeler that is blind to the failure mode under test.
- **Never use your own method as the reference**, and never color or select by its output.
  It is circular.
- **Purge a dropped reference everywhere**: data, panels, composer, docstrings, caption.
  Then grep for it and confirm zero hits.
- **Each panel uses the reference that is valid for its own axis.** One supplement used two
  references, each for the graph type it could see.
- **Write down the non-circularity argument.** For each metric, list which inputs it shares
  with each compared model. If the reference was derived from any compared method's output,
  or from a model's own training signal, the metric is circular or semi-circular: fix it or
  bound it in the caption.
- **Check that the input actually carries the reference modality.** One dataset's "cell"
  outlines were a nucleus expansion because only a nuclear stain was present; its rows were
  restricted to what it could support. A gene panel assumed to hold canonical markers did not.
  ML form: confirm the eval set has the labels or features the claim needs before scoring.
- **Validate on a signal the method never uses as input.** Input signals and validation
  signals are two disjoint lists. A variant that used the validation signal as an input was
  declared invalid. ML form: no tuning on the test metric; no eval-time features in training.

## 2. State the null and plot it

- **Every effect axis carries a labeled null line**: "chance", "100% = no preference",
  "g = 1", a ratio of 1 or a difference of 0, drawn bold. A log2 fold-change heatmap with no
  stated baseline was rejected in three words: "logfc vs what???". The fix expressed the
  effect as a percentage of the random-mixing expectation, on a log axis, with a bold
  100% = no-preference line.
- **Test against the matched null, not zero.** A matched null had a mean of +0.10, so dots
  "significant against zero" overclaimed. A negative control that was assumed null was not
  (it had a real biological reason to deviate); the real null was a random, unclustered set.
  ML form: compare against a matched random baseline (random features of the same dimension),
  not chance = 0.
- **Name exactly what the null controls.** "Controls abundance and edge count, not the degree
  sequence" means the caption may not say "degree-controlled".
- **Every panel needs a visible good and bad anchor.** "No one understands which is good/bad"
  was fixed with a shaded "detected" zone above a bold chance line. Pale "expected" and
  "unexpected" background bands keep the bars in method colors.

## 3. Use honest units of replication

- **Replicates are independent units, not raw items.** Millions of edges make every p-value
  tiny (all were below 1e-70). Spatial blocks of [a fixed size] became the
  replicates, with a block bootstrap for intervals. ML form: seeds, datasets or sources are
  the units, not individual test examples; use clustered standard errors when examples are
  correlated.
- **Report the effect with its interval when every p is tiny.** A test on pseudoreplicated
  units is labeled descriptive.
- **Use paired differences per unit for rival against hero**: per block (or per seed, per
  task) compute rival minus hero, report the matched-pairs rank-biserial in [-1, 1] with its
  interval.
- **Check the effective n.** Labels assigned at cluster level made the effective n far below
  the nominal n; the claim was retracted.

## 4. Subsample identically, or not at all

- **Arms see the same indices, or each arm gets its own seed derived from its name.** A cap
  of [n] items per method was drawn with one shared random generator advanced in sequence
  across methods, so each method got a different subsample. A "method X misses signal Y"
  claim had already been printed on the panel as a "missed" label. With all items and a block
  bootstrap, every method detected the signal. ML form: eval subsets that differ per model.
- **Never print a binary verdict ("detected", "missed") from point estimates.** Print it only
  when the interval excludes the threshold.
- **No silent filtering or subsampling for statistics.** "do not subsample [the data]" came
  up repeatedly. A subsample may be drawn for display only. State the one filter applied
  to every arm once in the caption and Methods, and show a supplementary sweep of that filter
  (for example 5, 10, 20, 50) with the default marked.
- **When a metric depends on n, compare at equal n.** Subsample every set to a common n over
  several seeds ([n] seeds, stated) and show the full curve before any summary scalar.

## 5. Gate every arm identically

- **An asymmetric gate manufactures results.** A clean separation between two classes came
  from gating one class to adjacency and leaving the other ungated. Removed; both treated
  alike. Grep the prep for every filter and confirm it applies to all arms.
- **Select features, thresholds and markers once, on a neutral set, and freeze them** across
  methods and conditions.
- **Check that missing data is not asymmetric across arms.** A rare category was empty for the
  good methods and filled only by the method that fragmented items, so its heatmap row read
  backwards. Pool rare categories.
- **A reporting threshold applies to every result alike** and is stated in the caption.

## 6. Keep the metric from crowning its own objective

- **If the model's training objective is the metric, the metric cannot crown the model.** A
  purity claim was retracted because the model's embeddings were built from the same
  composition the metric scored. Mark each figure metric as circular, semi-circular or
  independent; lead with the independent one; bound the others in the caption ("states the
  mechanism, not independent validation"). ML form: do not score a contrastive model on the
  similarity it maximized; score it on a downstream task it never saw.
- **Never give a proxy the canonical metric's name.** A marker-pair proxy reported under the
  name of the published metric was relabeled "reference-free; not the published metric".
  After the relabel, grep composers, captions and docs for the old number.
- **Use the field's established tests and terms, starting from the most conventional.** "did
  you just invent this method or does it have a name?" Name the test, the correction, the
  thresholds and n per group. Statistical method choice belongs to the stats-reporting skill.
- **A rename is a label change proved by a numeric diff** (section 7 of SKILL.md;
  `scripts/number_parity.py diff`).

## 7. Measured values only, with failure marks

- **Every drawn point is a measurement read from a named file.** An interpolated value for one
  method on one dataset was added and removed: "figure = measured values only". Out-of-memory
  kills drawn as data (time until the kill, memory at the ceiling) were removed. Least-squares
  estimates drawn as filled points were deleted. A hollow-ring placeholder was shipped and
  reverted the same day.
- **Carry a `failure_kind` column** (OOM, TIMEOUT, FAILED, SUBSET, NOT_ATTEMPTED, and
  NOT_RECORDED for a number that exists but was not captured). The renderer refuses to draw a
  failure as a measurement. A failure is a method-colored mark struck with a red x, labeled
  with its cap ("out of memory ([cap])", "out of time ([cap])").
- **Lines break where a failure sits**: join consecutive measured points only.
- **A subset run is a non-run.** Prove "full" from the output's extent, not from a folder name,
  a log line ("All done!" came from a run on a crop) or a coverage number. For example, a run
  that leaves far more of a fixed spatial grid empty than whole runs do is a subset; set the cut
  from the whole runs.
  ML form: an eval on a truncated split; a job preempted and resumed on part of the data.
- **Plot the memory that limits each arm.** When arms run on different hardware, the headline
  axis shows device memory for a GPU method and host RAM for a CPU method. A second line of the
  axis label names the split ("method A: VRAM; others: RAM"), and the caption gives the other
  view. A scheduler's memory figure is host RAM; read device memory from the framework (see the
  sibling skill `performance-tuning`).
- **One clock for all arms.** An internal timer and the scheduler's wall clock ran several
  times apart within one line. Log timestamps without a date wrapped runs at 24 h, putting
  durations off by exactly 24 and 48 hours. A stale dry-run log posed as the real run.
- **Round counts are truncations until shown otherwise.** An input cut at exactly 1,000,000
  rows had been benchmarked by every method.
- **Audit each row of a results table against its raw log**, from a tracked script that also
  writes an audit file, and keep a "verified, not worth re-checking" list so the audit is not
  repeated (`scripts/coverage_audit.py`).
- **Never fit a model the points cannot carry.** A three-point log fit with a real zero
  floored to a quarter of the smallest value produced a line that missed every point. Join
  the measured points; a zero is a real value, so use a linear axis when one is present.

## 8. Equal coverage per method

- **Every method gets the same number of marks.** "we have 8 datasets, each method should have
  8 points." A silent blank for the hero at the largest dataset read as a hidden failure.
- **A cell is a measured point or an explicit failure glyph.** If a number cannot be recovered
  for one method, drop that dataset for every method. "Leave out the truly oom/oot ones" means
  out of the line, not out of the record: they keep their x.
- **A gap is a data request.** The deliverable for a missing number is a paste-ready list of
  what to fetch (path, log name, command), not a new glyph or layout: "don't make it weird".
- **A method appears only if it is a scored competitor or the genuine reference** for that
  panel. A method kept "for contrast" implies a comparison that is not being made.

## 9. Controls that should and should not move

- **Every new-metric panel shows an upper anchor and a lower anchor**: real items as a
  positive control, random items as a negative control. "The claim holds if [the new items] are
  close to [real items] and far above random, consistently across types and across two algorithms."
  ML form: the oracle row and the shuffled-label row of an ablation table.
- **Add an internal negative control that should not move, in the same panel.** If it shifts
  without flipping, say exactly that and phrase the result as specificity.
- **A disqualified control is labeled as such.** One arbiter split cases at chance and its
  verdict swung with its own parameter; it was reported as disqualified, not as null.

## 10. Effect sizes, ceilings and the label lottery

- **Plot interpretable magnitudes** (fraction of total, log2 fold change, difference in
  percentage points). A "big separation" in a heatmap was a standardized statistic; the real
  fold change was small. Keep z or p in the caption or as a star.
- **Distrust a permutation z whose null tightens with the arm's own size.** A method with
  many more edges had a tighter null and an inflated z. Show a per-unit normalized
  effect. ML form: do not compare significance across eval sets of different size.
- **Prefer the effect that survives the skeptic lenses over the biggest raw gap.** The largest
  gap was an abundance artifact; it was plotted as a labeled control, not as a claim.
- **Check the metric's ceiling before blaming a method.** Feed perfect inputs (points drawn
  inside the true shape, at each item's real count) through the identical estimator. If the
  measured value sits on that ceiling, the residual is a sampling limit. If the ceiling sits
  below real data, the metric is broken: change the axis, after reproducing the old number
  exactly. ML form: the ground-truth retriever row.
- **Run a method-against-itself perturbation before claiming a per-class flip.** A seed change
  of the labeling pipeline on one method reproduced the flip for several times as many items
  as the between-method count. "Never repeat that claim." ML form: compare the between-model gap
  with the seed-to-seed gap.
- **Report the tension pair, not one flattering scalar**: precision with its recall or
  coverage twin, in the same strip, at the same scale.
- **A powered null reports its minimum detectable effect** with its interval.
- **Do not kill a confound by rarefying until a gap appears.** The latest rule: change the
  labels or the stratum so the confound is constant by construction, and show robustness by
  checking every depth bin. If the gap is monotone in depth, drop the claim. ML form: compare at
  equal compute or tokens by design, not by post-hoc subsampling.

## 11. Domain restriction and comparable baselines

- **Restrict to the domain where the effect is defined, built once from data no arm produced,
  and apply it identically to all arms.** Regions came from raw signal density (the top [q]% of
  blocks) and were the same for every method. ML form: slices defined from input features,
  never from a model's predictions.
- **Match baselines on nuisance dimensions** (count, budget, parameter count, compute). Use
  per-unit annotations and composition percentages, not raw totals, when raw totals reintroduce
  a size confound; report widths in physical units.
- **When the evaluation objective and the claim disagree, optimize for the claim axis.** Sweep
  the knob, plot the claim metric against its guard metric, pick the knee, and name the region
  where a setting wins by collapsing the guard ("rejected as gaming").
- **When three or more different variants land within noise, stop tuning.** Write the ceiling
  down and move to the representation or the data.

## 12. What is drawn equals what is counted

- **Every layer of a panel comes from one table and one labeling.** Masks colored by one type
  column and nodes by another disagreed for many type pairs. Import definition constants from the
  stats module; never redefine them in the panel.
- **Check label against pixels.** A printed value differed from what the tile drew. Decide
  whether the mismatch inflates or deflates the hero, and disclose it. Here it deflated the
  hero, so it stayed with a caption note.
- **Display processing must not remove the effect.** Smoothing that shrank shapes or hid
  contacts was undone or compensated by a stated buffer. Color by independent truth, not by the
  method's own assignment. Re-embed after filtering; do not drop points from a fixed layout.
- **Every layer the figure claims needs its evidence inside the frame.** If a panel draws an
  interaction, the frame must show the items that make it.

## 13. Pre-register before measuring

- **Write expected signs, candidate lists and the selection gate to a lock file before the
  sweep.** Selection scripts read the lock; panel scripts read the outcome. Record drops that
  lack a justification. ML form: freeze the eval suite and hypotheses before results.
- **Numbered predictions get one verdict each**: bug, dilution from wrong selection, or
  over-expectation. "do not fabricate signals that aren't real." Do not add a gate that
  collapses n to rescue a prediction.
- **Choose metric gates before seeing the ranking.** In the source a gate was moved after the
  ranking was known, and the note recorded the choice and its cost openly. If a gate is ever
  set after seeing results, the figure notes and the caption say so.
- **When a result changes direction between versions, stop and reconcile.** Diff the two
  pipelines (normalization, filters, test) and name the change that flipped the sign. Keep a
  settings diff table whenever numbers move ("every time you give me fully new results, this
  makes me anxious").

## 14. Requests to leave things out

Deadline pressure produces requests to hide or dilute weak results: to present non-default
runs as default, to leave a preprocessing step unstated, to show an estimate as a measurement,
to drop the features on which the authors' method looks worse, to tune settings until the
result looks right. None of these is a rule here. The honest forms:

| Request | Honest form |
|---|---|
| "say it ran with the defaults" | report every setting that differs from the default, where the result is reported |
| "leave that preprocessing step out" | state the procedure in the caption or Methods; an undisclosed step is what a reviewer or auditor asks about |
| "show the estimate as the value" | measured values only; the cell is a gap on a fetch list |
| "drop the markers where we look worse" | feature sets are fixed before scoring and identical across methods; curating display examples is allowed with disclosure, curating inputs to statistics is not |
| "pick the metric that makes us win" | pick by field convention before the ranking; a mixed result goes to the supplement with its number |
| "make the competitor's score reflect that it can't be that clean" | find the reference that can see the failure (section 1), or report the tie |

When asked to omit, flag the review risk once, offer neutral wording, and keep the record.

## 15. The claim-audit workflow

Use it before any comparative claim reaches a figure, and whenever a result "looks great".

1. State the claim and its supporting statistic.
2. Fan out k variant formulations plus three or four lens critics (depth or size,
   circularity, statistics, domain), then one synthesizer. Critics re-run code; reading prose
   is not enough.
3. Required tests: a permutation or label-shuffle floor; recompute under a common label set; a
   concentration check (do a few groups carry it?); effective n with a block test; the matched
   null.
4. Re-verify the make-or-break refutations adversarially.
5. Verdict: keep; demote to mechanism or illustration (no stars); or retract and replace with
   a confound-free stratum. Record dead rescue paths with "do not re-propose"
   (`references/negative-results.md`).
6. Before believing a surprise, re-derive the key number by an independent path, diff against
   the canonical recipe's file and lines, and check the denominator. Too symmetric, saturated,
   flat or mirrored patterns are bugs until shown otherwise; so are percentages that do not
   add to 100 and two analyses that agree suspiciously.

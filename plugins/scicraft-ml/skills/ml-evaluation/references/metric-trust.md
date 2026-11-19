# Metric trust

A metric earns a place in a benchmark by passing tests on inputs where the answer is known. Until it
has, every number it produces describes the metric more than the models.

## 0. Before inventing a metric

- **Find what the field already uses before inventing a metric, a test or a threshold rule.** Search recent
  papers at the target venue and the documentation of comparable tools, adopt the published definition and cite
  it. Invent only when nothing published measures the quantity, and say so in the methods. Several invented
  metrics in the source work were replaced by the standard form after a reviewer-style question.
- **Use the standard definition with the fewest free parameters.** Specificity is TN / (TN + FP), similarity of
  count profiles is a cosine, a test on counts is chi-square or a permutation. Drop every parameter, interval or
  correction that changes no decision: each one is a choice a reviewer can ask you to defend.

## 1. The trivial-solution test

For every metric, write one line: "what trivial strategy maximizes this?" Then pair the metric with a
second one that the trivial strategy breaks.

| Metric family | Trivial win | Paired metric that catches it |
|---|---|---|
| precision, purity, contamination | predict less (fewer items, smaller masks, abstain more) | recall, coverage, items per unit |
| recall, coverage | predict more (bigger masks, assign everything) | precision, contamination |
| agreement with a shape or a reference morphology | ignore the content, copy the prior | a content metric with no reference |
| purity of selected units | select only easy units | report the selected fraction beside it |
| retrieval at top-k | return near-duplicates of the query | diversity or a held-out-group split |
| calibration error | predict the base rate everywhere | accuracy or AUC |
| loss of a predictive objective | predict zero, the mean, or the marginal | log loss over its closed-form floor (see `training-diagnostics`) |

In the segmentation benchmark this rule came from, the trivial wins were all real: fewer assigned
items lowered contamination, bigger masks raised coverage, ignoring content matched morphology, and a
conservative selection inflated purity. The design response was a set of metrics with opposed failure
modes and a balanced profile across them. Build a failure-mode by metric table (rows: each way a method
can fail; columns: metrics) and check that every row is covered by at least one metric.

## 2. Planted truth

Before a metric goes into any figure, run it on inputs where the right answer is known:

- **Self-comparison scores the ideal value.** The reference scored against itself must give exactly 1
  (or 0 for an error). "Why should the reference itself get something not exactly 1?" was the question
  that found a bug.
- **Planted fractions.** Corrupt a known fraction of the input (0, 15, 30, 45, 55, 80 percent) and check
  that the metric moves monotonically and lands on the planted value where it should. One contamination
  metric was calibrated below about 45 percent foreign signal and then reported roughly min(f, 1 - f),
  because past 50 percent the unit flips identity.
- **Scale one input.** Multiply one feature or one class by 10. A metric that should be scale-free must
  not move. A "soft" variant of a co-expression metric went from 0.193 to 0.042 under that test while
  the published hard version stayed put; it was not the published metric and left the scoreboard.
- **Degenerate inputs.** Collinear points, float ids, empty units, a single class. Check the output schema
  is the same on failure paths as on the success path.
- **Determinism.** Run twice with the same seed. An unordered group-by feeding a seeded permutation gave
  different scores on identical runs.
- **Units.** A 20 "micron" radius applied to pixel coordinates scored 0.0 everywhere, silently.
- **Dead zones.** A ratio metric that clips at 1 scores every input at or below the clip identically.
  Plot the metric's distribution on real data before trusting its ranking.

Record a verdict per metric: pass, pass with caveats, or FAIL. Planted-input runs also correct
over-claims from code reading: an empirical round withdrew several findings of the first audit.

## 3. Known-good against known-bad

Score one run you know is good and one you know is bad. If they tie, the metric is out. Cases that
happened:

- A clustering agreement score read about 0 (between -0.004 and +0.003) for every run, good or bad, so
  an alarm that compared it with a correlation score of 0.2 was comparing two rulers.
- A split-half reliability was flat across every pooling scale (0.883 to 0.917) and could not choose one.
- A metric rose with coverage where intuition said it should fall; "question if there's a bug" found one.
- A known over-segmenting method scored well on a shape metric; the metric was debugged before the
  narrative was written.

Put the metric you trust in the automated pipeline. A metric run by hand off the pipeline means runs
get judged by whatever the pipeline prints.

- **Check the direction of each new metric over a sweep.** Before running, write the sign you expect between
  the metric and coverage, and between the metric and each contamination metric. Run a parameter sweep that
  moves coverage and compute the signs. A sign against expectation is a bug candidate until a planted input
  clears it.

## 4. Range and gating

- **A metric with no range cannot be the headline.** One metric read 0.0000 at every severity of a
  corruption sweep; another spanned only 0.946 to 0.967. Check each metric's spread over the conditions
  before plotting it.
- **A gated metric whose gated population changes with the treatment is biased by survivors.** With a
  minimum-count gate, a curve can bend upward under corruption because only the easy units survive.
  Emit the gate-passing count as its own series and score a second set fixed at the clean population.
- **A descriptor is not a quality score.** When a free parameter moves the metric by construction (mask
  size moves coverage; depth moves recall), hold the parameter fixed for every method or report the
  metric as a descriptor.
- **Freeze data-dependent selections before sweeping.** A "both axes improve" sweep was a large recall
  gain plus a flat specificity (change at most 0.02, non-monotone) whose drift came from recomputing the
  false-positive set at every threshold. Pin the selection at one operating point and set a minimum
  y-span on plots so a flat axis does not look like a trend.
- **Thresholds come from data with a stated rule** (Otsu, Li, Yen, a knee point on the plotted
  distribution), and the plot ships with the choice. Histogram thresholds fail silently on unimodal
  data; add a unimodality check.

## 5. Circularity

A metric is circular when it shares an input or a training signal with a model it scores.

- **List the model's training signals and mark each metric circular, semi-circular or independent.**
  When a model's embeddings are trained on class-proportion vectors, any class-composition metric
  scores the model with its own loss. Lead with the independent metric; bound the others in the caption.
- **The reference is external to every compared method.** Never use one compared method's output as
  the reference, and never use your own method as the reference. A reference that cannot see the
  quantity (for example, a detector that cannot see one class) is dropped or
  replaced, and every trace of it is removed from data, panels and captions.
- **Evaluate on the unperturbed source.** In a robustness study the evaluator built its reference from
  the input directory; scoring a perturbed run against its own perturbed directory would have scored
  every metric against the corruption. Enforce it in code: the preflight fails if the clean path
  resolves inside the perturbed tree.
- **Pair every reference-dependent metric with a reference-free one.** A metric that needs an external
  label set inherits that set's quality. Rankings across two references held while absolute values
  shifted by 7 to 14 percentage points and one metric inflated about 4 times; make cross-reference
  claims on ranks and absolute claims only within one reference.
- **Validation inputs and model inputs are disjoint.** A signal used to validate (staining, a held-out
  modality) is never an input.
- **Never give a proxy the canonical metric's name.** A marker-pair proxy reported under a published
  metric's name was pulled and relabeled "reference-free; not the published metric".

## 6. Too-clean numbers

Treat each of these as a bug until a file shows otherwise:

- three arms that agree to three decimals (check they loaded different checkpoints:
  `checkpoint_identity.py`);
- the same SD down a column (check the SD is over folds and not over seeds of one fold:
  `results_table.py` warns);
- a held-out curve that is too smooth (check the held-out set shares no group with training);
- a run that became 90 times faster, or memory identical across very different sizes;
- a volcano plot that is flat or one-sided (check normalization and the unit of replication);
- a count smaller than its parent count (43 transcripts across more cells than that);
- totals that do not add up across tables.

For each: name the raw file the number came from, recompute it independently, compare arrays by hash
across conditions, and state the coverage of any aggregate.

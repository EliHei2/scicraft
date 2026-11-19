# Subsampling, gates, filters, depth and budget

Every arm of a comparison sees the same data through the same filters, at the same budget. When it does not, the
gap is partly the difference in treatment.

## Identical subsampling

- **Same indices for every arm, or a seed derived per arm.** A claim that one method "misses" a signal
  was a subsampling artifact: a capped subsample was drawn with one shared random generator advanced
  sequentially across methods, so each method got a different random subsample. With all units and a block
  bootstrap, every method detected the signal. In machine learning: evaluation subsets that differ per model.
- **Subsample for display only, never for statistics.** Statistics run on the full data with one stated filter.
- **Equal counts when a metric depends on n.** Clustering, diversity and calibration metrics move with sample
  size. Subsample every set to the smallest set's count with several seeds (40 in one case), then show the full
  curve before any summary scalar. Moran's I "gave it backwards" and Gini and CV were "confounded by counts" until
  counts were equalized.
- **Determinism.** Fix the seed and the order: an unordered group-by fed a seeded permutation and gave different
  scores on identical runs. Run twice and diff.
- **Equal mark count per arm.** Every arm and dataset is a measured point or an explicit failure with its kind
  (out of memory, timeout, subset). If a dataset cannot be completed for all arms, drop it for all.

## Symmetric gates and frozen selections

- **Every gate and selection rule applies identically to every arm and class.** A clean separation between two
  classes was manufactured by an asymmetric gate (one class gated to adjacency, the other ungated) and was removed.
  Grep the preparation code for every filter and confirm it is applied to all arms.
- **Select once, on a neutral set, and freeze.** Markers were selected once from a reference and reused across all
  conditions. A sweep reported as "improves both" was a large sensitivity gain plus a flat specificity whose drift
  came from recomputing the false-positive set at every threshold; freeze any data-dependent selection before
  sweeping, and give flat axes a minimum span so noise does not look like a trend.
- **Selection may favor your method; the statistics may not.** Choosing which example to show can be deliberate
  and is disclosed ("for gene selection you can be biased, to compute the values you can't be"). Tests,
  normalization and thresholds are fixed before results are read.
- **Restrict to the domain where the effect is defined, built from data no arm produced.** Windows built once on
  raw signal and applied to every method; never windows drawn from the hero's output.
- **Write the expected signs and the candidate list to a lock file before measuring**, and have the panels read
  it. In machine learning: freeze the evaluation suite and the hypotheses before looking at results.

## Filters

- **One fixed, field-justified filter, stated once** in the caption and the Methods (for example at least 5
  counts per unit). No silent filtering; report every filter and how many items it removed.
- **Show the filter as a sweep** in the supplement (5, 10, 20, 50 in one case) with the default marked, so the
  reader sees the result does not hinge on it.
- **Every main-figure number equals the supplement at the supplement's default**, marked there with a dashed
  "default" line. One supplementary value differed from the main figure in the first decimal because a cache kept
  units below the main filter; it was fixed by applying the filter at read time. Keep shared filters in one constant.

## Depth, size and budget

The author's latest position, after first using rarefaction: **remove a depth or size confound by design, never
by subsampling until a gap appears.** "Changing the labels is the legitimate fix; rarefying is the trick."

1. Show that a gap is not depth-driven by reporting it in every depth bin and computing the correlation within
   each method, instead of matching depth after the fact.
2. Prefer a stratum where the confound is constant by construction (same item, same label, only the method's
   output differs).
3. If the comparison still favors the deeper method in every bin, write that it is monotone in depth and drop the
   claim.

A rarefied number that opens a gap is not printed on a figure. The same applies to "report the metric of what is
drawn": compute a separation score on the plotted 2D coordinates, not on a 50-dimensional space the figure does not
show, and with no adjustment that only one framing supports.

In machine learning the same rule reads:

- **Fix budgets before training.** Equal steps, tokens, GPU hours or parameters across ablations and architecture
  swaps, decided in the plan. Compare at matched steps and stage.
- **Match baselines on nuisance dimensions by design** (count, budget, parameter count, compute), and normalize
  per unit (microns, per cell, per token) so size does not stand in for quality.
- **A cost column compares like with like or stays out.** An inference-time column went through three forms in a
  day and was dropped because GPUs and workloads were unmatched across methods. Check what records exist
  before promising the column; state the confound in one line and ask before building it.
- **Report a setting that differs from the default where the result is reported.** Source-verify what "default"
  means (a command whose default applied no threshold was not a valid definition of default).
- **When an aggregate flips with the task pool, say so.** Report the rating on the planned pool and state that a
  different pool changes it.

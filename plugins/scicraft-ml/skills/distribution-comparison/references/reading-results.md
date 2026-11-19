# Reading the results and writing them down

How statistics are worded belongs to `stats-reporting`; comparing models belongs to `ml-evaluation`. This
file holds what is specific to a distribution comparison. Tags as in SKILL.md.

## The results table

One row per (view, comparison), with n per side on every row [notes]. Comparisons: observed; reference
halves; candidate halves; candidate one against candidate two where there are two. Columns: linear and
forest AUC with intervals, energy and MMD with p and z, precision, recall, density, coverage with its
analytic null, share out of support. A bar figure draws a faint baseline tick (candidate halves) on every
bar [notes].

## A null is a null

- **"A null result is reported as a null"** [notes]. When energy and MMD do not reject, both AUCs sit
  inside the baseline band and PRDC matches the halves, write that no difference was detected at these
  sizes, and give the sizes.
- **State what the design could detect**: for a correlation over n items at 80 % power and two-sided
  alpha 0.05, n=40 detects |r| ≈ 0.43 and n=200 about 0.20 (Fisher z); a null below the size that can
  detect the effect of interest is uninformative. For two-sample tests, run `simulate.py` at your N, M
  and d and report the smallest shift or contraction detected in nearly every run.
- **Never turn a null into "indistinguishable" or "covers 95 %"**: precision 0.93 and recall 0.95 at 60
  against 60 items are the no-difference level, not a coverage claim.
- Record a null with its hypothesis, test, sizes, result, likely reason and the scripts, so nobody reruns
  it unknowingly [notes].

## The link to downstream behavior

A common follow-up asks whether items far from the candidate side are the ones where a model trained on
the candidate does worse.

- **Do not presuppose the link**: "Do NOT assume correlation ... We want to test that rather than
  presuppose it" [notes].
- Spearman between per-item nearest-reference distance and the performance gap, a bootstrap interval
  (1000 resamples), and partial Spearman controlling for ranked log size (rows, features) [notes].
  Further controls used: high-cardinality categoricals, missing fraction.
- Performance gaps as a scale-free log ratio, log(error_baseline / error_model), over the items every
  model ran on, with imputed or missing results filtered out [ran].
- Published studies disagreed on this link (one found none, a later one a negative median correlation),
  so the question stays open until it is tested at a size that can detect it [lit].

## Summaries computed from tables

- **Write the summary as text computed from the result tables**, "no interpretation added" [notes]. Each
  line carries n per side and the baseline or chance level it is read against. A script that prints the
  summary from the tables keeps the text in step when the tables change.
- **Label every component** as exact reproduction, approximate reproduction or new extension, and never
  give a substitute the original's name [notes].

## Circularity and the ceiling

- **Ground truth for any secondary readout is external to both sides** [notes]. If a reference label was
  derived from one side's output or from an encoder's training signal, the readout is circular; write
  down which inputs each metric shares with each side.
- **Oracle control**: feed the true distribution (or clean inputs) through the same estimator. If the
  metric lands on its ceiling, a residual gap is a sampling limit; if the ceiling sits below the real
  data, the metric is broken [notes].
- **Test against the matched null, not zero**: a null with mean +0.10 makes "significant against zero"
  an overclaim [notes]. The halves baselines are the matched null here.

## Integrity

- Every view, comparison and baseline that was run stays in the record. A view that shows a smaller gap
  is reported beside the others, never in their place; a weak view goes to the appendix with its numbers.
- The reporting rule (which views, which baselines, which threshold for out of support) is fixed before
  results are read and applied to all views alike.
- A figure may drop a panel for space; the numbers behind it stay in the table. In the source study a
  summary-statistic panel was dropped and restored three times in one afternoon; the final version kept it,
  computed for every candidate including the ones added late.
- If the result contradicts the claim (the generator is not realistic in the non-linear test), the claim
  changes.

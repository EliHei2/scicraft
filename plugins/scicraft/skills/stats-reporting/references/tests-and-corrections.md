# Units, tests, effect sizes and the one correction

## Units of replication

The unit of replication is the thing that could have come out differently if the experiment were repeated: a
held-out fold, a training seed, a dataset, a patient, a spatial block. Test examples, cells, edges and tokens are
almost never independent.

- **Pick the unit so that nothing leaks across it.** In a tissue benchmark, moving the fold unit to the slide or
  patient took leakage down to 0%. In machine learning: group by source document, user, patient or
  scene before splitting.
- **Millions of raw units make every p tiny.** A graph analysis over millions of edges gave every p below 1e-70.
  The fix was 500 µm blocks as replicates with a per-block one-sample test of log2(observed/expected), and the
  effect size as the headline. A method-by-role interaction p over raw units was demoted to descriptive
  ("pseudoreplicated").
- **Effective n under clustering.** When labels are assigned per cluster, the effective n is far below the
  nominal n (intraclass correlation). One contested claim fell apart when effective n was computed and a block
  test run.
- **Never claim replicates you do not have.** A replicates claim did not hold: the seed never reached the model,
  so each point was a single run. Grep for
  `seed_everything`, `manual_seed`, `randperm`, `shuffle=True` and model initialization; split perturbation seeds
  from training seeds; run at least 3 training seeds per configuration, including the anchors; pin the GPU model
  so runs do not straddle architectures. With one run, the caption says "single run".
- **Cells versus samples.** For differential expression across conditions, test per sample (pseudobulk) or with a
  per-gene permutation over samples. A volcano that looked "so flat" came from testing over cells with a
  zero-inflation-blind default.
- **Too few units cannot be significant.** The exact two-sided signed-rank test cannot reach p < .05 with 5 or
  fewer paired units (the smallest possible p is 2/2^5 = .0625). A task with 4 folds was left out of a null-result
  figure because it would read as noise; say so where it is left out.

## Effect sizes first

- **Plot an interpretable magnitude**: a difference in percentage points, a log2 fold change, a fraction of the
  total, a Hodges-Lehmann shift, an observed/expected ratio. Keep z or p in the caption or as an asterisk.
- **Never let a standardized statistic pass as an effect.** A heatmap's "big separation" was a z-score or
  percentile; the real log2 fold change of that effect was small. A whole-section permutation z of about
  -800 was driven by abundance.
- **A permutation z whose null tightens with the arm's own size is confounded.** A method with about 3 times the
  edges had a tighter null and an inflated z. Report the per-unit effect (per edge, per cell, per token) with an
  interval when arms differ in n, density or edge count. In machine learning: do not compare significance across
  evaluation sets of different size; compare effect sizes.
- **Every effect axis names its null.** "logfc vs what???" rejected a forest and a heatmap. Express effects as a
  percentage of chance or as observed/expected with a bold line at the null (100% = no preference, ratio = 1,
  difference = 0) and name it in the axis label.
- **Report the honest pair.** A precision-like metric goes beside its coverage or recall twin in the same strip,
  so a gain bought by discarding items is visible. The cost panel sits at the same scale as the benefit panel.

## The paired test the author used

For per-fold scores of two methods on the same folds:

1. Pair on the unit (task and fold, plus the fold seed when folds are drawn with seeds).
2. Effect: Hodges-Lehmann shift of a minus b (median of the Walsh averages), with a 95% percentile bootstrap
   interval over units when the size is the question.
3. Test: exact two-sided Wilcoxon signed-rank, tie-aware (ties up to 1e-12 dropped, midranks).
4. Across tasks: a sign-flip permutation test stratified by task, statistic S = sum of the per-task standardized
   signed-rank statistics over sqrt(T), so each task weighs equally whatever its fold count. In text this is "the
   result over the N tasks together"; the words "Stouffer" and "composite" stay off figures and out of replies.
5. BH within the family.

`scripts/paired_tests.py paired` does steps 2 to 5 from a long CSV and prints the text the display rule allows.

## One correction

- **Benjamini-Hochberg everywhere.** Holm over comparators and BH within task coexisted once and drew "if you use
  BH then ... holmes"; the paper moved to BH only. Never name a second correction.
- **Define the family once** in the plan (for example: one family per task over all comparators; one family over
  all ablations) and say in the Methods, once, that every p covering several comparisons is adjusted.
- **"Significant" means adjusted p < .05**, in text, figures and replies. Asterisks follow it exactly. A later
  check removed the mark from two table entries whose adjusted p failed the threshold.
- **Asterisks mark significance** (adjusted p < .05) in figures and tables, drawn as separate text so the number
  stays centered. The caption defines the asterisk ("* adjusted p < .05, Benjamini-Hochberg"). Bold and underline
  may mark best and second best by value when the caption says so, a common venue convention; bold never marks
  significance. The author first bolded significant entries and switched to asterisks the same evening
  ("instead of bolding you can add star").
- **No special-case markers.** A dagger added for the one value outside the BH family was "a clear AI slop flag".
  The excuse behind it ("has no fold-level scores") was false: the records held fold scores. Check the records
  before printing an exception; then either re-run the family with the item in, or state plainly what was done
  ("is ranked but not part of the paired tests").

### Re-adjusting a family (the procedure used to move from Holm to BH)

1. The decision is taken: one correction, BH. Do not reopen it.
2. Collect the stored unadjusted p values per family.
3. Recompute the old correction from them and confirm it reproduces the stored adjusted values exactly. If it does
   not, the inputs are not what you think; stop.
4. Compute BH per family. Per family write the count significant, the largest significant adjusted p and its
   printable bound.
5. Write a changes file listing every place where a printed value or mark changes. Modify no inputs. A result
   whose significance flips under the new correction is named to the author explicitly, in both directions: the
   correction is chosen once for the whole paper, never per result.
6. Have the session or person who owns the records confirm the new values.

`scripts/paired_tests.py adjust pvalues.csv` does steps 3 and 4 and exits 1 when step 3 fails.

## Noise before verdicts (ablations and training runs)

- Each ablation wave carries one configuration-identical replicate as its noise unit, never borrowed from another
  wave. A difference smaller than 3 replicate SDs is printed as a tie, with the SD.
- A run with one seed is powered for large effects only.
- Compare at matched steps and matched stage. The controls gate the family before any variant is read: a short
  single-seed wave in which a trivial control scored at or above the full model was an unusable scoreboard.
- Read no trend from fewer than 4 to 5 points, and take medians over at least 20 logged steps. Reading training
  curves is covered in the `training-diagnostics` skill.

## Validate a new statistical method before it reaches a figure

Coefficient recovery against a standard library (Pearson 0.996 against statsmodels in one case), interval coverage
on simulated data (block-robust 0.93 against 0.25 naive), an analytic null against Monte Carlo (within 2%), a known
positive and a known negative through the same pipeline. A Wilcoxon default that was over-conservative on
zero-inflated data produced flat volcanoes; it was replaced with an exact Mann-Whitney U.

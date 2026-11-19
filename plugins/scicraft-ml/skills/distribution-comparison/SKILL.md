---
name: distribution-comparison
description: Compares two collections of data or of datasets (synthetic against real, a pretraining prior against a benchmark corpus, train against test, two cohorts, before and after a change) and reports every number beside a same-size no-difference baseline. Use it whenever the user asks whether two sets of items differ, how realistic a generator or prior is, whether there is dataset shift, or says "is our synthetic data indistinguishable", "the C2ST says AUC 0.5", "what does precision 0.87 mean", "run an MMD", even without naming the method. Holds what agents get wrong: one budget and identical preprocessing on both sides, a linear and a non-linear classifier test (a linear one misses a narrow distribution), permutation-calibrated energy and MMD distances, calibrated nearest-reference distance, PRDC at matched sizes, projections only for pictures, perturbations to attribute a gap, a null reported as a null. Prefer ml-evaluation for comparing models, stats-reporting for wording.
---

# distribution-comparison

How to say whether two collections differ, by how much, and where, so the answer survives a reader who
reruns it. Distilled from comparisons of synthetic and real data in many representations, and from the
evaluation rules of a year of representation-learning work. The lead examples are machine-learning ones
(generated against real data, a prior against a benchmark, train against test); the rules hold for images, documents, embeddings,
cohorts and tables alike.

Every rule carries its evidence: **[ran]** verified by running code in the source project (2026-10-08) or
by this skill's scripts; **[sim]** reproduced on Gaussian data by `scripts/simulate.py` here; **[notes]**
a decision in the project's design notes, not separately verified; **[lit]** read from a paper in the
source project; **[doc]** read from published lists or documentation, not run. Library facts are
dated; recheck them against the installed version.

> **PRIME DIRECTIVE: no distance between two collections can be read until the same distance has been
> computed between two halves of one collection at the same sizes.** These metrics do not read zero when
> there is no difference. Precision and recall sit near 0.85 to 0.89 for identical distributions at
> about 100 items. Print the baseline beside every number.

Three failures cost the most. Guard against them from the start:

1. **A gap that is only a collection artifact.** Without one budget, "real against synthetic" was "mostly
   big against 1024 rows"; integer columns typed as categorical and NaN patterns became top
   discriminators. Equalize the budget and strip trivial channels level by level (section 1).
2. **A blind test read as "indistinguishable".** When the synthetic cloud was a ×0.7 contracted copy of the
   real one, logistic regression gave AUC 0.49 to 0.51 while a random forest reached 0.84 and energy and
   MMD rejected in every run. Run both classifiers and a distance test (sections 3 and 4).
3. **Raw values read without a baseline.** Coverage has expected value 0.9999 at 100 against 500 items
   with no difference at all. Compute every metric for reference halves and candidate halves at matched
   sizes (section 2).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The question** in one sentence, and which side is the **reference** (the real data, the benchmark,
  the test set, the target cohort) and which the **candidate** (the generator's output, the prior, the
  training set). Recall, coverage and nearest-reference distance depend on this choice.
- **What one item is**: a row, an image, a document, a whole dataset. When items are whole datasets
  (tables, slides, corpora), n is the number of datasets, typically 50 to 600, and every statistic below
  is computed over datasets.
- **How each side was produced**: size of each item, preprocessing, type casting, missing-value handling,
  ordering, which generator version and settings. Diff the defaults across versions: a library release
  can silently change its generator's defaults, for example so that features become nearly
  independent; compare a simple dependence summary (mean |r|) across versions [ran].
- **The representations** (views) in play and whether any was trained on one of the two sides.
- **Derived copies**: chunks, subsamples or variants of one item. They are kept out of every fit and test.
- **What will be claimed** from the result, and by whom it will be read.

Work in a folder beside the data; write results as files that carry n per side and the settings.

## 1. One budget, one preprocessing, no trivial channels

Detail: `references/budget-and-channels.md`.

- **Subsample both sides to one budget with one seeded rule** (same rows per item, same features, same
  resolution, same token count), and keep the original size as metadata, never as a feature. A
  generator that emits exactly 1024 rows against benchmark tables of any size makes size the whole
  signal [notes].
- **Apply the same preprocessing to both sides**, including the side that is already in that form. The
  real tables got the prior's own preprocessing (clamp at inlier mean ± 4 SD, z-score, missing to the
  column mean), and the synthetic tables got it too, where it is nearly the identity [ran].
- **Know exactly what the candidate side emits** before comparing: clipping order, encoding of categories,
  label ranges, dtypes. A prior that clamps before its final z-score emits values far outside the clamp, and
  categories can arrive as unflagged z-scored codes [ran].
- **Strip trivial channels and report the gap at levels**: all features on raw data; canonical data
  without size features; dependence features only. Channels met: size, dtype-based typing, NaN
  patterns, a target column present on one side only, unshuffled row order [notes].
- **A feature missing in more than 20 % of items on either side is dropped**, "else imputation itself
  separates the groups"; "not applicable" is coded 0, never NaN [notes].
- **De-duplicate across sources before counting**: one public suite can sit almost entirely inside
  another, so the unique pool is much smaller than the sum of the suites [doc]. Match normalized names,
  confirm every match by identical row and column counts (names alone miss renamed datasets) and
  keep the mapping in a file; the procedure is owned by the sibling skill
  `research-kickoff/references/verify-spec.md`.

## 2. A same-size baseline for every number

- **Compute every metric three times** [notes]: observed (reference against candidate); reference halves;
  candidate halves sized min(N, M/2) against the rest, which mirrors the observed N against M. Where
  there are two candidates (two generator versions), add candidate one against candidate two.
- **Hold out a seeded share of the candidate (20 % by default)** for the nearest-reference calibration of
  section 5; never train any encoder on evaluation items (disjoint seed ranges per split) [ran].
- **Read the observed value against the baselines, not against zero or one.** In the test runs here, the
  bootstrap interval of a no-difference baseline excluded 0.5 (forest AUC 0.581, interval 0.514 to
  0.661) [ran]: the interval is conditional on the fitted models and optimistic, so the baseline and the
  permutation test decide.

## 3. Classifier two-sample tests: a linear and a non-linear classifier

Detail and the power table: `references/classifier-tests.md`.

- **Pre-register two classifiers and report both, never the maximum over them** [notes, sim]:
  `LogisticRegression(C=1, class_weight="balanced")` and
  `RandomForestClassifier(300, min_samples_leaf=2, class_weight="balanced")`.
  A linear classifier cannot separate a narrow distribution from a wide one with the same mean.

  | Candidate against reference (N=100, M=500, d=16, 10 runs here) | linear AUC | forest AUC | energy rejects |
  |---|---|---|---|
  | identical | 0.51 | 0.50 | 0.00 |
  | mean shifted 1 SD | 0.74 | 0.69 | 1.00 |
  | contracted ×0.85 | 0.51 | 0.62 | 0.80 |
  | contracted ×0.7 | 0.51 | 0.83 | 1.00 |
  | contracted ×0.5 | 0.53 | 0.98 | 1.00 |

- **Refit every data-dependent step inside each training fold**: cleaning, scaling, PCA and the
  classifier are one `Pipeline` [notes]. Never resample before splitting: a published study bootstrapped
  with replacement and then split 70/30, so duplicates sat in train and test and inflated AUC [lit].
- **Out-of-fold ROC AUC is the statistic**: chance is 0.5 at any class ratio, while accuracy at 100 against
  500 has a majority baseline of 0.83 [lit]. Use `StratifiedKFold(min(5, n_small))`, repeated (5 to 10
  repeats), probabilities averaged over repeats, AUC by the Mann-Whitney rank identity (with single-job
  forests this cut the test from 38 s to 9 s per view) [ran].
- **Interval**: stratified bootstrap of the out-of-fold scores (resample each side separately, 1000 to
  2000 draws), labeled "conditional on fitted models", plus the spread over repeats [notes]. For a p
  value, permute the labels and rerun the whole CV, p = (1 + C)/(1 + B), B = 200 to screen and 1000 for
  a headline (`--c2st-perm`) [lit].
- **When AUC is near 1, stop reading the p value.** Read each item's out-of-fold P(reference) as a
  per-item "out of distribution" score and the standardized coefficients as the features that separate
  the sides [lit].

## 4. Energy and kernel distances with permutation calibration

Detail: `references/distances-and-support.md`.

- **Energy distance is the primary distributional test** because it has no bandwidth:
  2E|X−Y| − E|X−X′| − E|Y−Y′| [notes, lit].
- **Unbiased MMD² beside it**, RBF kernel, bandwidth the median pairwise distance of the pooled sample
  (labels unused, so the permutation test stays exact) [notes, lit].
- **Permutation p values**, p = (1 + C)/(1 + B), every permutation in one matrix product over an
  indicator matrix; B = 200 to screen, 1000 for a headline [notes].
- **Report a z-score against the permutation null**, (stat − mean_perm)/sd_perm, because raw MMD values
  are not comparable across representations [notes]. `twosample.py` prints it for energy too.
- **Compute distances in a low-dimensional space** (cleaned, scaled, PCA to at most 32 dimensions):
  the power of kernel and distance tests falls polynomially with dimension [lit].
- **Exchangeability**: fit scalers, PCA and bandwidth on the pooled sample without labels, or refit them
  inside every permutation. "Fitting PCA on real only (or synthetic only) and then testing breaks the
  permutation null" [lit].

## 5. Nearest-reference distance, in calibrated units

- **Distance of each reference item to its nearest candidate item, divided by the median nearest-neighbor
  distance of held-out candidate items to the same candidate set** [notes]. This makes distances
  comparable across representations.
- **Out of support** = above the 95th percentile of the held-out candidate distances [notes]. Under no
  difference about 5 % of reference items are flagged (0.050 in 10 Gaussian runs here) [sim]; under a
  ×0.7 contraction 0.60 were [sim].
- **Report the share out of support and the per-item list**; break it down by any known stratum (for
  datasets: split regime, source suite) [notes].

## 6. Precision, recall, density and coverage at matched sizes

Detail: `references/prdc.md`.

- **The reference is `real_features`, the candidate is `fake_features`.** Recall is the share of reference
  items inside the candidate's k-NN manifold (how much of the reference the candidate reaches); density
  is candidate mass in reference-dense regions (1 under no difference) [lit].
- **Subsample the candidate to the reference size and average over 10 draws**: these metrics depend on
  sample size [notes].
- **Print the analytic coverage null** 1 − Π_{i=1..k}(N−i)/(M+N−i) and call coverage saturated when it
  is at least 0.99 [lit]. At N=100, M=500, k=5 it is 0.9999.
- **Recall and density are primary in the small-n regime.** The narrow-candidate signature is precision
  near 1, recall falling, density well above 1 (×0.7 contraction here: precision 0.999, recall 0.34
  against 0.88, density 3.2) [sim]. A mean shift lowers density (0.97 to 0.90 at 1 SD) more than precision
  or recall [sim].
- **Check recall at k = 3 and k = 10**; candidate outliers inflate k-NN balls [lit].

## 7. Many views: same items, balanced fitting, pictures only

Detail: `references/views-and-projections.md`.

- **Evaluate every view on the same items**: the inner join of items every view encoded; print how many
  were dropped [notes].
- **Fit projections on a balanced set**: all of the smaller side plus an equal-sized seeded subset of the
  larger (at least 30), "keeps synthetic variance from defining the axes" [notes]. Everything else (other
  candidates, perturbed items, derived copies, extra datasets) is placed with `transform`, never fitted.
- **Projections are for pictures only.** No reported number is computed from UMAP or t-SNE coordinates;
  do not refit a map per perturbation severity [notes]. Picture rules belong to `embedding-maps`.
- **Balance blocks before concatenating views**: each view cleaned, PCA to 16, divided by the square root
  of its total variance, then concatenated ("equal weight per set") [notes].
- **Compare a learned view with the training distribution of its encoder**: if items look out of
  distribution only to encoders trained on the candidate side, the gap is partly the encoder's
  familiarity. A 2×2 over {encoder family} × {trained on candidate, trained on reference} separates the
  two [notes]. Choosing and validating encoders belongs to `representation-probes`.

## 8. Attribute a gap with controlled perturbations

Detail: `references/perturbations.md`.

- **Perturb reference items with known operations and measure where they move** in the same fitted space:
  displacement over the noise floor (median distance between two disjoint halves of one item), change in
  distance to the candidate (< 0 means toward it), cosine with the reference → candidate mean difference,
  and agreement of directions across parents [notes].
- **Every perturbed item records parent, kind, requested severity, seed and measured severity**, and a
  test checks measured against requested (one column for column-wise kinds, 10 % for noise, 0.02
  otherwise) [notes]. For tables, `perturb_tables.py` builds all eleven kinds and writes each measured
  severity and its tolerance; `gap_attribution.py` checks them again and exits non-zero when they
  disagree [ran].
- **Pair perturbations that differ in one property**: nuisance columns (row-permuted copies, same
  marginals, no dependence) against redundant columns (noisy copies of informative ones) differ only in
  dependence structure [notes].
- **Ask the mirror question with candidate anchors**: which corruptions make candidate items look more
  like the reference [notes].

## 9. Read and report

Detail: `references/reading-results.md`. Wording of statistics belongs to `stats-reporting`.

- **A null result is reported as a null** [notes], with the effect size the design could detect: a
  correlation over n=40 datasets detects |r| ≈ 0.43 at 80 % power, over n=200 about 0.20 (Fisher z).
- **Do not presuppose a link** between distance and downstream performance; test it with Spearman, a
  bootstrap interval (1000) and partial Spearman on ranked log size [notes].
- **Write the summary as text computed from the result tables**, each line carrying n per side and its
  baseline or chance level, with no interpretation added [notes].
- **Ground truth for any secondary readout is external to both sides**, and an oracle input (the true
  distribution fed through the same estimator) shows the metric's ceiling before a gap is blamed on the
  candidate [notes].
- **Every number in the record stays in the record**: a favorable view is not reported alone, a weak
  view goes to the appendix with its number, and the reporting rule (which views, which baselines) is
  stated and applied to all views alike.

## 10. Scripts

Python 3.9 or later with numpy, scipy and scikit-learn. Run from the skill folder.

| Script | Does |
|---|---|
| `scripts/twosample.py` | the battery of sections 2 to 6 on two CSV or .npy matrices: observed, reference halves, candidate halves; JSON and per-item output |
| `scripts/simulate.py` | the same battery on Gaussian data with a known answer; `--selftest` asserts 14 known answers |
| `scripts/perturb_tables.py` | section 8 for tables: the eleven perturbation kinds plus label shuffle and row halves, seeded per grid point, with measured severity and a manifest; `--selftest`; numpy only |
| `scripts/gap_attribution.py` | section 8 from parent, perturbed and half-split vectors; flags severity mismatches |

```bash
S=<skill>/scripts
python3 $S/simulate.py --n-ref 80 --n-cand 400 --dim 24 --reps 10     # what each metric does at your sizes
python3 $S/twosample.py --reference real.csv --candidate synth.csv --id-col id --quick       # screen
python3 $S/twosample.py --reference real.csv --candidate synth.csv --id-col id \
    --c2st-perm 1000 --out result.json --per-item items.csv --jobs 4                         # headline
python3 $S/perturb_tables.py --tables real/*.csv --target y --quality --out perturbed --check  # then encode
python3 $S/gap_attribution.py --reference real.csv --candidate synth.csv \
    --variants variants.csv --halves halves.csv --id-col id --out attribution.csv
```

Hand-crafted summary statistics take `--scaler robust --signed-log --corr-prune 0.98`; learned
embeddings keep the default standard scaling [notes]. `--fit pooled` fits the distance space on all items
without labels, the exact choice for permutation tests; the default `balanced` follows the author's design
(section 7).

## 11. Check before anything is handed over

1. `simulate.py --selftest` passes on this machine (14 checks, about 100 s); for table perturbations,
   `perturb_tables.py --selftest` passes too (under 1 s).
2. Both sides went through one budget and one preprocessing; the trivial-channel levels are reported.
3. Every metric has its reference-halves and candidate-halves value beside it in the table.
4. Both classifiers are reported with intervals; neither is chosen after the fact.
5. Energy and MMD carry permutation p values and z-scores; B is stated.
6. Coverage is printed with its analytic null; a saturated coverage is not read.
7. Every view was evaluated on the same items, and the count dropped is stated.
8. No number comes from a 2-D projection.
9. Perturbation severities were measured and match the request.
10. A null is written as a null with its detectable effect size; nothing was dropped from the record.
11. Say what was not checked: library versions not reverified, sizes outside the simulated regime, a
    view whose encoder was trained on one side.

## 12. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| unequal item sizes | "Without this, 'real vs synthetic' is mostly 'big vs 1024 rows'" | one budget, size kept as metadata |
| a linear C2ST alone | "a linear classifier is blind to a contracted ('narrow') prior" | linear and forest, both reported, "not a max over them" |
| raw precision and recall | "at n ≈ 100 they sit near 0.85 even when there is no gap" | reference and candidate halves at matched sizes |
| raw MMD across views | "not comparable across views" | z-score against the permutation null |
| PCA fitted on one side | "breaks the permutation null" | balanced or pooled fit, then `transform` |
| numbers from UMAP | "UMAP is for visualization, NOT the primary quantitative metric" | PCA space for numbers, UMAP for pictures |
| a map refit per severity | "Do not refit a separate UMAP for each perturbation severity." | one fit, `transform` |
| naive concatenation | "Do not naively concatenate raw representations." | balanced blocks, equal weight per set |
| imputing sparse features | "else imputation itself separates the groups" | drop above 20 % missing on either side |
| a p value at AUC near 1 | "the p-value carries no information" | per-item P(reference) and coefficients |
| relative-to-norm displacement | "Relative-to-norm numbers cannot be compared across encoders" | noise-floor and calibrated units |
| an assumed link to performance | "Do NOT assume correlation ... We want to test that rather than presuppose it." | Spearman with interval, partial Spearman, null as null |
| density contours on item maps | "please drop the density lines overall it didn't work" | points only |

## Reference files

- `references/budget-and-channels.md`: budget, symmetric preprocessing, trivial channels and levels, cleaning settings, de-duplication, derived copies.
- `references/classifier-tests.md`: classifiers, folds, AUC, intervals, permutation p, saturation, per-item scores, the power table.
- `references/distances-and-support.md`: energy, MMD, permutation mechanics, z-scores, bandwidth checks, nearest-reference distance, libraries.
- `references/prdc.md`: definitions, roles, nulls, saturation, the narrow signature, k checks, metrics left out.
- `references/views-and-projections.md`: same items, balanced fitting, joint views, pictures only, agreement across views, encoder familiarity.
- `references/perturbations.md`: attribution design, perturbation kinds, measured severity, provenance, what to measure.
- `references/calibration.md`: the full simulation tables at d=16 and d=32 and how to run your own.
- `references/reading-results.md`: nulls, detectable effects, the performance link, text summaries, circularity and oracle controls, integrity.

# Classifier two-sample tests

A classifier two-sample test (C2ST) trains a classifier to tell the two sides apart and reads its
held-out performance. Training a classifier and checking it against chance is a two-sample test whether
or not it is called one [lit]. Tags as in SKILL.md.

## Two classifiers, both reported

- **Linear**: `Pipeline(cleaner, PCA, LogisticRegression(C=1, class_weight="balanced", max_iter=2000))`,
  for comparability with earlier work.
- **Non-linear**: `RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced")`
  in the same pipeline. An alternative with the same power on a contraction is logistic regression on
  [z, ‖z‖²], which reached AUC 0.90 (d=16) and 0.96 (d=32) on a ×0.7 contraction [lit, from the source
  project's simulations].
- **Report both, "not a max over them"** [notes]. Choosing the better one after seeing results inflates the
  statistic, and the pair carries information: linear near 0.5 with forest high is the signature of a
  difference in spread or shape at equal mean.

Why: a contracted copy (the "narrow prior" a published study reported) has the same mean and the same
principal directions as the reference, so no hyperplane separates it. Measured here (N=100, M=500, 10
runs, `simulate.py`) [sim]:

| Candidate | d | linear AUC | forest AUC |
|---|---|---|---|
| identical | 16 / 32 | 0.51 / 0.51 | 0.50 / 0.50 |
| shift 0.5 SD | 16 / 32 | 0.59 / 0.57 | 0.57 / 0.54 |
| shift 1 SD | 16 / 32 | 0.74 / 0.71 | 0.69 / 0.66 |
| contraction ×0.85 | 16 / 32 | 0.51 / 0.51 | 0.62 / 0.67 |
| contraction ×0.7 | 16 / 32 | 0.51 / 0.47 | 0.83 / 0.89 |
| contraction ×0.5 | 16 / 32 | 0.53 / 0.52 | 0.98 / 0.99 |

The source project's own simulation gave the same picture: linear 0.49 to 0.51, forest 0.84 (d=16) and
0.90 (d=32) at ×0.7, k-NN with k = ⌊√n_train⌋ 0.67 and 0.63 [lit]. For a pure mean shift the linear test
has more power than the forest.

## Folds, leakage and the statistic

- **Everything data-dependent is inside the pipeline and refit per training fold** [notes]: cleaning
  (column drops, imputation, scaling), PCA, the classifier. A cleaner fitted on all items leaks the
  test fold's statistics into training.
- **Never resample before splitting** [lit]. A published comparison bootstrapped with replacement and then
  split 70/30, so copies of one item sat in train and test.
- **Folds**: `StratifiedKFold(n_splits=min(5, n_smaller_side))`, shuffled, repeated with a new seed per
  repeat; 10 repeats recommended, 3 used for screening, 5 in `twosample.py` [notes]. Items that come in
  groups (several items from one source, one patient, one donor) need grouped folds; see `ml-evaluation`
  for fold purity.
- **Statistic: out-of-fold ROC AUC** of the probabilities averaged over repeats [notes]. Its chance level
  is 0.5 at any class ratio; accuracy is uninterpretable at 100 against 500, where predicting the majority
  gives 0.83 [lit]. Balanced accuracy is a secondary number.
- **AUC by the Mann-Whitney rank identity**, (sum of ranks of the positive class − n1(n1+1)/2)/(n1·n0),
  with average ranks for ties; together with single-job forests this cut the test from 38 s to 9 s per
  view [ran].
- **Continuous scores beat signs**: an accuracy-based C2ST ignores the classifier's confidence and has
  higher variance, so use AUC or logits [lit].

## Intervals and p values

- **Interval**: stratified bootstrap of the out-of-fold scores, each side resampled separately, 1000 to
  2000 draws, percentile interval, labeled "conditional on fitted models" [notes]. Cross-validation
  intervals under-cover because fold scores are correlated [lit]; report the spread over repeats beside
  it.
- **Observed here**: on two identical mixtures (60 against 300 items) the candidate-halves forest AUC was
  0.581 with interval 0.514 to 0.661, and on another draw the observed linear AUC was 0.586 with interval
  0.513 to 0.666 while energy p was 0.26 [ran]. A bootstrap interval that excludes 0.5 is not a finding;
  the baseline columns and the permutation p decide.
- **Small halves can read below 0.5**: reference halves of 60 against 60 gave linear AUC 0.40 and 0.42 in
  test runs [ran]. Read it as noise, never as "anti-separation". A likely cause is that each training
  fold over-represents the other side of the held-out item (explanation Suggested, not yet tested in real
  work).
- **Permutation p value** [lit]: permute the side labels and rerun the whole cross-validation,
  p = (1 + C)/(1 + B). B = 200 for screening (smallest p about 0.005), 1000 for a headline. In the source
  project's simulation the null AUC was 0.49 to 0.51 (SD 0.03 to 0.05) with rejection rates 0.00 to 0.07.
  `twosample.py --c2st-perm B` does this for the linear classifier with one repeat per permutation; the
  forest is too slow for it at B = 1000 on most laptops.
- **Imbalance check** (optional): mean AUC over 20 balanced subsamples (candidate drawn to the reference
  size) makes AUCs comparable across views and candidates [lit].

## When the AUC saturates

When AUC is near 1 (simple summary statistics of generated against real tables reached 0.97 to 0.9997 in
a published study), the p value carries no information [lit]. Read instead:

1. **each reference item's out-of-fold P(reference)** as a per-item "out of distribution" score
   (`twosample.py --per-item`);
2. **the standardized coefficients** of the linear classifier, which name the features that separate the
   sides;
3. **out-of-fold P(reference) of candidate items** as a density-ratio score: correlate it (Spearman) with
   the generator's recorded latent parameters to see which settings produce realistic items [notes].

## Library notes (dated 2026-10-08)

- `sklearn.model_selection.permutation_test_score(estimator, X, y, cv=..., n_permutations=100)` implements
  the label-permutation test with p = (C + 1)/(n_permutations + 1) [lit].
- A synthetic-data toolkit's detection metric reports the mean ROC AUC over CV splits and maps it to
  1 − (max(AUC, 0.5)·2 − 1) [lit]; that rescaling hides values below 0.5 and the baseline.
- XGBoost was run only for comparison with a published discriminator, with proper stratified CV [notes].

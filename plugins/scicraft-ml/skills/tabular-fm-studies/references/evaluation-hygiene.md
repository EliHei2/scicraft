# Evaluation hygiene specific to tables

Status tags as in references/environment-and-traps.md. The general rules (matched nulls, two-sample tests,
resampling inside the loop, debiased agreement statistics) live in `distribution-comparison`,
`representation-probes`, `ml-evaluation` and `stats-reporting`. This file holds what is specific to studies where
the unit is a whole table.

## 1. The unit is the dataset, and there are few of them [doc, notes]

- One row per dataset in every analysis; real counts are small (51 TabArena, about 144 deduplicated real tables;
  N_real about 50 to 200 against M_syn about 300 to 600 synthetic in the study).
- **State the detectable effect size before correlating anything with performance.** At alpha 0.05 and 80 % power,
  n = 51 detects abs r of about 0.38; n of about 144 detects about 0.23. "A null is informative only at n of about
  144." "Mind the Gap?" stated "we would detect correlations of abs r > 0.2" with N = 164 TALENT datasets.
- Do not assume the correlation the study hopes for; test it. "A null result is reported as a null."
- Report Spearman with a bootstrap interval (1000 resamples) and a partial Spearman on ranked log n_rows and log
  n_features, plus the BeyondArena Test-4 covariates (rows, high-cardinality categoricals, missing fraction).
- When a classifier separating real from synthetic tables reaches AUC near 1, the p-value carries no information;
  read each real dataset's out-of-fold P(real) as a per-dataset score and the standardized coefficients.

## 2. Aggregate per dataset first [doc, notes, rerun]

- Average over folds within a dataset before anything crosses datasets. Fold counts differ by size (TabArena 9 or
  30 folds; BeyondArena 3, 10 or 20 repeats of 3-fold by size), so pooling folds weights small datasets up.
- Compare models only on the datasets every one of them ran on; filter imputed rows (references/corpora-and-results.md).
- Metrics differ by target type (1 - AUC binary, log-loss multiclass, RMSE regression): never average raw errors
  across datasets. Use a per-dataset log ratio or ranks, and report counts by task type (rerun: TabICLv2 default
  against the best tuned+ensembled tree won 24/30 binary, 6/8 multiclass, 11/13 regression).
- Record each dataset's split regime (IID, temporal, grouped) and report by regime; a temporal or grouped dataset
  evaluated with IID folds is a different benchmark.

## 3. Derived copies stay out of every fit and every test [notes]

Derived versions of one table (row chunks, a zero-rate ladder, perturbed copies, label-shuffled copies, halves)
are near-duplicates. Filter them out of the reference set in every analysis script by an id convention (the study
used suffixes such as `_chunk` and `_zero`, and `parent~kind@severity#seed` for perturbations); project them onto
fitted spaces, never fit on them or test them. Otherwise they inflate density and retrieval.

Example from the study: one insurance table (10,000 policies, 95 % zero claim counts) in three target framings
(count regression, occurrence binary, frequency = count / exposure clipped at 1e-3), a ladder keeping every positive
and subsampling zeros to 90, 75 and 50 %, and four disjoint row chunks as a stability control; all projected.
The author asked how 95 % zeros became 50 %: write how every derived variant was built where it is shown.

## 4. Seeds and splits that cannot leak [notes]

- Disjoint seed ranges per purpose (prior evaluation tables, encoder-training tables, held-out synthetic tables);
  "evaluation tables never train Dataset2Vec".
- Hold out a seeded fraction of synthetic tables as the null reference (synthetic against held-out synthetic at the
  real sample size).
- Fit cleaning, scaling and PCA once on a balanced clean reference (all real tables plus an equal-sized
  deterministic synthetic subset, at least 30), so synthetic variance does not define the axes; transform the rest.
  No number is computed from UMAP coordinates.

## 5. Separate "the encoder knows the prior" from "the data differ" [notes]

A learned encoder trained on the synthetic prior may place real tables "out of prior" because they are unfamiliar
to it, not because they differ. A 2 x 2 over encoder training data separates the two:

| | trained on a synthetic prior | trained on real tables |
|---|---|---|
| large in-context model | TabICL | TabDPT |
| small set encoder | Dataset2Vec retrained on prior tables | Dataset2Vec with released UCI weights |

If real tables look out of prior only to encoders trained on the prior, the gap partly reflects familiarity. Caveat:
TabPFN v2's default checkpoint is the synthetic-prior base model, and architecture family (per-row tokens with
label-aware attention against column ISAB with CLS readout) may matter as much as training data. TabDPT's OpenML
pretraining corpus may overlap TabArena (unverified).

## 6. Label-aware representations [notes]

Before reading any embedding, say whether it contains the target (references/model-interfaces.md, section 3).
For label-aware models keep task, null and delta views and a label-free control. Separability can be computed
on marginal statistics and on the delta view separately, so a gap in one is not read as a gap in the other.

## 7. Concatenating descriptions [notes]

Balance blocks before concatenating: each description cleaned, PCA to 16, divided by the square root of its total
variance, optionally weighted, then concatenated; say "equal weight per set" where it is shown.

## 8. Report what each number is [notes]

- Every summary line carries n_real, n_synth and its null reference or chance level, and is computed from the
  result tables, with no interpretation added.
- Label every component R (exact reproduction), A (approximate reproduction) or E (new extension); keep a
  "Deviations from papers" list beside the results.
- Every non-default setting (restored is_causal, `batch_size_per_gp=1`, binned targets, AMP off, permutations
  averaged) is reported where the result is reported.

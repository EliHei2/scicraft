# Equal budget, the canonical copy, and dataset-level meta-features

Status tags as in references/environment-and-traps.md.

## Contents

1. Equal budget for every table
2. The canonical copy
3. Regression targets for classifier-only encoders
4. Channels that separate corpora for trivial reasons
5. PyMFE: inputs that give one feature list for every table
6. The "Mind the Gap?" 70-d vector, exactly
7. Cleaning meta-features before any comparison
8. Replicating a meta-feature-against-performance paper

## 1. Equal budget [notes, run]

- **Every table gets the same row and feature budget**; synthetic tables have exactly `max_rows` rows. "Without
  this, 'real vs synthetic' is mostly 'big vs 1024 rows'." The study used 1024 x 100 (the stage-1 prior's own
  limits) and kept the original size as metadata.
- Rows: seeded stratified subsample for classification (largest-remainder allocation, at least one row per class,
  classes re-encoded afterwards); a seeded random subsample for regression. Columns: a seeded random subset.
- The seed is a hash of (dataset id, global seed, purpose), so the same table always gets the same subsample and
  the hash seed of the process does not matter.
- Never take the first rows: "Mind the Gap?" used the first 512 rows unshuffled, which biases features on sorted
  tables [doc].
- Size features: report the gap with and without them (a "no shape" level), because a classifier separates corpora
  by size first.

## 2. The canonical copy [run, rerun]

Make a copy of every real table with the prior's own preprocessing, and pass synthetic tables through the same
function (near identity), so preprocessing is symmetric. `scripts/canonical_table.py` implements it:

1. Ordinal-encode categoricals; parse numbers stored as strings; drop datetime, period and timedelta columns and
   text columns (string with more than max(100, 0.5 n) distinct values); drop grouping and time keys; count every
   drop. A date read from CSV arrives as text and is dropped as text [rerun].
2. Budget (section 1).
3. `outlier_removing` (clamp at mean plus or minus 4 SD, mean and SD re-estimated on inliers, ddof 1, SD floor 1e-6),
   then `standard_scaling` (z-score, clip plus or minus 100). The numpy port matched tabicl's torch functions to
   4.8e-7 with an equal NaN pattern; the shipped test tolerance is 1e-4 [run]. Rerun on a toy table with a 1e9
   outlier: max abs difference 1.9e-5 against float32 torch, within tolerance [rerun].
4. NaN to 0 (the column mean after z-scoring). The functions pass NaN through, so impute afterwards. A constant
   column becomes all 0.
5. Drop categorical flags (the prior emits none); canonicalize regression targets with the same clamp and z-score.

Keep two copies where a description needs raw values (hand-crafted statistics computed on raw and canonical data);
learned encoders, PyMFE and Dataset2Vec read the canonical copy.

## 3. Regression targets for classifier-only encoders [notes, rerun]

The TabICL classifier, TabDPT's standard path, PyMFE and Dataset2Vec need classes. One classifier space for every
task: bin regression targets into 10 quantile classes with `searchsorted(side="left")`, so **ties go to the lower
bin and zero-inflated targets keep 2 or more classes** (a 90 %-zero count target binned to 2 classes in a rerun).
Hand-crafted statistics and landmarkers keep the raw target. Record `binned_target` with every vector.

## 4. Channels that separate corpora for trivial reasons [doc, notes]

Before claiming a real-against-synthetic gap, strip each channel, level by level:

| Channel | What happened | Fix |
|---|---|---|
| size | real tables bigger than 1024-row synthetic ones | equal budget; a level without size features |
| dtype | MtG types columns by dtype: real integer columns become "categorical", prior float columns "numeric"; `type_ratio` and `n_cols` became top discriminator features | cast every column to one dtype convention before typing |
| missingness | NaN only in real tables; meta-features NaN only in one group | "not applicable" is 0, never NaN; drop meta-features with more than 20 % NaN in **either** group, else imputation itself separates the groups |
| target handling | MtG appended the target as a column for synthetic tables while T4 tables had none | append it for both, or for neither |
| row order | first 512 rows | seeded random subsample |
| categorical flags | real tables flag categoricals, the prior emits unflagged z-scored codes | drop flags (canonical copy); pass `cat_cols=[]` to PyMFE |
| resampling before split | MtG bootstrapped with replacement, then split 70/30: duplicate tables land in train and test and inflate AUC | split first; refit every data-dependent step inside each fold |

The study reported the gap at three levels: all features on raw data; canonical data without shape features;
dependence and feature-target features only. The two-sample tests themselves are in `distribution-comparison`.

## 5. PyMFE 0.4.4 [run, doc]

```python
MFE(groups="default", features="all", summary=("mean","sd"), measure_time=None, wildcard="all", score="accuracy",
    num_cv_folds=10, shuffle_cv_folds=False, lm_sample_frac=1.0, hypparam_model_dt=None, suppress_warnings=False,
    random_state=None)
.fit(X, y=None, transform_num=True, transform_cat="gray", rescale=None, rescale_args=None, cat_cols="auto",
     check_bool=False, precomp_groups="all", wildcard="all", suppress_warnings=False, verbose=0)
.extract(verbose=0, enable_parallel=False, suppress_warnings=False, out_type=tuple) -> (names, values)
```

Groups: landmarking, general, statistical, model-based, info-theory, relative, clustering, complexity, itemset,
concept; "default" is general, info-theory, statistical, model-based, landmarking. `measure_time` takes
"avg", "avg_summ", "total", "total_summ" (there is no `timeopt`). `extract_with_confidence(sample_num=128,
confidence=0.95)` gives bootstrap intervals. MIT license, released 2025-08-17.

Rules [run]:
- **Impute first**: NaN in X turned 43 of 48 statistical outputs into NaN.
- **Bin the target**: with a continuous y, model-based returned 0 outputs (the name list changed), landmarking all
  NaN, statistical took 36 s, clustering 30 s, complexity over 240 s (killed).
- **`cat_cols=[]` explicitly**: "auto" detection differs between real tables and the prior's unflagged codes.
- **Fixed name list**: extract once on a reference multiclass table, `reindex` every table to it; fixed length is a
  test. Names were identical and in the same sorted order for 3-class, binary, 10 categorical columns and 256 rows.
- Always NaN: `g_mean.*`, `h_mean.*`, `sd_ratio`; `num_to_cat` NaN without categoricals; `can_cor.sd` NaN for binary.
- "Fast" profile = general + statistical + info-theory + model-based: **97 outputs** in about 1.2 to 1.3 s per
  table at 256 and 1024 rows (rerun: 97) [run, rerun]. In the pipeline with the canonical copy: 4 s at 1024 x 82,
  2 s at 256 x 25.
- Landmarkers (sklearn models) under `threadpool_limits(1, "openmp")` (section on OpenMP in environment traps).

Fit + extract seconds per table, 100 numeric features, 3 classes, `summary=("mean","sd")`:

| group | outputs | 256 rows | 1024 rows | 4000 x 100 | NaN outputs |
|---|---|---|---|---|---|
| general | 12 | 0.02 | 0.03 | 0.14 | 1 |
| statistical | 48 | 0.12 | 0.15 | 0.45 | 5 |
| info-theory | 13 | 0.94 | 1.02 | 1.78 | 0 |
| model-based | 24 | 0.03 | 0.10 | 0.80 | 0 |
| landmarking | 14 | 0.27 | 1.12 | 11.8 | 0 |
| relative | 14 | 0.25 | 1.13 | 7.8 | 0 |
| clustering | 8 | 0.04 | 0.29 | 4.7 | 0 |
| complexity | 34 | 0.15 | 1.79 | 54.9 | 2 |
| itemset | 4 | 0.57 | 2.38 | 15.4 | 0 |
| concept | 8 | 0.03 | 0.21 | 3.5 | 0 |

Complexity, itemset and landmarking scale steeply with rows; a "full" profile adds the slow groups with
`lm_sample_frac` below 1 for n above 2000.

## 6. The "Mind the Gap?" 70-d vector [doc]

From the code (`tabdistances/discriminator/features.py::df_to_vec`, treat the code as ground truth; the appendix
lists features the code lacks and omits `missing_rate`):

| idx | name | definition |
|---|---|---|
| 0 | `n_cols` | columns in the DataFrame, **including the target** for synthetic data |
| 1 | `type_ratio` | categorical columns / n_cols (typing rule below) |
| 2 | `missing_rate` | fraction of NaN cells |
| 3, 4 | `mean_col_skew`, `std_col_skew` | pandas `skew()` (bias-corrected G1) over numeric-dtype columns, NaN to 0; std ddof 1 (0 with one column) |
| 5, 6 | `mean_col_kurt`, `std_col_kurt` | pandas `kurt()` (bias-corrected excess G2); std ddof 1 |
| 7, 8 | `mean_abs_corr`, `std_abs_corr` | abs Pearson (pairwise complete) off-diagonal over numeric-dtype columns; std `np.std` ddof 0 |
| 9 | `frac_high_corr` | fraction of abs r **> 0.7** (strict; the appendix says at least 0.7) |
| 10 to 39 | `hist_mean[0..29]` | mean over typed-NUMERIC columns of a 30-bin cumulative histogram |
| 40 to 69 | `hist_std[0..29]` | `np.std` (ddof 0) of the same; zeros with at most 1 numeric column |

- Histogram per column: drop NaN; cast to float (non-numeric via `pd.factorize`); keep finite; zeros(30) if none or
  constant; `np.histogram(values, bins=30)` from min to max; `cumsum/total`. Bin 29 is always 1, `hist_std[29]`
  always 0.
- Typing: `float64` is NUMERIC unless `nunique/len < 0.2`; any other dtype is CATEGORICAL unless `nunique > 20`.
- Skew, kurtosis and correlation use numeric-dtype columns (integer-coded categoricals and the integer target
  included); histograms use typed-NUMERIC columns: two different column sets.
- Paper subsets (`analysis/pairwise-tables.py` drops `missing_rate`, prepends `n_cols`): Full 69, Scalars 9,
  Histograms 61 (the paper says 70 and 60).
- No quantiles, no target features, no mutual information, no Spearman. A brief that described MtG's features as
  "moments, quantiles, MI, Spearman" was wrong.
- For a faithful replication copy its preprocessing too (numeric-dtype columns only, first 512 rows, target as a
  column); for a main analysis compute on X only, add a separate target block, and unify dtypes first. Label
  each component as exact reproduction, approximate reproduction or new extension, and never give a substitute
  the original's name [notes].

## 7. Cleaning meta-features before any comparison [doc, notes]

Fit every step on the clean reference set (real plus synthetic, no perturbed or derived tables), then apply it.
L = literature-backed (Rivolli et al., Knowledge-Based Systems 2022), O = the study's own choice:

1. Extract with a fixed `random_state` (L). Pass `cat_cols` explicitly (O).
2. Map exceptions and plus or minus inf to NaN and log each case (L).
3. Drop meta-features with more than 20 % NaN in **either** group (O).
4. Drop near-constant features: IQR = 0, or one value in at least 95 % of tables (O).
5. log10 of size features (nr_inst, nr_attr, ratios) (L); signed `log1p` for abs skew above 2 on the reference (O).
6. One feature from each pair with abs Spearman above 0.95, keeping the one with fewer NaN (O).
7. Median-impute fitted on the reference; optional missing indicators (O).
8. `RobustScaler` (median/IQR), clip plus or minus 5 (O); `QuantileTransformer(output_distribution="normal")` as a
   sensitivity analysis; then PCA to 16 to 32 dimensions per description before any distance or test.

Rivolli et al. say which transformation to use "has not been satisfactorily addressed in the MtL literature";
these choices are the study's, not the field's.

## 8. Replicating a meta-feature-against-performance paper [notes]

The study replicated "Explaining TFM Differences Through Meta-Features" (arXiv 2605.28418: PyMFE features against
TabArena gaps; only `attr_ent.skewness` and `attr_conc.median` survived its protocol) on its own pool:

1. Gaps as log error ratios from per-dataset results (references/corpora-and-results.md, section 6).
2. PyMFE with the paper's rich summaries (mean, sd, median, min, max, range, IQR, kurtosis, skewness, quantiles,
   histogram) plus five controls from the raw table: log n, log d, d/n, categorical fraction, feature missing
   fraction.
3. Drop features with more than 20 % missing or at most 2 unique values; keep one per abs Spearman above 0.95 group
   (fewest NaN first).
4. Spearman per feature, Benjamini-Hochberg at 0.05, bootstrap sign consistency at least 0.90 over 500 resamples.
5. Print whether the paper's surviving features survive cleaning on your pool, and how many datasets entered.

The author asked why a recent meta-feature paper was missing from the first literature sweep; check the last few
months of arXiv for meta-feature and prior-coverage papers before fixing a feature set.

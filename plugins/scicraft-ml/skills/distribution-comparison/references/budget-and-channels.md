# Budget, preprocessing and trivial channels

A difference between two collections is only interesting when it is not a difference in how they were
collected. This file holds the steps that remove collection artifacts before any statistic is computed.
Tags as in SKILL.md: [ran], [sim], [notes], [lit], [doc].

## One budget

- **Every item is reduced to the same budget by one deterministic rule** [notes]. In the source study each
  table was subsampled to at most `max_rows` rows (stratified by class, seeded by the dataset id) and at
  most `max_features` columns; the full size was kept in metadata. The prior emitted exactly
  `max_seq_len` rows, so without this "real vs synthetic is mostly big vs 1024 rows".
- **Seed by item identity**, so the same item gets the same subsample in every run and every view
  (stratified largest-remainder allocation, at least one row per class, classes re-encoded afterwards)
  [ran].
- **Use a seeded random subsample, never the first rows**: a published comparison used the first 512
  rows unshuffled, which carries any ordering in the source file into the comparison [lit].
- Instances in other fields (Suggested, not yet tested in real work): images resized and cropped by one
  rule on both sides; documents truncated to one token count; cohorts with the same follow-up window and
  the same number of records per patient, or record counts kept as metadata.

When items are rows of one dataset rather than whole datasets, the budget is the number of items per
side. `twosample.py --max-per-side` caps both sides with a seeded subsample; classifier tests handle
unequal sizes with `class_weight="balanced"` and AUC, and PRDC subsamples to matched sizes itself.

## One preprocessing, applied to both sides

- **Apply the target side's own preprocessing to every item, including items already in that form**
  [ran]. The source study kept two copies of every real table:

  | copy | what it is | used by |
  |---|---|---|
  | raw | values as stored; categories as flagged ordinal codes; NaN kept | the "easy gap" statistics |
  | canonical | the prior's own preprocessing: clamp at mean ± 4 SD with mean and SD re-estimated on inliers (ddof 1, SD floor 1e-6), then z-score clipped at ±100; categorical codes lose their flag and are z-scored; missing values become the column mean (0) | every learned encoder and the canonical statistics |

  Synthetic tables already come out canonical, so re-applying the transform is nearly the identity and
  the comparison stays symmetric.
- **Know what the generator emits** [ran]: clamping before the final z-score leaves values far outside
  the clamp; rare-category columns can end with SD below 1; categories can arrive as unflagged z-scored
  codes in some priors' tables and not others; labels can be non-contiguous, so re-encode with
  `np.unique(..., return_inverse=True)`; label dtypes can differ between priors.
- **Pin the generator to the configuration that produced the artifact you compare against**, read from
  its training scripts at a pinned commit; do not trust package defaults [ran]. A release can set a
  sampling flag to a fixed value without a changelog entry, so a trainer run with default settings
  does not reproduce the published configuration.
- **Make the generator deterministic per item** [ran]: seed every random generator before each item,
  run it single-process, and test across processes and hash seeds. One generator's output depended on
  `PYTHONHASHSEED` because it iterated over a Python `set`; sorting fixed it. Parallelize across items in
  your own pool.
- **Record the generator's latent parameters per item**, even when the API hides them (wrap the sampling
  call), so a per-item realism score can later be correlated with them [ran].

## Trivial channels, removed level by level

List the features that encode collection artifacts, strip them, and report the gap at each level [notes]:

| Channel | How it leaked | Fix |
|---|---|---|
| size | row and column counts separate the sides by themselves | one budget; a level without size features |
| dtype typing | a method typed columns by dtype, so real integer columns became categorical and generated float columns numeric; type ratio and column count became top discriminators [lit] | cast to one dtype convention before typing |
| missingness | NaN patterns become the signal | "not applicable" coded 0, never NaN; drop features above 20 % missing on either side |
| asymmetric target handling | the target was appended as a column for generated tables only | the same treatment on both sides |
| row order | first rows taken unshuffled | seeded random subsample |

Levels reported in the source study: (1) all features on raw data; (2) canonical data without shape
features; (3) dependence and feature-target dependence features only. The third level asks whether the
gap is in the relationships or in the marginals [notes].

The cohort example of the evals: two sites whose per-patient summaries differ only in record count and
missing fraction separate at AUC 1.00; with those two columns removed the linear AUC is 0.54 and energy
p is 0.40 [ran].

## Cleaning settings for item vectors

Fitted once on the reference set of clean items (for distances) or inside every fold (for classifiers).
Defaults of the source study [notes]:

| Step | Hand-crafted statistics | Learned embeddings |
|---|---|---|
| signed log, sign(x)·log1p(\|x\|) | yes | no |
| drop columns above 30 % NaN | yes | yes |
| drop constant columns | yes | yes |
| drop one of each \|r\| > 0.98 pair | yes | no |
| median impute | yes | yes |
| scale | robust: (x − median)/(IQR/1.349) | standard |
| clip | ±10 | ±10 |
| PCA | to at most 32 dimensions | same |

`twosample.py --scaler robust --signed-log --corr-prune 0.98` gives the left column.

Meta-feature libraries need inputs that give the same output list for every item [ran]: NaN in the input
turned 43 of 48 statistical outputs into NaN in one library; a continuous target changed the list of
model-based outputs; automatic category detection differed between real tables and unflagged generated
codes, so pass the categorical columns explicitly and reindex to a fixed name list.

## Units, duplicates and derived copies

- **De-duplicate across sources by a normalized name or a content hash before pooling**: one
  public suite can sit almost entirely inside a larger one, so the unique pool is much smaller than the
  sum [doc] (name matching on the published lists). Confirm every name match by identical row and column
  counts and check the rest by eye: normalized names miss renamed datasets, which an identical row and
  column count can still find. Keep the name mapping in a file. The full
  procedure is owned by the sibling skill `research-kickoff/references/verify-spec.md`.
- **Derived copies of one item (row chunks, subsampled variants, a zero-rate ladder) are projected, never
  fitted or tested** [notes]; otherwise near-duplicates inflate density and retrieval.
- **Drop grouping and time key columns and record each dataset's split regime** (IID, temporal, grouped),
  then report out-of-support shares by regime [ran].
- **Bin regression targets when a method needs classes**: 10 quantile bins with ties sent to the lower bin,
  so a target with many zeros keeps at least two classes [notes].

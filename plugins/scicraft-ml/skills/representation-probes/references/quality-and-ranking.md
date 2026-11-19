# Quality of one space, and ranking several

## The analysis space

All probes run on the same coordinates for a given view:

1. Clean per view: signed log1p for heavy-tailed hand-made features, drop columns with more than 30% NaN and
   constant columns, drop one of each pair with |r| > 0.98 (hand-made features only), median-impute.
2. Scale: robust (IQR / 1.349) for hand-made features, standard for learned ones, clip at +-10.
3. PCA to at most 32 dimensions.
4. Fit 1 to 3 once on a reference set and apply with `transform` to halves, shuffles, perturbations and
   projected items. When two groups of very different size share the space, fit on a balanced reference (every
   item of the small group plus an equal-sized deterministic subset of the large one, at least 30) so the
   larger group's variance does not define the axes.

A pipeline fitted on one group only and then used for a permutation test breaks the permutation null; fit on the
pooled sample without group labels, or refit inside every permutation.

## Noise floor

- Split each item into two disjoint halves (stratified by class where items carry labels; seeded by a stable
  hash of the item id). Embed each half in the same analysis space.
- Noise floor = median over items of ||z(A_i) - z(B_i)||.
- Report it in the encoder's units and as a fraction of the median between-item distance (`noise_over_spread`
  in `probes.py quality`). A floor close to the spread means the encoder cannot tell items apart from samples.
- Halves contain half the parts. If the encoder's output depends on item size, the floor includes a size
  effect; a 75% subsample against the full item is the second reference used in the encoder survey.

## Retrieval

- Query z(A_i), rank z(B_i) among all B. Report top-1, MRR and chance 1/n.
- In the larger split-validity form, the query is a variant (a half or a 75% subsample) and the pool is every
  clean item from every source. A hit means the nearest item is the variant's own parent.
- A leave-one-fold-out form: split each item into K = 5 disjoint folds, query each fold against centroids of
  the other folds of every item, print chance 1/n, and report the ratio of median within-item fold spread to
  median between-item distance.
- Retrieval saturated at 1.00 for every encoder on a 10-table panel. A probe that every candidate passes ranks
  nothing; enlarge the pool before reading it.

## Label sensitivity

- label shift = median over items of ||z(item) - z(item, labels shuffled)||; null averaged over at least two
  content-defined shuffles.
- label sensitivity = label shift / noise floor.
- The ratio of label shift to subsample shift (`label_over_subsample`) is the survey's signal over noise.

## The encoder survey

Brief for choosing one frozen encoder (a subagent can run it; give it a download budget, a scratch environment
it deletes afterwards, and the instruction to recommend at most one addition):

1. Candidate table with columns: code and license, weights (size, gate, license), install on the target Python,
   speed, the vector it gives, label-aware or not, verdict. Gated or non-commercial weights and dead weight hosts
   decide candidates before any speed test does.
2. Toy input: success, output shape, vector dimension, warm time.
3. Speed input at realistic size on the target hardware (1024 rows x 100 features x 10 classes in the source
   study), CPU and accelerator, one and four ensemble members.
4. Determinism over repeated calls and row-permutation change.
5. Common-scale panel (below).
6. Recommendation: at most one addition, its settings, the risks to log, and the zero-cost fallback.

### Common-scale panel

- Items: a mix of real and synthetic (10 in the source study: four public toy datasets and six generated ones,
  each capped at 512 rows and z-scored).
- Z-score each encoder's dimensions across the clean items.
- Distances in units of that encoder's median between-item distance.
- Per encoder: label shuffle shift, 75% subsample shift, their ratio, retrieval, seconds per item.
- Agreement between encoders: Spearman of their pairwise distances (`references/agreement.md`), marked
  "indicative, not conclusive" at this size.

Result of the source panel, to show the shape of a reading:

| Encoder kind | Label shuffle | 75% subsample | Ratio | Retrieval |
|---|---|---|---|---|
| in-context model A, row stage | 1.23 | 0.33 | 3.8 | 1.00 |
| in-context model A, prediction stage | 1.21 | 0.18 | 6.7 | 1.00 |
| label-free sibling of A | 0.000 | 0.12 | 0 | 1.00 |
| in-context model B | 1.56 | 0.28 | 5.5 | 1.00 |
| in-context model C, trained on real data | 1.00 | 0.09 | 11.1 | 1.00 |
| in-context model D | 1.06 | 0.23 | 4.6 | 1.00 |
| set encoder, released weights | 0.001 | 0.012 | 0.1 | 1.00 |

Reading: a label shift far above the subsample shift means the vector encodes the input-to-target relation and
not only the input marginals. A label shift above 1 spread means shuffling moves an item further than the
typical distance between two different items, so the null views of that encoder will cluster together. C was
chosen; retrieval separated nothing.

## Split validity: which description is most valid

The author asked for "an embedding/stats set which makes most sense ... sth that is most valid". The answer was
a stability test over descriptions (hand-made statistics, meta-features, learned embeddings):

1. For every item: two disjoint stratified halves and three 75% subsamples, seeded by item id.
2. Describe each variant with each description; transform with the space fitted on the reference only.
3. Retrieval@1 against all items of all sources; report halves and 75% subsamples separately, and the subset of
   real items.
4. Move: distance to the parent over the median between-item distance.

The most valid description is the one whose variants find their parent and move least.

## Redundancy and informativeness

From the analysis package that this skill's `beyond` subcommand ports:

- redundancy: `cross_val_predict(RidgeCV(alphas=np.logspace(-2, 3, 12)), stats, view, cv=5)`, R² over all
  dimensions pooled (1 - SSres / SStot).
- informativeness: the same with the view predicting a behavior profile (out-of-fold scores of simple models
  per item, rescaled per item).
- Compare informativeness with the behavior R² from the statistics alone, which `beyond` prints when both
  inputs are given.
- Low redundancy with high informativeness means the view adds something the statistics do not carry.

Statistics as the reference must be computed on the same input copy the encoder saw. Remove trivial channels
first: item size ("without this, 'real vs synthetic' is mostly 'big vs 1024 rows'"), dtype conventions,
missingness patterns ("not applicable" stored as 0, never NaN, so a NaN pattern cannot become the signal), and
asymmetric handling of the target.

## Running `probes.py quality`

```bash
python3 scripts/probes.py quality \
  --encoder enc_a=emb/enc_a --encoder enc_b=emb/enc_b --zscore --out quality.json
```

Each folder holds `half_a.npy` and `half_b.npy`, and optionally `full.npy`, `shuffled.npy` and
`subsample.npy`, all items x dims with row i the same item. The table is ranked by label sensitivity when every
encoder has a shuffle, otherwise by MRR, and flags saturated retrieval.

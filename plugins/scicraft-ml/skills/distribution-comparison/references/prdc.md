# Precision, recall, density and coverage

These k-nearest-neighbor metrics came from the evaluation of image generators and apply to any set of
item vectors. They are the easiest to misread, because their no-difference values are not 1. Tags as in
SKILL.md.

## Definitions (reference X of size N, candidate Y of size M, k neighbors)

- **Precision**: share of candidate items inside the union of reference k-NN balls (each ball's radius is
  the distance from a reference item to its k-th reference neighbor) [lit].
- **Recall**: share of reference items inside the union of candidate k-NN balls [lit].
- **Density** = (1/(kM)) Σ_j Σ_i 1[Y_j ∈ B(X_i, NND_k(X_i))]: how many reference balls a candidate falls
  in, on average, divided by k. Expected value 1 under no difference [lit].
- **Coverage**: share of reference items whose k-NN ball contains at least one candidate item [lit].
  Expected value under no difference 1 − Π_{i=1..k} (N − i)/(M + N − i), independent of the distribution
  and the dimension [lit].

`twosample.py` implements all four (ported from the author's `prdc`), plus recall at k = 3 and k = 10.
The `prdc` package on PyPI (MIT) computes the same four from `compute_prdc(real_features=...,
fake_features=..., nearest_k=5)` [lit].

## Roles

The reference side is `real_features`, the candidate is `fake_features` [lit]:

- recall = how much of the reference the candidate reaches;
- coverage = share of reference items with a candidate nearby;
- density = candidate mass in reference-dense regions (above 1 when the candidate piles up there);
- each reference item's recall indicator is a per-item "inside candidate support" flag.

Swapping the roles changes the meaning of every number; state the roles in the table caption.

## Matched sizes and baselines

- **Subsample the candidate to the reference size and average over 10 draws** [notes]. The values move
  with N, M and k.
- **No-difference values measured here** (N = M = 100 after balancing, k = 5, d = 16, 10 runs) [sim]:
  precision 0.89, recall 0.88, density 0.97, coverage 0.97 (analytic null 0.971). At d = 32: 0.84, 0.86,
  0.98, 0.98. The source project measured 0.88/0.87 (d=16) and 0.85/0.80 (d=32) for precision/recall at
  100 against 500, and about 0.79 with k = 3 [lit]. Raw values mean nothing without the halves baseline.
- **Coverage saturates at unequal sizes**: at N=100 against M=500, k=5, the analytic null is 0.9999, and
  coverage stayed 1.00 under a 1 SD shift and under ×0.7 and ×0.5 contractions in the source project's
  simulation [lit]. Print the analytic null and call coverage saturated when the null is at least 0.99;
  `twosample.py` prints `coverage_null` and `coverage_saturated`.
- With N ≈ 100 items in 16 to 32 dimensions each reference ball is wide enough to reach some candidate,
  which is why coverage barely moves [lit].

## What each difference looks like (N=100 against M=500, matched to 100, k=5, 10 runs here) [sim]

| Candidate | d | precision | recall | density | coverage |
|---|---|---|---|---|---|
| identical | 16 / 32 | 0.89 / 0.84 | 0.88 / 0.86 | 0.97 / 0.98 | 0.97 / 0.98 |
| shift 0.5 SD | 16 / 32 | 0.86 / 0.83 | 0.89 / 0.87 | 0.93 / 0.88 | 0.96 / 0.96 |
| shift 1 SD | 16 / 32 | 0.85 / 0.83 | 0.84 / 0.83 | 0.90 / 0.92 | 0.94 / 0.96 |
| contraction ×0.85 | 16 / 32 | 0.97 / 0.98 | 0.68 / 0.51 | 1.77 / 2.61 | 0.99 / 1.00 |
| contraction ×0.7 | 16 / 32 | 1.00 / 1.00 | 0.34 / 0.12 | 3.22 / 6.03 | 1.00 / 1.00 |
| contraction ×0.5 | 16 / 32 | 1.00 / 1.00 | 0.04 / 0.00 | 6.37 / 13.3 | 1.00 / 1.00 |

- **Narrow-candidate signature**: precision near 1, recall falling, density well above 1 [sim, lit]. The
  source project measured recall 0.64 and 0.41 with density 1.9 and 2.7 at ×0.85, recall 0.31 and 0.08
  with density 3.3 and 6.1 at ×0.7 (d = 16 and 32) [lit].
- **Shift signature**: density falls below 1 while precision and recall move by a few hundredths [sim,
  lit].
- **Recall and density are the primary pair in this regime**; precision and coverage are reported but
  rarely decide [lit].

## Checks

- **Recall at k = 3 and k = 10** beside k = 5: candidate outliers inflate k-NN balls and recall with them
  [lit]. A recall that changes sign of conclusion across k is not a result.
- **Precision and recall in high dimension are asymmetric and outlier-sensitive**; later variants exist
  (probabilistic precision and recall, topological precision and recall) [lit]. Use them as checks, not
  as replacements chosen after the fact.

## Left out, with reasons

- **α-precision, β-recall and authenticity** were skipped in the source study [lit]: item space was
  multi-modal; about 100 items are too few to train the one-class embedding; the reference implementation
  requires equal sizes and assumes one roughly spherical cloud; memorization was not the question. Use
  them where the question is memorization and the samples are large.
- **A global-radius "coverage"** from a published study is a recall with a fixed radius at the 95th
  percentile, near 0.95 under no difference by construction. Keep it as an extra number only for
  comparison with that study, named for what it computes [lit, notes].

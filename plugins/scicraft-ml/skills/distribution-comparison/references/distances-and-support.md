# Energy and kernel distances, and nearest-reference distance

Tags as in SKILL.md.

## The space the distances live in

- Distances are computed in one cleaned, scaled PCA space of at most 32 dimensions [notes]. The power of
  kernel and distance tests "drops polynomially with increasing dimension" [lit], so test in the reduced
  space and never in a raw descriptor space of hundreds of columns.
- **Exchangeability** [lit]: every data-dependent step (scaler, PCA, bandwidth) is either fitted on the
  pooled sample without using the side labels, or refitted inside every permutation. Fitting PCA on one
  side only and then testing breaks the permutation null.
- The author's design fits the space on a balanced set (all of the smaller side plus an equal-sized
  seeded subset of the larger, at least 30) so the larger side does not define the axes [notes]. Strictly,
  the balanced choice uses the labels to pick the fit set. Under no difference, 40 Gaussian runs gave
  near-identical p values for raw, balanced and pooled spaces (rejection 0.05 at d=16 for all three)
  [sim]. `twosample.py --fit pooled` is the exact option; state which was used.

## Energy distance (primary)

- Statistic: E = 2E|X − Y| − E|X − X′| − E|Y − Y′|, estimated with within-side sums over i ≠ j
  [notes, lit]. Energy distance is the MMD of a distance kernel [lit] and has no bandwidth to choose,
  which is why it is the primary test.
- Permutation p value with the group sizes fixed, p = (1 + C)/(1 + B) [notes].
- z-score against the permutation null, (E − mean_perm)/sd_perm, so values can be compared across views
  (the source code computed z for MMD only; `twosample.py` adds it for energy).
- Libraries (dated 2026-10-08) [lit]: `scipy.stats.energy_distance` handles one-dimensional samples only
  and returns the square root; `dcor.energy_distance(x, y)` is multivariate and returns the un-rooted
  statistic; `dcor.homogeneity.energy_test(x, y, num_resamples=...)` and
  `hyppo.ksample.Energy().test(x, y, reps=1000)` run permutation tests on samples of different sizes.

## MMD (companion)

- Unbiased MMD²_u for unequal sizes: 1/(m(m−1)) Σ_{i≠j} k(x_i, x_j) + 1/(n(n−1)) Σ_{i≠j} k(y_i, y_j)
  − 2/(mn) Σ_{i,j} k(x_i, y_j). It may be negative [lit].
- Gaussian kernel on the standardized PCA scores, bandwidth the median pairwise distance of the pooled
  sample (a heuristic; labels unused, so the permutation test stays exact) [lit, notes].
- Do not subsample the larger side for the test; the unequal-size estimator handles it [lit].
- Report the p value and z = (MMD²_u − mean_perm)/sd_perm. "MMD values are not comparable across views"
  [notes].
- Bandwidth check (from the source project's recommendations, not run there): an aggregated MMD test
  without a held-out set for kernel choice, or the maximum over bandwidths {¼, ½, 1, 2, 4} × median
  calibrated by the same permutations [lit]. The aggregated test's reference code was not on PyPI on
  2026-10-08 and installed from its repository.

## Permutation mechanics

All permutations are evaluated in one matrix product [notes]:

1. Stack both sides, Z = [A; B], and compute the pairwise matrix once (distances for energy, kernel values
   with a zero diagonal for MMD).
2. Build an indicator matrix I of shape (N + M, 1 + B): column 0 is the observed split, the rest are
   random permutations of it.
3. Within-A sums are (I ∘ K I) summed over rows, within-B sums the same with J = 1 − I, cross sums
   (I ∘ K J); every column gives one statistic.

A 700 × 700 matrix with 1000 permutations takes well under a second. Memory grows as (N + M)²; above a
few thousand items per side subsample both sides with one seeded rule (`--max-per-side`).

**Calibration measured here** [sim]: under no difference, 400 Gaussian runs (N=100, M=500) gave rejection
rates 0.053, 0.045 and 0.058 at d = 2, 16 and 32. Runs of 10 gave 0.0 at d=16 and 0.3 at d=32 by chance,
and one block of 40 seeds gave 0.2 under several permutation seeds. Never estimate a rejection rate from
fewer than about 200 runs.

Power measured here (N=100, M=500, 10 runs, B=200, alpha 0.05) [sim]:

| Candidate | energy rejects d=16 / 32 | MMD rejects d=16 / 32 | energy z d=16 / 32 |
|---|---|---|---|
| identical | 0.0 / 0.3 | 0.0 / 0.3 | 0.15 / 0.33 |
| shift 0.5 SD | 0.9 / 0.6 | 0.9 / 0.6 | 3.4 / 2.4 |
| shift 1 SD | 1.0 / 1.0 | 1.0 / 1.0 | 12.0 / 8.3 |
| contraction ×0.85 | 0.8 / 1.0 | 0.9 / 1.0 | 2.9 / 4.7 |
| contraction ×0.7 | 1.0 / 1.0 | 1.0 / 1.0 | 15.9 / 21.7 |

The source project's simulation (30 runs) gave the same pattern: energy and median-bandwidth MMD 0.83 at a
0.5 SD shift and 1.00 at a 1 SD shift or any contraction, while the linear C2ST was competitive only for
mean shifts [lit]. The d=32 null row above is the 10-run chance result described in the calibration
paragraph, not a miscalibration.

## Nearest-reference distance and out of support

The distance of each reference item to the candidate side, in units that mean the same thing in every
view [notes]:

1. Split the candidate side into a reference part and a held-out part (seeded, 20 % held out).
2. For each reference item: d = distance to its nearest candidate in the reference part.
3. For each held-out candidate: d_hold = distance to its nearest candidate in the reference part.
4. Unit = median(d_hold). Report d / unit per reference item and the median over items.
5. Out of support: d / unit above the 95th percentile of d_hold / unit.

Under no difference about 5 % of reference items are flagged; measured 0.050 (d=16) and 0.052 (d=32) in
10 runs, 0.047 in 30 runs [sim]. Under a ×0.7 contraction 0.60 and 0.83 were flagged, under a 1 SD shift
only 0.07 [sim]: the measure detects reference items the candidate does not reach, and is weak for a
shift that leaves every item near some candidate.

A related number from the literature is the per-item percentile within the held-out distribution, a
calibrated "out of distribution" score that is comparable across views [lit]. A published "coverage" that
uses a global radius (a point is covered when its mean 5-NN distance to the other set is at most the 95th
percentile of that set's internal mean 5-NN distances) sits near 0.95 by construction under no
difference; keep it only for comparison with that study, and never under the name coverage (see
`prdc.md`).

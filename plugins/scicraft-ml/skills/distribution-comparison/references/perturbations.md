# Attributing a gap with controlled perturbations

Once two sides differ, the next question is in what way. Perturb items with operations whose effect you
know, measure how far and in which direction each moves in the same fitted space, and compare those
movements with the gap. Tags as in SKILL.md.

## Design

- **Anchors**: a deterministic set of reference items, spread over the range of size or complexity (the
  source study spread anchors by feature count and required at least 4 features) [notes]. Candidate
  anchors answer the mirror question: which corruptions make candidate items look more like the
  reference?
- **A grid of kinds × severities × seeds**, each perturbed item rebuilt deterministically from its parent
  and seed rather than stored [notes]. Identifier `parent~kind@severity#seed`; random generator seeded
  from a stable hash of (item id, kind, severity, seed). Never Python's built-in `hash()` of a string,
  which changes with `PYTHONHASHSEED`.
- **Every perturbed item records parent, kind, requested severity, seed and measured severity**, and a
  test asserts measured against requested with kind-specific tolerances: one column for column-wise
  kinds, 10 % for noise, 0.02 otherwise [notes]. Two tolerances needed widening when the port ran on small
  synthetic tables [ran]: regression label noise is a ratio of sample SDs like noise and gets the same
  10 %, and the scaling lower bound (measured above half the request) holds only from 7 numeric columns,
  because the largest of k draws of |U(−s, s)| falls below s/2 with probability 0.5^k. A perturbation that delivers a different severity than
  requested makes its displacement curve meaningless.
- **Pair kinds that differ in one property**: nuisance columns are row-permuted copies of existing columns
  (same marginals, independent of the target and of other columns); redundant columns are noisy copies
  (0.1 SD noise, 5 % category resampling) of the most informative columns. Both keep marginals; only the
  dependence structure differs [notes].

## Kinds used for tables (source study) [notes]

`scripts/perturb_tables.py` builds every kind in the table and returns measured severity;
`gap_attribution.py` then checks it against the request. The first column gives the script's kind names.
It reads CSV tables (one per item, with a target column), applies the default grid of the source study or
`--grid kind=s1,s2`, seeds each grid point from a sha256 of (item id, kind, severity, seed), and writes
each perturbed table plus a manifest (id `parent~kind@severity#seed`, parent_id, kind, severity, seed,
measured_severity, tolerance). Encode the perturbed tables with the same encoder as the comparison, join
the vectors to the manifest by id, and pass the result to `gap_attribution.py` as `--variants`; encoded
`half` tables become its `--halves`, with a `half` column (A for severity 0, B for 1). `--check` exits 1
when a table misses its tolerance [ran]. In a smoke run (6 parent tables of 200 rows; candidate tables
were the same generator with 0.6 SD added noise; six summary statistics as the encoder) the noise kind
gave cos to gap 0.97 and moved items toward the candidate, while row subsampling pointed away (−0.43).

| Kind | What it does | Measured severity |
|---|---|---|
| missing | MCAR missing values | share set to missing |
| noise | Gaussian noise relative to each column's SD | SD of noise / column SD |
| nuisance | row-permuted copies of existing columns | columns added |
| redundant | noisy copies of the highest-information columns | columns added |
| dropout | features removed | share removed |
| rows | stratified row subsample | share kept |
| label_noise | labels flipped, always to a different class (regression: additive noise) | share flipped |
| outliers | values set to median ± U(5, 10) SD | share affected |
| scaling | columns rescaled by 10^U(−s, s): "changes units, not information" | s |
| monotone | rank, log or exp warps | share of columns |
| cat_corrupt | category codes resampled, always to a different existing category | share affected |
| label_shuffle | permutes labels (a quality variant, `--quality`) | 1 |
| half | two disjoint row halves, severity 0 and 1 (a quality variant, `--quality`; gives the noise floor) | 0.5 |

Other fields (Suggested, not yet tested in real work): for images, blur, JPEG quality, color jitter and
crops with measured PSNR or SSIM as severity; for text, token dropout, synonym swaps and truncation with
measured edit rate; for cohorts, measurement noise, dropped visits and unit changes.

## What to measure, per perturbed item [notes]

| Quantity | Definition | Reading |
|---|---|---|
| displacement | distance from its parent | raw size of the move |
| displacement / noise floor | noise floor = median distance between two disjoint halves of one item | how far above resampling noise; below about 1 the view cannot see the perturbation |
| displacement / spread | spread = median distance between items | comparable across views |
| Δ distance to candidate | change in nearest-candidate distance, in held-out candidate units | < 0 moved toward the candidate side |
| Δ distance to reference | the same toward the reference side | < 0 moved toward the reference |
| cos to gap | cosine of the displacement with the reference → candidate mean difference | > 0 the perturbation points the way the gap points |
| direction agreement | mean pairwise cosine of displacements across anchors, per kind and severity | near 1 the perturbation moves every item the same way |
| monotonicity | displacement rises with severity | a flat curve means the view ignores the kind |

"Relative-to-norm numbers cannot be compared across encoders": one encoder's 0.1 % change "could just
reflect a large constant offset", so report displacement over the noise floor and over the spread, and
use a common-scale panel across views [notes].

`gap_attribution.py` computes all but monotonicity from three CSV files and exits non-zero when a
kind's measured severity departs from the request by more than `--sev-tol`. On a Gaussian test (gap a
1 SD shift along one axis; perturbations of 0.6 along that axis, along another axis, and one with a
wrong recorded severity) it gave cos to gap 0.98, −0.12 and 0.00, direction agreement 0.99 for all, and
flagged the third kind [ran].

## Reading

- A kind whose displacement lies along the gap (cos near 1, Δ distance to candidate < 0) across anchors
  is a candidate explanation of the gap ("the gap is noise-shaped"). It is evidence about direction,
  not proof of mechanism; say "consistent with".
- A kind that moves items far but orthogonally to the gap explains none of it.
- The mirror experiment (candidate anchors moving toward the reference) is the stronger test of a
  proposed explanation.
- Report every kind that was run, including those that explain nothing.

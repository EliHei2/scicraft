# Perturbation trajectories and the training-distribution design

## A perturbation set that answers questions

Controlled corruptions of an item, each at several severities, show what an embedding responds to. The source
study used eleven kinds on tables; the principle carries to any item made of parts.

| Kind | What it does | What it isolates |
|---|---|---|
| missing | values removed completely at random | sensitivity to missingness |
| noise | Gaussian noise relative to each column's SD | sensitivity to measurement noise |
| nuisance | row-permuted copies of existing columns | new parts with the same marginals and no dependence |
| redundant | noisy copies (0.1 SD, 5% category resampling) of the most informative columns | new parts with the same marginals and full dependence |
| dropout | columns removed | loss of parts |
| rows | stratified subsample | sample size alone |
| label noise | labels flipped, always to a different class (regression: additive noise) | the input-to-target link |
| outliers | values set to median +- U(5, 10) SD | tails |
| scaling | multiply by 10^U(-s, s) | units, which "changes units, not information" |
| monotone | rank, log-like or exp-like warps | marginal shape with order kept |
| categorical corruption | category codes resampled | discrete parts |

- **Pairs that differ in one property** carry the clearest reading: nuisance against redundant differ only in
  dependence, scaling should move an invariant encoder by nothing.
- **Severities include 0** (the anchor itself through the same code path) and at least three nonzero levels, so
  monotonicity can be computed (the source grid used 0, 0.25, 0.5, 1.0 for fractional kinds).
- **Measured severity.** Each perturbation returns the severity it achieved, and a test compares it with the
  request (one column for column-wise kinds, 10% for noise, 0.02 otherwise).
- **Provenance.** Id `parent~kind@severity#seed`; random state from a stable hash of (item, kind, severity,
  seed). Perturbed items are rebuilt from the cached parent and seed, never stored.
- **Anchors** are chosen deterministically and spread over item size (at least 4 features each in the source).
  Anchors from a second group (synthetic) answer the mirror question: which corruptions make them look like the
  first group?
- **Perturbed items are projected, never fitted.** They never enter the fit of the analysis space or of any
  classifier.

## Trajectory measures

For anchor a, perturbation kind k and severity s, the displacement vector is d = z(perturbed) - z(a).

| Measure | Definition | Reading |
|---|---|---|
| displacement over noise | median ||d|| / noise floor | below 1, the perturbation is invisible against resampling |
| displacement over spread | median ||d|| / median between-item distance | how far relative to the gap between items |
| direction agreement | mean pairwise cosine of d over anchors, per kind and severity | near 1, one direction for all items; near 0, item-specific |
| monotonicity | Spearman of severity against ||d|| per anchor, median over anchors | a space that measures the corruption moves further as it grows |
| change in distance to a reference group | distance to nearest reference item after minus before, in units of the reference's held-out nearest-neighbor distance | below 0, the perturbation moved the item toward the reference |
| alignment with a gap | cosine of d with the mean difference between two groups | positive, the gap is shaped like this perturbation |

Monotonicity is listed as a measure in the source design without its formula; the Spearman form here is
Suggested, not yet tested in real work.

```bash
python3 scripts/probes.py trajectory --anchors anchors.npy --perturbed perturbed.npy \
  --meta meta.csv --noise-floor 0.68 --out trajectory.json
```

`meta.csv` has one row per perturbed item with columns `anchor` (row index into anchors.npy), `kind`,
`severity`. Direction agreement is reported at the highest severity of each kind.

A paired perturbation probe also tests claimed invariances: apply the change, measure the output change, and
keep the null in the report. Adding positional vectors before a sum pool is exactly invariant
(sum(z + p) = sum(z) + sum(p)), so "the obvious fix silently fails"; only the probe showed it.

## The 2x2 over training distribution

Question: is a difference between two groups of items (real against synthetic) a property of the data, or of an
encoder that is familiar with one group?

|  | trained on the synthetic prior | trained on real data |
|---|---|---|
| large in-context model | model A | model C |
| small set encoder | set encoder retrained on prior samples | set encoder with released weights |

- If items of the real group look "out of prior" only to encoders trained on the prior, the gap partly reflects
  familiarity. If it persists for real-trained encoders and for hand-made statistics, it is a property of the
  data.
- Fill an empty cell on purpose. The real-trained in-context model was added for this cell; the set encoder was
  retrained on prior samples (GPU only; 1,500 steps against the original's early stopping at up to 10,000,
  which the report states).
- Seeds for samples that train an encoder are disjoint from evaluation seeds ("evaluation tables never train"
  the encoder).
- Check what each checkpoint was trained on. One "fine-tuned" default was an alias of the synthetic base model,
  and architecture family (per-row tokens with label-aware attention against column-set encoding with a CLS
  readout) "may matter as much" as training data. Say which reading the 2x2 can and cannot separate.
- The same logic applies outside tables: an image encoder trained on one scanner, a language encoder trained on
  one domain. Cross what it was trained on with what kind of model it is before blaming the data.
  Suggested, not yet tested in real work.

## Related

- Two-sample tests, classifier tests and distances between groups: `distribution-comparison`.
- Designing which perturbation arms to run and their gates: `ml-experiment-design`.

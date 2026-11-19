# Robustness studies

A robustness study asks how a method degrades as its input or its supervision gets worse. Reviewers ask it as
"how much error can it tolerate". Design it like a dose-response experiment.

## 1. The taxonomy

Name the axes along which the input can be wrong and cover each one. A list of convenient noises is not a study.

**Tables** (a perturbation suite from a tabular foundation-model study, eleven types):

| Type | Severity in natural units | What it changes |
|---|---|---|
| missing values (MCAR) | fraction of cells | presence |
| additive noise | multiple of the column SD | values |
| nuisance columns | number added, each a row-permuted copy of a real column | adds columns with the same marginals and no relation |
| redundant columns | number added, each a noisy copy of an informative column | adds dependence |
| feature dropout | fraction of columns removed | width |
| row subsampling | fraction of rows kept | size |
| label noise | fraction of labels flipped | supervision |
| outliers | fraction of cells replaced by extreme values | tails |
| scaling | factor | units |
| monotone transforms | transform family | marginal shape |
| categorical corruption | fraction of categories remapped | codes |

Nuisance and redundant columns both keep the marginals intact; only the dependence structure differs, so comparing
them compares like with like.

**Instance labels** (second instance): a 2 x 2 of boundary wrong vs object wrong,
crossed with too little vs too much: erode, dilate, drop objects, add spurious objects. Each axis has its own
signature on a precision and recall view: shrinking keeps precision at 1 while recall falls; dropping a fraction
q of objects gives recall 1 - q.

Write the honest limits of the taxonomy into the plan, for example that a 2x2 taxonomy oversells when erosion and
dropout only remove supervision. When the dose axis is anchored on a reference you do not trust as truth, say it
is coherent as a dose axis and not as a truth claim.

## 2. Severity and the shared axis

- Signed severity in natural units (multiples of the column SD, multiples of the mean object radius, fractions of
  cells).
- One shared x-axis across types where possible, for example the measured fidelity of the perturbed input against
  the clean one. Record the measured severity, not only the requested one.

## 3. Two zero levels

- Zero level A: a verbatim copy of the clean input.
- Zero level B: the clean input re-derived through the same perturbation code at severity zero.
- The gap between A and B is the pipeline's own artifact. In the source study a geometry bug silently deleted a few
  percent of objects, including in the zero level; level B made it visible.

## 4. Never evaluate against the corrupted input

- The test set and every reference the evaluator reads (ground truth, anchors, morphology references) come from
  the clean source. Validating a perturbed run against its own perturbed directory scores every metric against the
  corruption and makes the experiment circular.
- Enforce it in code. The preflight fails if the clean path resolves inside the perturbed tree, records the clean
  path in a `preflight.json`, and the job watcher checks that every evaluation job received exactly one clean
  input.
- Tabular form: the held-out rows and labels are never perturbed for evaluation unless the claim is about
  test-time corruption, and then the label comes from the clean table.

## 5. Readouts

Three readouts per level:

1. **Absolute quality**: the task metric against the clean reference.
2. **Stability**: agreement with the method's own clean-run output.
3. **Recovery**: agreement with the clean reference, plotted against the corrupted input's own agreement with that
   reference, with a y = x diagonal. A method that copies its input lands on the diagonal by construction; points
   above it repair the corruption.

Compute agreement in two ways when part of the output can be unassigned (unassigned as singletons, and on the
commonly assigned items only), and report both.

## 6. Training under corruption

- When the claim concerns supervision, retrain at every level.
- A 2 x 2 of {train clean, train corrupt} x {predict clean, predict corrupt} separates a biased learned function
  from a corrupted input scaffold.
- When missing outputs are possible, record them as explicit statuses. An export that dropped unassigned
  items read 100% coverage at every level.

## 7. Seeds and replicates

- Trace the seed to every random source: grep for `seed_everything`, `manual_seed`, `randperm`, `shuffle=True` and
  model initialization. A claim of replicates was retracted when the seed reached only the corruption draw and the
  method itself had no seeding at all.
- Keep `PERTURB_SEEDS` and `TRAIN_SEEDS` separate.
- At least 3 training seeds per level, including the zero levels.
- Pin the GPU model so a level does not straddle two architectures.
- Ban defaults for anything whose wrong value voids the result (data directory, reference path, method flags,
  resource limits): the script aborts when one is unset. Keep a "known-wrong assumptions" section in the plan so a
  corrected value is not silently reintroduced.

## 8. Provenance

Every perturbed input records its parent, type, severity, seed and measured severity. Rebuild it deterministically
from the cached parent and do not store it. Test the measured severity per perturbation type in the suite.

## 9. Invariance probes

For every invariance or sensitivity the method claims, write a paired probe: apply the transformation, measure the
change in output, and add the null (the same probe on a model or operator known to be invariant).

- Tabular: permute rows and check that a row-order-invariant model's table embedding is unchanged; permute columns
  and check the claimed equivariance; keep each column's marginal and destroy the joint (shuffle columns
  independently) to test whether the model uses feature interactions.
- Architecture before loss: a pooling operator with no slot information is exactly invariant, and adding a
  positional vector before a sum pool stays invariant (the sum of z + p equals the sum of z plus the sum of p).
  The obvious fix fails silently and only a probe shows it. Keep a guardrail row that re-creates the trap.
- Eval-side interventions write the same output format as a normal run, so every downstream probe runs on them
  unchanged.

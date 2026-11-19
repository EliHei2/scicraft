# Probes and inert knobs

## 1. Content, nuisance and batch probes

An anti-collapse term guards rank. It does not guard content, batch identity or structure:

- A positional residual kept effective rank high while the content signal collapsed ("anti-collapse is
  content-blind").
- An embedding whose dominant axes are dataset identity can be perfectly isotropic ("a rank guard, not a batch
  guard").
- No uniformity term can force a property the architecture cannot express.

Log on a fixed probe batch, per step or per evaluation:

| Probe | How | Bad sign |
|---|---|---|
| nuisance R² | ridge regression of the embedding on position, density, sequence length, dataset id | R² that rises while the content probe stays flat |
| selectivity | loss of a control trained on shuffled content minus loss of the real run | near 0: the model learns nothing the shuffle cannot |
| batch-id variance fraction | share of embedding variance explained by batch or dataset id | rising over training |
| content probe | linear probe on held-out labels from an independent source | at chance or at the twin |

Rules that came with it:

- Labels for a probe come from outside the representation. Labels from clusters of the embedding being probed gave
  the wrong sign for a whole session; two self-referential readouts agreed with each other and were both wrong.
- Put a batch or domain token into the predictor or decoder only, so the encoder stays batch-free, and never feed
  dataset id to the model as an input.
- Check that the probe separates a known-good from a known-bad checkpoint before trusting it. A clustering metric
  read about 0 for every run, good or bad.

For tabular and in-context models: regress the embeddings on dataset id and on nuisance columns such as row index,
missingness rate and table size. Suggested, not yet tested in real work.

## 2. Paired perturbation probes

For every property you claim the model has (it uses order, arrangement, interactions, context), write a probe that
applies a perturbation and measures the change in the output, and put the null in the evaluation.

Recipe:

1. Pick the perturbation that destroys exactly the property: permute content between slots, shuffle rows, shuffle
   positions within a radius, break the joint while keeping marginals.
2. Measure relative output change ‖f(x) − f(perturb(x))‖ / ‖f(x)‖ over many inputs and, for an architecture
   question, over 32 random initializations.
3. Compare with a positive control (a perturbation the model must notice) and a numeric floor (float rounding).

Measured cases:

- Sum pooling was exactly permutation-invariant: 2.0e-16 over all 24 swaps.
- Adding positional vectors before a linear pool stays invariant: Σ(z + p) = Σz + Σp. "The obvious fix silently
  fails." Sum pool plus a tag measured 8.998e-08 (dead); an attention pool plus an additive tag 7.954e-04; rotary
  encoding 2.602e-01.
- "Four real tower defects sat for a week with no symptom because the figures were structurally incapable of showing
  one." There was no arrangement null anywhere in the repository.

Rules:

- Architecture before loss: a discriminator on an invariant token has zero gradient.
- Scope every trap exactly. The rule "never add positional encoding" was overstated and nearly killed a correct idea;
  the measured rule is "never add positional encoding in front of a linear pool". Keep the counter-row that shows
  the trap.
- Never add a consistency term whose optimum is the invariance you are trying to break.

For tabular and in-context models: test row-permutation and column-permutation invariance or equivariance with an
exact tolerance (one encoder check used 1e-7), and test whether the model uses feature interactions with a probe
that keeps each column's marginal and destroys the joint (row-permute one column independently). Suggested, not yet
tested in real work.

## 3. Identical-output check

When variants look the same ("r3/r4/r5 literally have the same umaps, what's the bug?"):

1. Hash the weights of each checkpoint.
2. Hash the outputs on a fixed batch; compute linear CKA between variant outputs.
3. Compare rendered images pixel by pixel.
4. Read which readout each variant used. In the incident, the default readout bypassed the varied component.
5. Read the resolved config of each: five arm configs once differed only in comments and built the identical network,
   because structural switches were left to dataclass defaults.

## 4. Positional encoding band

A frequency ladder must match the coordinate units. With `max_period=1000` on coordinates in [0, 1], the top
frequency was 0.159 cycles per crop; the encoding was 99.3% affine in the input with rank 3, and a shift of a few
coordinate units was below bf16 rounding. The same bug appeared independently in a second codebase that applied an image-style ladder to
raw micron coordinates. "Every PE mechanism is a measurable no-op until it lands", and the null reads as "positional
encoding does not help".

Test: compute the encoding's numerical rank and its affine R² in the raw inputs; set the top frequency to the
Nyquist frequency of the finest grid that matters.

## 5. Inert-knob arithmetic

For each locality, capacity, cap or schedule knob, compute which constraint binds on the real data at the operating
point.

| Knob | Arithmetic that showed it inert | Lesson |
|---|---|---|
| neighbor radius [r] | at training density the k-nearest-neighbor radius was well below [r], so the neighbor count bound first; the receptive field was far below the intended one | compute the effective receptive field from the data |
| a point cap documented as never binding | bound at exactly 400,000 points | count how often each cap binds; log the retained fraction |
| episode length 200 steps | 0 of the arms completed a curriculum stage; at 24 steps 7 of 7 did | check every gate is reachable under the budget |
| sample reweighting | effective sample fraction (Σw)²/(N·Σw²) = 0.992 | compute it before claiming the reweighting matters |
| zero-init gate on a conditioning code | views started equal to the base and could stay so ("scale-code inertia, invisible today") | log the gate norm and the view-versus-base cosine per step |
| Euclidean margin 1.0 in d = 64 | saturated after imprinting about 9% of the target's variance | use a scale-free metric (cosine) |
| a loss averaged over d | diluted the term 64-fold, letting the regularizer dominate | reduce consistently; log term ratios |

Related rules:

- **A speed optimization can change the science.** Cutting a regularizer's random projections from 1024 to 256 for
  speed made 2 of 4 splits collapse (effective rank 4 to 5). A speed-up must give an identical loss trajectory at a
  fixed seed; "a change that alters the loss but still trains is the worst outcome, because it silently produces
  publishable numbers."
- **Train and evaluation in one regime.** Evaluation streamed without the node cap that training used, about a
  twofold shift in reach. A window parameter was asserted at training and not at inference; the checkpoint did not
  pin graph parameters. Persist every preprocessing parameter in the checkpoint and assert all of them at load.
- **Encode at training density.** Encoding at full density changed what the receptive field covered.
- **Fail loudly on unknown or disabled features.** A feature that a config switches off without a warning can stay off for a whole run; a
  misspelled config key used to fall back to its default; a removed key left in all 7 configs made every one
  unloadable once the unknown-key guard existed. Grep the configs when cutting a knob, and assert at step 0 that each
  expected feature is on.

For in-context models, check whether context-length or feature-count caps bind at inference and keep the inference
context distribution equal to training. Suggested, not yet tested in real work.

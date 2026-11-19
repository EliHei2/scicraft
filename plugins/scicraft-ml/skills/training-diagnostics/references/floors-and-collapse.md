# Floors and collapse

## 1. Trivial floors in closed form

For every loss term, compute what a model that learned nothing would score, from the batch's own targets, and log
loss divided by floor per term.

| Floor | What it is | Watch for |
|---|---|---|
| predict zero | the loss of an all-zero output | the usual floor for regression on unit vectors |
| best global constant | the loss of the best single output for the whole batch (the mean for squared error) | the collapsed solution of most latent objectives |
| best per-group constant | the best constant per group (per dataset, per class, per position bucket) | an oracle when groups are singletons; one attack was withdrawn for this reason |
| position only | a fit from coordinates or index alone | fit on held-out data it can score worse than a constant; one such floor set the bar about 46% too high |

Worked cases from real runs:

- A prediction loss pinned at 0.498 was smooth-L1 of a zero prediction against a unit-norm target. The predictor
  had learned to output nothing.
- Every step of a five-step architecture ladder logged a prediction loss of 0.007812. That is exactly 0.5/d with
  d = 64: smooth-L1 with mean reduction over d for a zero prediction against unit vectors. Effective rank was about
  63 of 64 at the same time. The objective was dead, the five architectures were indistinguishable, and the fix
  was a redesign, not a rerun.
- Smooth-L1 with β = 1 on unit vectors equals (1 − cos)/d, verified by autograd to 5e-10. The loss was already a
  von Mises-Fisher negative log-likelihood with concentration 1/d. A guardrail "never use cosine" therefore cost a
  64-fold gradient attenuation without anyone choosing it.
- "An arm reporting loss ≈ 0.0027 has learned nothing beyond its own coordinates": the position-only floor sat
  there.
- A per-level loss of 0.0 with zero mass means no valid query in that level. Log the mass beside every term.

For supervised and in-context models the predict-the-prior floor is the marginal label entropy (classification,
cross-entropy) or the target variance (regression, squared error). Log loss over that floor. Suggested, not yet
tested in real work.

## 2. The collapse margin

Derive the value of the full objective at the collapsed solution (every embedding equal, or the predictor at its
best constant) and log

```
collapse_margin = loss − loss_at_constant_solution        # positive = collapsing would lower the loss
```

A positive margin means the collapsed solution scores better than the model does, so the objective pays for
collapse. A negative and falling margin means the model beats collapse. This is the sign the kill rule uses
(`collapse_margin > 0`); write the convention next to the logged name, because the opposite one is also common. The incident: the latent objective's global minimum
was the constant field. The fully collapsed run had the lowest loss of the project. The
margin "would have flagged the problem within 100 steps, about 4 GPU-minutes."

- Use it as a kill criterion only after warmup and when sustained over 3 evaluations: in the campaign's gates, the
  kill rule was the objective paying for collapse over 3 consecutive post-warmup evaluations.
- Calibrate it under multi-GPU training. An uncalibrated margin moved from 1.52 to 2.44 when the batch was split
  over ranks, because the pooled statistics changed.
- When the margin says the objective pays for collapse, more anti-collapse weight does not help: "anti-collapse
  weights and pool sizes cannot repair a degenerate objective." Adding a variance hinge and target centering left the
  payoff in place; a discriminative form of the same objective flipped the margin's sign. Put contrastive,
  variance or whitening terms on a projector and deploy the features before it; add a data target (reconstruct the
  input or its context) on the deployed read-out.

## 3. Loss identities before weights

- Verify each loss identity with autograd before tuning a weight (section 1, the smooth-L1 case).
- Null-normalize statistic regularizers so that an isotropic batch scores about 1. Warm their weight from 0.
- Log term ratios. A regularizer that is 99.97% of the loss at step 0 makes the predictor give up; one ratio of
  regularizer to prediction ran at about 300 against an intended order of 1. Keep terms of order 1, with the
  regularizer a nudge (about 4% of the total in the design that worked).

## 4. Effective rank: a canary, not a verdict

Facts from real runs:

- Centered effective rank is blind to collapse onto a shared offset: it read 54.8 of 64 at total collapse, higher
  than every healthy run.
- "Effective rank tracks the learning rate."
- A good run converged at about 38 while a worse run sat at 62. Training curves and collapse statistics do not rank
  runs.
- A dead objective reached 63 of 64 alongside a shortcut solution.
- Raw effective rank is bounded by d; report effective rank divided by d, never raw values across different d.
- A trained encoder should be more anisotropic than at init.

What to use instead, together:

1. The deliverable's probe score minus the same architecture's random-init twin. Give the twin its own seed, name it
   `<parent>-rand-init`, and check that its initialization matches the student's (in one project the initialization
   explained 31 to 66% of twin margins, so "pretraining beats random init" was two claims).
2. The held-out trend on a fixed probe set.
3. Several collapse diagnostics: effective rank misses a cap, a uniformity loss misses a blob. Localize collapse per
   stage against the twin.

Before calling a 2-D picture of embeddings a collapse, measure: in one case effective rank was 56 of 64, the top
principal component held 3.8% of variance and dataset id 2.1%. A plot of the first two components shows about 6.6%
of the signal and looks like mush by construction.

## 5. Target rank

A target with low effective rank invites a trivial solution. Pooling one unit vector per masked block gave a target
of rank about 1 per block. The only low-loss answer was collapse, the anti-collapse term forbade collapse, and the
predictor output went to about 0. Working latent-prediction methods predict per-token targets. Per-token targets
fixed the trivial floor in that project; a later probe showed they did not restore arrangement, because the optimal
predictor had a rank-1 Gram matrix against a rank-64 target. Both findings stand, for different failures.

Test: compute the effective rank of the target per example and compare it with the representation's dimension.

## 6. Loss and guards on the shipped layer

Write, for each deliverable, the tensor that ships, and assert that the loss, the regularizer and the tripwire
attach to it. Three incidents:

- The anti-collapse term acted on the tower read-out while the shipped leaf got no direct loss and no anti-collapse
  term; the leaf collapsed (effective rank 10.5).
- The tripwire watched the student leaf while the shipped artifact was the teacher leaf.
- The default read-out bypassed the component being varied, so four variants produced identical pictures by design.
  The predict path shipped a normalized leaf and never called the tower, so no tower fix could move the deliverable.

When comparing architectures, score every readout separately. Prefer mechanisms that act by construction on the
deliverable over mechanisms that must be learned.

## 7. Liveness audit in the first 2k steps

- Gradient norm per module. A silent zero on the deployed path is a disconnected deployment.
- Movement since init per module. Whole levels stayed bit-equal to init in one run.
- Zero-init gains stayed at 0.000 to 0.001 of the gradient; parametrize auxiliary heads as residuals so their gain
  is exactly 0 at init and check it moves.
- K seed tokens initialized with std 0.02 stayed copies of one another (effective rank 2.025 of 4).
- LayerScale 1e-4 switched off 43.5% of parameters; 0.1 worked for shallow stacks.
- A warmed-up learning rate on a probe head kept its gain at 0 for thousands of steps.
- Gradients into the tower must exceed the optimizer's epsilon at init.
- Attention with query-key normalization at gain 1 was a uniform mean at init; start the gain at the square root of
  the head dimension.

## 8. Batch statistics

For any term that is not a sum over examples (covariance, isotropy, characteristic function, whitening):

- **Pool size.** With fewer pooled rows than d the estimator is rank-deficient and inoperative. Size the pool so that
  rows per rank ≥ d. Collapse tracked pool/d, not the weight. "Never scale lambda to fix collapse before checking
  the pool."
- **World size.** Under data-parallel training the term's gradient can arrive 1/world_size too small, silently, with
  the symptom (rank collapse at 8 GPUs) pointing nowhere near the cause. All-reduce the sufficient statistics, or
  pre-scale by world size because the framework mean-reduces.
- **Reduction across views.** An isotropy term averaged over views instead of summed halved the margin; collapse
  became a local minimum.

Keep every batch spanning several sources (at least 4 in the work this came from), so batch statistics do not
whiten one source.

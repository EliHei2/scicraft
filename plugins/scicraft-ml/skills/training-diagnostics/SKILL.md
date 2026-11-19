---
name: training-diagnostics
description: Diagnoses a model training run and returns a verdict with its receipts (collapsed or alive, better or worse, bug or effect) plus the one test that settles it. Use this skill whenever someone reads a loss curve or training log, asks "is it collapsing?", "why is the loss stuck?", "why do all three variants look the same?", "the new model looks worse", or wants to kill, restart or compare runs, even when they do not say diagnosis. Covers self-supervised, supervised and in-context models. Holds what an agent gets wrong by default: reading the last logged row, trusting effective rank as a collapse signal, missing that the loss sits at the value of a model that learned nothing, changing two levers at once, and calling a confound (input depth, a swapped checkpoint, window size, unequal steps) a model effect. Ships a windowed-median log reader. Prefer ml-experiment-design for planning ablations and ml-evaluation for benchmark protocol.
---

# training-diagnostics

How to tell what a training run is doing before anyone kills it, reruns it or writes it up. Distilled from a year
of self-supervised foundation-model training (a teacher and student objective with anti-collapse regularizers,
several model sizes, multi-GPU runs) in which the costliest weeks went to
three things: an objective whose lowest loss was the collapsed solution, alarms raised from single log rows, and
comparisons that differed in more than one factor. Most rules below came from one of those incidents, and each
comes with the number that exposed it. The checks are stated so they apply to supervised and in-context models
too. Where only the self-supervised case was met in real work, the line says "Suggested, not yet tested in real
work".

> **PRIME DIRECTIVE: no run is called collapsed, alive, better or worse until its number is set against what a
> model that learned nothing would score, read on the layer that ships, as a windowed median, in a comparison
> that changes one factor.**

The failures that cost the most:

1. **An objective that pays for collapse, watched with a blind metric.** The fully collapsed run had the lowest
   loss of the project, and its centered effective rank read 54.8 of 64, higher than every healthy run. It took
   about three model generations and roughly six GPU-days on one large run to see it. A margin over the collapsed
   solution, logged from step 0, would have flagged it within 100 steps, about 4 GPU-minutes (sections 2 and 3).
2. **A false alarm from the last logged row.** "Collapse" was reported twice in one session from last-row reads
   (154, then 125, then 111); the trailing medians were 168.7, 168.7 and 169.1. It cost the user's trust in every
   later report (section 1).
3. **A comparison that moved two factors.** A "thin versus dense input" gap turned out to compare two different
   checkpoints; a "new version versus old" bar compared 15k steps against 8k steps with a key feature silently off
   (section 6).

## 0. Before diagnosing

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The logs themselves** (the `train.jsonl` or CSV, evaluation rows, the run manifest), never a screenshot of a
  curve or a summary written by an agent.
- **The code line that writes each logged name** and the loss function it reads (section 1).
- **The resolved config of every run** as the trainer echoed it at start. YAML comments, docs and dataclass
  defaults disagree with it often: one project had four mask ratios in its docs and one in its code.
- **Which tensor ships**: the layer or head that downstream users read (section 3).
- **Identity of every checkpoint** by content (a weight hash or a key join), plus steps, data seen and input budget
  per run (section 6).
- **The claim at stake**: kill or keep, A better than B, collapse or not. A diagnosis answers one question.

Ask the user what changed between the runs they compare, and whether a run is still training. Never kill or
restart a running job yourself: the author stops jobs.

## The symptom map

Each row is a failure met in real work: what was seen, the test that isolates the cause, and the rule that
followed. Details and arithmetic are in the reference files.

| Symptom | Test that isolates the cause | Rule |
|---|---|---|
| "It's collapsing": a metric dropped in the last rows | `windowed_medians.py`: trailing median beside the previous window, spread beside the change | Never read the last row (section 1) |
| A logged "cosine" sits near 0 forever | open the line that logs it | Trace every logged name to its code line (section 1) |
| Loss pinned at a suspicious constant (0.498, 0.0078) | derive the predict-zero and predict-constant loss in closed form | Trivial-floor arithmetic (section 2) |
| The collapsed run has the lowest loss | loss at the constant solution, `collapse_margin` from step 0 | Margin over the collapsed solution (section 2) |
| Effective rank high, model useless | random-init twin margin, held-out trend, content probe | Effective rank alone does not show collapse (section 3) |
| Predictor output near 0, anti-collapse term at war with the loss | rank of the target per example | Match target rank to the representation (section 3) |
| The shipped layer collapsed while the monitored one looked fine | list which tensors each loss, regularizer and tripwire touches | Loss and guard on the shipped layer (section 3) |
| Rank fine, but embeddings encode position, dataset or batch | R² of embeddings on nuisance variables, batch-id variance fraction | Content, nuisance and batch probes (section 4) |
| A fix for order or arrangement "did nothing" | permute the inputs, measure the output change | Paired perturbation probes (section 4) |
| Variants r2 to r5 give identical pictures | hash weights, compare outputs pixel by pixel, CKA between variants | Identical-output check (section 4) |
| Changing a knob changes nothing | compute which constraint binds on real data | Inert-knob arithmetic (section 5) |
| A speed-up and the science moved together | fixed-seed loss trajectory before and after | Re-verify after any speed change (section 5) |
| Fixed something near a collapse and it collapsed again | arms that change one lever each | One lever at a time (section 6) |
| "The new model is worse" | same metric, same extent, same steps, same checkpoint identity, same input budget | Confounds that looked like model effects (section 6) |
| Three arms agree to three decimals; standard deviations equal down a column | confirm the arms loaded different checkpoints; confirm the SD is over folds | Suspiciously uniform numbers are bugs until shown otherwise (section 6) |

## 1. Read the log honestly

- **Trace every logged name to its code line before interpreting it.** A metric named "cosine" was computed one
  layer upstream of the loss and read about 0 for the whole run; it was measuring something nobody cared about.
  Write a short table: logged name, file and line, what tensor, what reduction.
- **Never read the last logged row; compare windowed medians.** Per-step metrics swing hard (one effective-rank
  metric moved from 88 to 190 between adjacent logged steps, a prediction loss from 5.5 to 7.4). Compare the median
  over a trailing window (about 2,000 steps in the original runs) with the median of the window before it, and set
  the change against the spread. The script carries a comment forbidding the last-row form; keep it.

  ```bash
  python3 <skill>/scripts/windowed_medians.py runs/a/train.jsonl --where event=none --keys loss loss_pred effrank
  python3 <skill>/scripts/windowed_medians.py runs/a/train.jsonl --where event=val --keys val_loss --best-min val_loss --min-points 3
  ```

- **No trend from fewer than 4 to 5 points or from the first ~10 steps; medians over at least 20 logged steps.**
  Five misreads in one session had this shape; "the 2-3-point read is most seductive precisely when it confirms the
  thing you just fixed."
- **A default is not an observation.** Never `.get(key, 0)` a metric and then interpret the zero; print `absent`.
  A per-level loss of 0.0 with zero mass means "no valid query", never "solved": log the mass beside each term.
- **Never plot a weighted loss as a learning curve while its weights warm up.** About 90% of one loss drop was the
  regularizer relaxing. Log each term raw, its weight, and its share of the gradient; quote a minimum together with
  the drift.
- **The training loss of a self-referential objective does not measure progress.** With a moving teacher,
  "teacher-relative losses fall when the target arrives, not only when the model improves"; pretext loss ran
  anti-correlated with transfer in one campaign. Judge progress on fixed referents: a frozen held-out probe, the
  random-init twin, the exact initialization. Take the checkpoint by its probe score, never the endpoint by loss.
- **Validation loss compares only within one objective, one mask distribution and one held-out set.** Three false
  kill decisions came from comparing validation loss across an added loss term. Key comparisons on the config and
  validation-set content hash.
- **A guard that fires all run long is not news, and a guard that cannot fire is not a guard.** Check thresholds
  against observed values: one tripwire allowed effective rank down to 8 of 64 while the collapsed value was about
  0.9.

`references/reading-logs.md` has the full procedure and the logging checklist.

## 2. Floors: what a model that learned nothing scores

- **For every loss term, derive the trivial floors in closed form from the batch's own targets and log loss over
  floor per term.** Floors to compute: predict zero, best global constant, best per-group constant, position only.
  A loss pinned at 0.498 was smooth-L1 of a zero prediction against a unit target. A loss of 0.007812 for every
  step of a five-step ladder was exactly 0.5/d with d = 64: "dead objective", and five architectures were
  indistinguishable because none of them learned.
- **Check the floor is a floor.** A per-group constant with singleton groups is an oracle. A position-only fit
  scored worse than a constant on held-out data and set the bar about 46% too high.
- **Derive the loss at the collapsed solution and log `collapse_margin = loss − loss_at_constant` from step 0.** If
  the margin is positive the objective pays for collapse. Use it as a kill criterion only after warmup and
  sustained over 3 evaluations, and calibrate it under multi-GPU training, where an uncalibrated margin moved from
  1.52 to 2.44.
- **Verify loss identities with autograd before tuning weights.** Smooth-L1 with β = 1 on unit vectors equals
  (1 − cos)/d to 5e-10, so a guardrail "never use cosine" silently cost a 64-fold gradient attenuation. A
  regularizer was 99.97% of the loss at step 0 and the predictor gave up.
- **Supervised and in-context models:** compare the loss against the predict-the-prior baseline, the marginal
  label entropy for classification and the target variance for regression. Suggested, not yet tested in real work.

`references/floors-and-collapse.md` gives the closed forms, the margin and worked arithmetic.

## 3. Collapse: what rank shows and what it hides

- **Effective rank alone does not show collapse.** Centered effective rank is blind to collapse onto a shared
  offset (54.8 of 64 at total collapse); it tracks the learning rate; a good run converged at about 38 while a worse
  one sat at 62; and a dead objective reached 63 of 64 with a shortcut solution. Report effective rank divided by d.
  Use two independent yardsticks: the deliverable's probe score minus its own random-init twin, and the held-out
  trend. As the author put it, "think of it with scores."
- **Measure before calling an embedding blob a collapse.** A 2-D PCA scatter of an embedding with effective rank
  56 of 64 and a top component at 3.8% of variance shows about 6.6% of the signal, so it looks like mush by
  construction. Print effective rank and variance explained first.
- **Match the target's rank to the representation.** Pooling one unit vector per masked block gave a target of rank
  about 1 per block; the only low-loss answer was collapse, the anti-collapse term forbade it, and the predictor
  output went to about 0.
- **Put the loss, the regularizer and the tripwire on the layer you ship.** The anti-collapse term acted on the
  tower read-out while the shipped leaf got no loss and collapsed (effective rank 10.5). Elsewhere the tripwire
  watched the student while the teacher shipped, and the default read-out bypassed the component being varied, so
  four variants were identical by design. Write the readout per deliverable and assert where each term attaches.
- **Run a liveness audit in the first 2k steps.** Log gradient norm per module and movement since init. Zero-init
  gains stayed at 0.000 to 0.001 of the gradient; LayerScale 1e-4 switched off 43.5% of parameters; whole levels
  stayed bit-equal to init.
- **Batch statistics need enough rows.** A covariance, isotropy or whitening term with fewer pooled rows than d is
  rank-deficient and inoperative; under multi-GPU training it can arrive 1/world_size too small. Check pool ≥ d per
  rank before raising its weight.
- **Weights cannot repair a degenerate objective.** Adding anti-collapse terms left the payoff for collapse in
  place; changing the objective's form flipped the margin's sign.

## 4. Probes that see what rank cannot

- **Content, nuisance and batch probes beside the rank canary.** An anti-collapse term guards rank, not content
  and not batch identity: a positional residual kept rank high while content collapsed, and an embedding whose top
  axes are dataset identity can be perfectly isotropic. Log per step: the R² of the embedding on nuisance
  variables (position, density, dataset id), selectivity (shuffle-trained loss minus real loss), and the fraction
  of variance explained by batch id.
- **Paired perturbation probes for every claimed property.** Apply the perturbation, measure the output change,
  keep the null in the evaluation. Sum pooling was exactly permutation-invariant (2.0e-16 over all 24 swaps), and
  adding positional vectors before the pool stays invariant because Σ(z + p) = Σz + Σp. Four real defects sat for a
  week because the figures could not show them. Architecture before loss: a discriminator on an invariant token has
  zero gradient.
- **Identical-output check.** When variants look alike, hash weights and outputs, compute linear CKA between
  variant outputs and compare rendered images pixel by pixel ("just compare the umaps pixel-wise").
- **Positional encodings must match coordinate units.** A frequency band set with `max_period=1000` on coordinates
  in [0, 1] was 99.3% affine with rank 3; the same class of bug appeared in a second codebase. Measure the
  encoding's numerical rank and affine R².
- **Tabular and in-context models:** test row and column permutation equivariance explicitly, regress embeddings
  on dataset id and on nuisance columns (row index, missingness), and test feature interactions with a probe that
  keeps the marginals and destroys the joint. Suggested, not yet tested in real work.

`references/probes.md` has each probe with its recipe.

## 5. Inert knobs

- **For every locality, capacity or cap knob, compute which constraint binds on real data.** A radius knob
  was inert because at training density the k-nearest-neighbor radius was well below it, so the neighbor count
  bound first. A cap documented as "never binds" bound at exactly 400,000 points.
- **Check every gate is reachable under the configured budget.** With 200-step episodes, 0 of the arms completed a
  curriculum stage; with 24-step episodes, 7 of 7 did.
- **Check that a reweighting does something.** The effective sample fraction (Σw)²/(N·Σw²) was 0.992: a no-op.
- **A fixed margin saturates; gate a lever by its scale.** A Euclidean margin of 1.0 in d = 64 saturated after
  imprinting about 9% of the target variance. A mean over d diluted one loss 64-fold and let the regularizer
  dominate at about 300 times its intended ratio.
- **A speed optimization can change the science.** Cutting a regularizer's random projections from 1024 to 256 made
  2 of 4 splits collapse (effective rank 4 to 5). Require an identical loss trajectory at a fixed seed.
- **Keep train and evaluation in one regime.** Evaluation ran without the 6144-node cap used in training (about
  twice the reach); a hash guard was stored and never asserted. Persist every preprocessing parameter and assert it
  at load.

`references/probes.md` (inert knobs) holds the arithmetic.

## 6. Comparisons: one factor at a time

- **Change one lever at a time near a collapse basin.** Changing the regularizer weight together with another fix
  could re-open a collapse basin met at step 360. Gate init and metric changes separately, with arms that do one each.
- **List every factor that differs between A and B before reading the gap**: checkpoint, steps, data seen, input
  budget, flags, readout, evaluation extent, metric. Add a matched intermediate arm for each extra factor.
- **Confounds that looked like model effects:**

| Looked like | Was | Test |
|---|---|---|
| a model effect of input density | the representation was built from a 1.5% (and a 0.06%) subsample; depth matching flipped one verdict | thin the richer arm to the poorer one's budget; measure the saturation curve (2, 4, ..., 64 per unit) |
| thin versus dense input | two different checkpoints (outputs on the same items had cosine 0.007) | identity by content; a third arm, dense thinned back to thin depth |
| a peak at one spatial scale | a small window starved by its fit/test buffer; at full extent it kept rising past that scale | evaluate at full extent with blocked folds |
| a new version worse than the old | 15k against 8k steps, a key feature silently off | matched steps, feature on, then compare |
| a new architecture much worse | two different metrics on the two runs, and a metric that scored good and bad runs alike | same metric, both runs; score a known-good and a known-bad run first |
| a component that does nothing | the default read-out bypassed it | score every readout separately |

- **Suspiciously uniform or clean numbers are bugs until shown otherwise.** Identical SDs down a column, three arms
  equal to three decimals, a too-smooth validation curve, identical peak memory across models: check that
  different checkpoints loaded, that the SD is over folds, and that held-out data is held out.

`references/confounds.md` has the decomposition procedure and the "new model looks worse" sequence.

## 7. Decide and record

- **Redesign when the objective is degenerate; tune when it is alive but weak.** If every variant sits at the
  trivial floor or the variants are bit-identical, rerunning cannot help. If the loss is below the floor but
  selectivity is small, tune the levers that inject the missing signal.
- **Name the verdict**: inconclusive (could not answer; say what was missing), negative (answered no), dead (the
  measurement was degenerate). Each comes with a next action. Keep reversals visible, in order.
- **Scope every null to what was tested.** For example, "X does not help at scale [s]" is the finding; "X does not
  help" is a misreading.
- **Do not fix a crash by loosening the check.** Loading with `strict=False` would have run the wrong readout and
  corrupted the evaluation silently; the fix persisted the architecture and asserted it.
- **Pre-stage fallbacks as written configs**: collapse means restart from an earlier checkpoint with a stated
  change, written before the run.

## 8. Check before reporting

1. Every number quoted came from a log or result file you opened; name the file. "If the clause is 'the tool
   printed it', that is not a receipt."
2. `windowed_medians.py` on every log behind a trend claim; zero problems, or the problem named in the report.
3. The logged-name table exists for every metric the verdict rests on.
4. The trivial floor and the collapse margin are computed for each loss term the verdict uses.
5. For any comparison, the list of differing factors is written out and each extra one is matched or named.
6. Look at the curves yourself, raw and smoothed, with the floor drawn in.
7. Say what was not checked (no twin, no content probe, extent not matched) and what the verdict therefore cannot
   claim.

## 9. What was thrown out, and what replaced it

| Thrown out | In the author's words or the record | Replaced by |
|---|---|---|
| reading `tr[-1]` | "reporting a false collapse twice in one session cost the user's trust" (record) | trailing windowed medians, a comment forbidding the last-row form |
| effective rank as the collapse verdict | "blind by construction" (record) | twin margin plus held-out trend, rank as a canary |
| judging runs by curves | "think of it with scores" | downstream, floor-subtracted scores |
| more anti-collapse weight | "anti-collapse weights and pool sizes cannot repair a degenerate objective" (record) | a change of objective form, data targets on the deployed features |
| rerunning a dead ladder | "the fix is a redesign, not a rerun" (record) | floor arithmetic, then redesign |
| a better plot to show invariance | "the figures were structurally incapable of showing one" (record) | paired perturbation probes with a null |
| look-alike variants taken at face value | "r3/r4/r5 literally have the same umaps, what's the bug?" | weight hashes, CKA, pixel comparison |
| near-equal arms accepted | "super similar!! ... there might be a bug!" | checkpoint identity check |
| several levers in one restart | "can re-open the collapse basin" (record) | one change per staged restart |
| `strict=False` to stop a crash | "would run the wrong readout and silently corrupt" the metric (record) | persist and assert the architecture |

## Reference files

- `references/reading-logs.md`: tracing logged names, windowed medians, weighted and self-referential losses,
  the per-step logging checklist, the script's options.
- `references/floors-and-collapse.md`: closed-form floors, the collapse margin, effective-rank caveats, target
  rank, shipped-layer checks, liveness audit, batch-statistic pool size.
- `references/probes.md`: content, nuisance and batch probes, paired perturbation probes, identical-output check,
  positional-encoding band, inert-knob arithmetic.
- `references/confounds.md`: one lever at a time, matched intermediate arms, depth matching, extent, steps,
  checkpoint identity, the "new model looks worse" sequence, verdict labels.

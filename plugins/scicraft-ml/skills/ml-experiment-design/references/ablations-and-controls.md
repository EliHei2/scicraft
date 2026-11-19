# Ablations and controls

## 1. The order of steps

Write the ladder before any training, with a parameter count per step:

| Step | Content | Tabular foundation model |
|---|---|---|
| 0 | no-learning floor | per-table descriptive statistics, or PCA of raw features, into the same probe |
| 1 | training-free version of each learned module | mean of raw neighbor features in place of a learned set encoder |
| 2 | reference | previous working model at its tagged commit, checked out in a worktree |
| 3 | additive steps, one component each | + column attention, + row attention, + the pretraining prior |
| 4 | main model | the configuration you would bet on |

- The main model is the best bet. Ablations, sweeps and tests run in parallel with it, not before it.
- A learned extra module must beat its training-free version. A high mean-pool baseline is "a HIGH baseline any
  learned aggregator must beat."
- Evaluate all steps. Render the expensive pictures (embedding maps, UMAPs) for the main model and the baselines
  only.
- When results are bad, the ablation ladder is not the first tool: diagnose first (`training-diagnostics`).

## 2. One arm per component

- Before coding, list each component with the claim it supports and the arm that tests it. Keep the arms in an
  `ablation/` config folder, one file each (`references/configs-and-sweeps.md`).
- Each arm removes or replaces exactly one thing. Label it as the intervention ("-column attention",
  "mean pooling"), at most four words.
- Do not change a second axis inside an arm. When the author was offered a different layer count per model size,
  the author declined: "that would introduce another point of comparison, let's keep all the same."
- A scalar change with a plausibly large effect is its own arm. From a design hand-off: "Run this as its own arm.
  It is a scalar change with a plausibly large effect and it will confound every other arm if bundled." Its
  falsifier names the follow-up: if it fails or destabilizes, sweep three values rather than assuming one.
- Near a known instability, change one lever at a time and gate each separately with its own control arm (init
  only, metric only, both).
- Cut a component you cannot afford to ablate.

## 3. Controls

**The control for an ablation is a trained model, matched on data seen.**

- Same recipe, same seeds, same step budget as the arm. Compare at the same number of samples, rows or tokens
  seen, not at the same wall time or epoch count.
- In a revision, the control is trained with the same recipe, seed and number of steps as the arms, and every arm
  is reported against it.
- Never use an untrained twin as the comparison for an ablation. When an untrained-twin comparison was offered
  beside the trained arms, the author's answer was "give me the trained ones!"; later reports dropped twins unless
  a reviewer asked.

**Random-init twins as floor rows.** A twin answers a different question: does training beat a random network of
the same architecture? When it is reported:

- name it `<parent>-rand-init` and match it by the exact parent name (substring matching once routed the wrong
  row);
- give it its own seed, and use several draws when the twin is a floor (two twins rebuilt from one descriptor at
  one seed are one twin);
- score the exact initialization as its own row too: a trained model can beat a random network and still be worse
  than where it started, so "pretraining beats random init" is two claims;
- leave the scoring protocol to `ml-evaluation`.

**Destroyed-input controls.** A control that keeps the pipeline and destroys the signal (position only, features
shuffled across rows, labels permuted within fold groups) gates the whole family. If it scores at or above the
baseline, no arm in that wave can be read.

## 4. Ablate the shipped recipe

- Byte-diff each ablation family's base config against the config you ship. A whole wave once ablated a
  degenerate default; a control inherited a setting the flagship did not use.
- When the recipe changes, re-run claimed ablations under the new recipe and drop the ones that no longer ablate.
- An arm must test what its name says. A "why not a plain transformer" arm once still used the multi-level readout
  of the full model, so it tested nothing.
- `scripts/ablation_audit.py` resolves every arm against the base and reports arms with no difference, arms
  identical to each other, and arms built on another base.

## 5. Isolate with a 2 x 2

When two factors move together (architecture and context size, model and preprocessing), cross them:
{A, B} x {setting 1, setting 2}. A at 1 vs A at 2 isolates the setting; A at 2 vs B at 2 isolates the
architecture. A five-step ladder in which every step shared one context size could not test reach at all; the
decisive comparison had "already existed and was demoted".

## 6. Noise before verdicts

- Every wave carries one config-identical replicate arm: the same config, another seed. It is the noise unit of
  that wave and is not borrowed from another wave.
- |difference| below 3 replicate SDs is printed as a tie, with the SD. "No significant change" never means "no
  change".
- Claim a component only if full minus ablation exceeds max(per-task SE, |control seed 0 minus control seed 1|)
  and the sign is stable between two checkpoints (two steps fixed in advance).
- Single-run arms are powered for large effects only; say so in the caption.
- Step-match or step-correct, and stage-match, every comparison.
- One dataset cannot separate "the architecture does not help" from "the model is data-starved". Plot the score
  against the number of independent added datasets (blocked units on the x-axis). For tabular foundation models
  this is the curve over the number of pretraining tables; evaluation tables that share a prior with training
  make the evaluation circular.

## 7. A minimal decisive set

| Tier | Contents |
|---|---|
| 0 | gates before any long run: data ordering, validity of the stopping rule with destroyed-input controls run through the stopping metric, memory sizing on the densest batch |
| 1 | at most five decisive experiments; each could end the paper, has a written "falsified if", and names the lever if it fails |
| 2 | a necessity table (one arm per component) with one replicate |
| 3 | scaling; a short run of the largest model is not a scaling point |

Keep the program as a table in the ablation README:

```
| # | claim | arms | falsified if |
| 1 | the learned aggregator uses context | full vs no_context.yaml vs training-free neighbor mean | full within noise of the training-free version |
```

Add pre-staged conditional arms with an explicit trigger and the expected signature, so they are run on evidence
and not on mood. Use the theory's one numerical prediction as a cheap test: evidence, not rationale.

The four controls a reviewer will demand and that cost almost nothing (scored per `ml-evaluation`): a supervised
ceiling, smoothing or trivial baselines, a leakage probe on an identity covariate (source, instrument, table id),
and a label-permuted floor per method.

## 8. Reviewer questions at design time

For each design choice write a row:

| Choice | Strongest reviewer question | Answer | Evidence type |
|---|---|---|---|
| column attention | why not a plain MLP over concatenated features? | arm `no_column_attention` | planned arm |
| pretraining prior | why not gradient-boosted trees fitted per table? | trees as a fit-on-eval comparator row | comparator |

If a row has no answer from theory, literature or a planned arm, change the design. Running the questions past
critics is useful; give them the code and the plan, not your conclusion, and keep critics read-only on the source
(`research-design-review`).

## 9. Do not spend the budget on loss weights

- A family of loss-weight sweeps returned ties within ±0.01; a two-line recipe fix gained more than extra steps or
  extra capacity at a fraction of the GPU hours. Spend arms on architecture, input masking and data ordering.
- Before proposing an experiment, look its lever up in the settled-levers index: lever, verdict (HELPS, HURTS,
  NULL, NEVER-ISOLATED, NEVER-RUN), receipt, confidence. A new proposal cites a defect in the earlier control or is
  a confirmatory seed of a single-run effect. Report absent levers as gaps.
- Protect what already works: a shipped masking ratio within 8% of the best scheme was not worth a sweep. Measure
  before sweeping.

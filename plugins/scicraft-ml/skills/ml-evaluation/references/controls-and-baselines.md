# Controls and baselines

Every headline number is a gap over something. The controls below say what the gap is over. They run
through the same frozen code path as the method, in the same pass, and they appear in the table.

## 1. Floor, ceiling and null

| Control | What it is | What it answers |
|---|---|---|
| floor | the same pipeline trained on inputs whose informative structure is destroyed (feature-shuffled, column-permuted, label-permuted, position-only) | is the signal in the content, or in the geometry the pipeline imposes? |
| ceiling | a second training seed (or a replicate), and an oracle input through the same estimator | how much would a perfect or repeated model score? |
| null | row-shuffled scores, or label-permuted within fold group on the method's own features | what does chance score under this metric and these folds? |

- **Report main minus floor, and state whether it clears the two-seed band.** A raw cross-feature-set
  correlation rose steadily, and much of it was shared geometry; the pre-registered metric was the gap
  over the feature-shuffle floor. One two-seed spread was larger than every difference between model
  variants, and a bar of "gap below 0.05 is noise" was written into the design.
- **The decision script refuses to certify when the floor is absent.** With floor runs missing, the
  decision script returned NaN for every variant and rejected all of them, which was correct.
- **A chance-corrected zero is not chance until a floor shows it.** Under leave-one-group-out folds,
  label-permuted floors sat at -0.10 to -0.19 on a corrected scale. When held-out groups lack classes,
  1/K is the wrong floor.
- **Run destroyed-input controls through the stopping metric before trusting it.** A split-half
  statistic used to stop training was maxed by a position-only control; it rewarded smoothing.

Tabular form: for every headline arm, train a column-permuted and a label-permuted control and a second
seed.

- **For imputation or reconstruction, add a copy null and an abundance null**: predict each held-out value
  from its own observed copy, or from its mean abundance. A copy null once beat every model on an imputation task.
  Such a task does not rank the models: report it with the number of the null and say so.
- **A trivial covariate through the same probe is a row too**: a one-hot of the slide, the instrument or the
  table id. One task lost close to half of its distance above the floor to such a row.

## 2. The cheapest baselines

- **Include a linear baseline and a training-free baseline through the identical metric.** An audit
  named the linear PCA baseline "the decisive missing control": the shuffle floor tested content over
  geometry, not "nonlinear learned model over linear". Tabular form: ridge or a gradient-boosted tree on
  raw columns, and a kNN.
- **A learned extra module must beat its training-free version.** A self-excluded neighbor mean
  (about 20 lines of code) was the control a learned context module had to beat. Mean pooling at a
  large scale was a high baseline that any learned aggregator had to clear.
- **A counts or PCA control that beats a model is a result about that model.** It goes in the table.
- **Pick comparators by a mechanistic reason.** Name what each comparator is free to do that the others
  are not ("the only comparator free to disagree about the units themselves"). Comparators are the top
  published models whose data are available plus the two or three most-cited classical methods; a pet
  baseline is not a comparator.
- **Always include the previous working model as an arm.** "Does the redesign beat where we started?"
  is the first question. Land the cheap flat version first to get the before number.

## 3. Regress the baseline out and test what is left

A gap of two separately computed scalars (model minus baseline) cannot tell a new subspace from the same
subspace recovered slightly better. When training levers push toward the baseline's subspace, test
directly:

1. Residualize the baseline features out of the representation (OLS on the train fold, applied to both
   folds).
2. Score the residual with the same probe and folds.
3. Score the residual against its own null (target permuted within the train fold).
4. If the residual scores at its null, report no win on this task, however healthy loss curves,
   effective rank or reconstruction look.

Also run the **concat arm**: raw features beside the representation. If concat equals raw, the
representation is redundant on this task. Then look for the task the raw features cannot reach: disjoint feature subsets,
unseen schemas, transfer across feature sets. Claim that capability.

`scripts/residual_probe.py` runs baseline, embedding, concat, residual and residual null under
leave-one-group-out folds. On the synthetic check shipped with this skill, an embedding that was a
rotation of the baseline scored a residual of 0.47 against a null of 0.53; an embedding with one extra
informative direction scored 0.79 against 0.47.

## 4. Oracle inputs through the same estimator

Before blaming the method, check the metric's ceiling: feed perfect inputs through the identical
estimator.

- Generate oracle inputs (noise-free, drawn from the true distribution, the reference's own outputs)
  and run the identical pipeline.
- If the measured value lands on the oracle value, the residual is a sampling limit of the estimator.
- If the oracle scores below real data, the metric is broken. Change the axis, and first confirm the old
  number reproduces exactly on the new code ("change of axis, not of answer").
- When the question is "is our approximation legitimate?", hold everything else fixed so only the
  operator is on trial, and bin by the nuisance variable. Series that collapse onto one curve show that
  variable is the only driver.

ML form: the oracle row of an ablation table (a ground-truth retriever, true labels into the downstream
head).

## 5. Random-init twin and exact init

- **Score the exact initialization as a row**, and make the random-init twin a method row with its own
  seed, routed and named after its parent (`<parent>-rand-init`, matched on the exact name, never a
  substring). A trained model can beat a random network and still be worse than where it started.
- **An initialization derived from data is its own claim.** A data-derived embedding table explained 31
  to 66 percent of the twin margins, so "pretraining beats random init" became two claims and needed an
  init-matched twin.
- **Two twins rebuilt from one descriptor at one seed are one twin**, an n = 1 floor. Use several twin
  draws and print their spread.
- When a twin adds nothing to the argument, it can leave the main table; keep it in the appendix with
  its number.

## 6. Positive and negative controls for a claim

Define every new claim as a test with an upper anchor and a lower anchor: "the claim holds if and only
if fragments look like real units and far unlike random masks, consistently across classes and across
two clustering methods". Add an internal negative control that should not move (an off-pathway column,
random gene sets centered at 0), and plot it in the same panel. If the control shifts but does not flip,
say exactly that.

Run a positive control through a test before trusting its null. A differential-expression method gave
no gene of the panel even for a textbook positive contrast, so its significance was miscalibrated on that
data and its nulls meant nothing.

## 7. The verdict rule

A column carries a model claim only if the best shipped row beats every random-init twin, every floor
and the raw-feature baseline. When a pre-registered endpoint is missed, say so where the result is
reported.

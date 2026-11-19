# Nulls, controls and circularity

A significance mark is a claim about a null. Measure the null before drawing the mark.

## The null

- **Test against the correct null, not against zero.** A matched null had mean +0.10, not 0; dots marked
  significant against zero overclaimed. Build the null matched on the confounders (expression level, proximity,
  depth, size), report its mean, and test the difference from it. In machine learning: random features of the same
  dimension, a random-init twin of the same architecture, a shuffled-label probe.
- **Measure the null's false-positive rate first.** Run the test on random sets or negative-control sets. A
  permutation null was anti-conservative because one group had larger units: it flagged many random feature
  sets. Against size-matched random sets the same effect was no longer significant. The gap between a label-permutation null and a matched null is the
  size of the confound.
- **Permutation and matched nulls answer different questions.** A label permutation asks whether labels matter
  at all; a matched (competitive) null asks whether this set differs from comparable sets. Use the matched one
  when the claim is specificity.
- **A chance-corrected metric's zero is not chance.** Permuted floors of one chance-corrected recall sat at -0.10
  to -0.19. Measure the floor; do not assume it.
- **A "null" control can carry signal.** A negative control turned out to sit next to the structure tested; the
  real null was a random set drawn away from it. Check that the negative control actually sits at the null.
- **Measured values only.** No interpolated placeholder, no estimate drawn as a hollow mark, no failure drawn as a
  measurement (see `data-figures` for failure marks).

## When the absolute effect depends on the null

- **A one-sided test needs its direction fixed in the plan** before the data are seen, applied to every comparison
  alike, and named in the caption. Choosing the side after seeing the sign halves the p value for free.
- **In a significance map, color carries the effect size and a dot carries significance.** Neither stands in for
  the other: a saturated color is not a significant entry, and a dot on a pale entry is a small significant effect.
- **When the absolute effect moves with the choice of null but the ranking holds under every null tried, state
  the claim as a ranking.** In one audit a cross-method claim survived the positive control but not the
  expression-matched null, so the absolute significance was dropped. The claim kept was relative: which method is
  positive, which inverts, which is neutral, with the controls flat. A headline P value became a relative claim
  this way.
- **Test on the richest model you have.** Refitting a model on a matched subset to remove a confound left it
  undertrained, and the effect shrank to less than half of the full model's. Do the matching in the test (a
  matched null, a matched comparison set), never by refitting on fewer units. In machine learning: do not retrain
  on a down-sampled split to equalize a nuisance variable; match it in the evaluation.
- **Build the alternative panel beside the original** and leave the original untouched until the author chooses.
  Record each dead end (an analysis that was tried and failed) with a "do not re-propose" line so it is not
  retried.

## Controls

- **Every new metric gets an upper and a lower anchor**: an oracle or known-good input and a random or shuffled
  input. "Real cells as positive control and random masks as negative control": the claim holds only if the method
  is near the positive anchor and far from the negative one, consistently across subgroups and settings.
- **An internal negative control goes in the same panel** with the same statistic: a row of off-pathway items,
  random sets centered at 0, a secreted class beside a contact class. If the control shifts but does not flip, say
  exactly that, and phrase the result as specificity.
- **Run a positive control through the same test before trusting a null result.** A differential-expression
  model gave no gene of the panel even for a textbook positive contrast, so its significance was miscalibrated on that
  data and was not used.
- **The ceiling.** Before blaming the method, feed perfect inputs through the same estimator. For "is our
  approximation good?": hold everything else fixed, draw n uniform points inside the true shape (n = the item's
  real count), run the identical estimator, and plot measured against ceiling binned by the nuisance variable. If
  measured is near the ceiling, the residual is a sampling limit. If the ceiling sits below real data, the metric
  is broken; change the axis (for example the feature set) after confirming the old number reproduces exactly. In
  machine learning this is the oracle row of an ablation table.
- **Planted truth.** Before a metric goes into a figure, run it on inputs with known answers: planted fractions
  (0, 15, 30, 45, 55, 80% foreign signal), one feature scaled by 10, degenerate geometry, the same seed twice, the
  output schema on failure paths. One audit found a seeded run that was non-deterministic (an unordered group-by
  fed the seeded permutation), a score with a dead zone (every ratio at or below 1 scored exactly 1.0), and a
  "soft" variant that was not the published metric (scaling one feature by 10 moved the soft score while the hard
  score stayed put).

## Before a win reaches a figure: the adversarial checks

A claimed win that looks large is audited before it is drawn. Required:

1. a permutation or label-shuffle floor (one claim's floor equaled a large share of its gap);
2. a recompute under a common label set (the same claim flipped sign under forced common labels);
3. a concentration check (a handful of label pairs carried nearly all of it);
4. effective n under clustering or blocks, and a block test (not significant in that case);
5. a spatial or block bootstrap.

The outcome is one of three, recorded with the date: keep the claim; demote it to mechanism or illustration with
no significance marks; retract and replace it with a confound-free stratum. Dead rescue paths are written down with
"do not re-propose".

**Label lottery.** Before claiming that two methods disagree on some items, rerun the labeling pipeline on one
method with another seed. A seed change of one method reproduced a "spectacular" per-class flip for several times as
many items as the between-method count, so the flip was noise. In machine learning: compare the between-model gap
with the seed-to-seed gap.

## Circularity

**A model's own objective cannot crown it.** List the model's training signals. For each metric in the figure,
mark it circular, semi-circular or independent:

| The metric | Status | Example |
|---|---|---|
| is the training objective, or a monotone function of it | circular | a contrastive model scored on the similarity it was trained to maximize; a student model scored by its agreement with the teacher it was distilled from |
| shares an input or a label source with the model | semi-circular | an evaluation on pseudo-labels the model produced; a reference derived from one of the compared methods |
| uses a signal the model never sees | independent | distance to a stained boundary the threshold never sees; a downstream task on held-out labels |

- Lead with the independent readout. Keep one caption line that bounds the semi-circular ones ("state mechanism,
  never independent validation").
- **Ground truth is external to every compared method.** A data-driven "genuine" set was weak and mildly circular
  and was replaced by a curated, literature-grounded set. Evaluating every level against a corrupted directory
  would have been circular; the clean reference was used.
- **Never use your own method as the reference**, and drop a reference that is blind to the category being
  measured (one imaging reference badly under-detected immune cells, so it had "no truth to recover" there). A weak labeler is not ground truth outside the domain it was validated on.
- **Validate on a modality the method never uses as input.** List input signals and validation signals; they
  must be disjoint.
- **Write the non-circularity argument down** in the figure notes, one line per metric.

## Reporting a negative

- **A null is a result.** Record the hypothesis, the test, the ground truth, the direction, the reason it failed,
  the scripts and a "do not retry unless X" line. An exhaustive screen of every candidate that left only the known
  axis was reported as "un-cherry-pickable".
- **A powered null reports its interval and its minimum detectable effect.** A control is tested for its own
  stability first; one arbiter split cases at chance and swung with its own parameter, so it was "disqualified,
  not merely null".
- **Ask whether the analysis could detect a real effect at all** before chasing a weak one: a positive control or
  a power argument. When the signal sits at the detection floor, reframe as comparative power (for example ΔAUC of
  a probe over a nuisance-only baseline, with block cross-validation intervals).
- **Turn an honest negative into a method-justification panel** when it is one: "our test against the
  alternative test" on the same positive and negative controls. A confound gets its own panel when a reader would
  otherwise suspect it (a mask-size confound with Spearman ρ = +1.00 was shown and the claim rejected).
- **A result that contradicts a claim changes the claim.** A weak or mixed result goes to the appendix with its
  number, never out of the record.

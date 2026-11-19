# Matching and identity

When two numbers differ, exactly one factor may differ between them. This file covers the factors that
silently differed in real comparisons, and how to prove what was compared.

## 1. List every differing factor

For any A-against-B comparison, write the list before reading the numbers: checkpoint, training steps,
data seen, input budget (depth, context rows, features), flags, readout layer, decision stage, unit of
aggregation, preprocessing, hardware. Then add arms that change one factor at a time.

- **A matched intermediate arm splits a difference into its parts.** "Thin against dense" turned out to
  compare two different checkpoints. The fix was a third arm: the dense output thinned back to the thin
  budget. Published to matched then measures the checkpoint; matched to dense measures the budget.
- **A 2 x 2 design isolates one factor per comparison.** A five-variant ladder could not test context
  reach because every variant shared one window size; {small, large model} x {small, large window}
  separated reach from hierarchy.
- **Reconcile steps and silent flags before trusting a bar.** One model was trained far longer than the other,
  and the shorter run had a feature switched off without a warning: "re-run matched steps with the feature on before
  trusting any bar".
- **Change one comparison axis at a time.** Across a size ladder, vary only width (or the agreed depth
  set); per-size layer counts were rejected because they "introduce another point of comparison".

## 2. Depth, budget and step matching

- **Report the input budget behind every number.** An export capped crops at training density, so every
  exported field was a subsample of 1.5 or 0.06 percent of the data, and nobody had said so.
- **Measure the real ceiling and the saturation curve.** Score the baseline at full input against itself
  (split-half), then at budgets 2, 4, 8, ..., 64 per unit. The full-input ceiling measured 0.625, not 1.0;
  reliability saturated past about 32 per unit.
- **Match by design, not by post-hoc thinning, where you can.** The latest rule from that work: compare
  models at equal compute, tokens or context rows by design. Subsampling a richer arm after the fact to
  manufacture or erase a gap is a trick. Where depth confounds a comparison, show the gap in every depth
  bin or choose a stratum where the confound is constant by construction; if the comparison is still
  monotone in depth, drop the claim. When matching is the only option, thin multinomially with the model,
  units, labels and folds held fixed, and report published, matched and full side by side.
- **Ablations are compared at the same data seen.** Compare each arm with its control at roughly the same
  number of samples or tokens seen, trained with the same recipe, seed and step budget. Match on data
  seen, not wall time.
- **Report depth-sensitive metrics as depth artifacts when methods differ in depth.** A method that
  captured more items per unit won every recall-type metric through depth alone, while a metric that
  does not depend on depth gave no such lead. Show items per unit next to every recall-type metric.
- **A short run of a large model is not a scaling point.**
- **Prefer more seeds at the same budget over a higher cap**, because more seeds stay in distribution.

Tabular form: compare models at matched numbers of context rows and features, and plot score against
context size before calling a gap a model effect.

`scripts/thin_to_budget.py` writes the matched arm: it thins every unit of the richer arm to the poorer arm's
total for that unit by a seeded draw without replacement, keeps unit ids and folds, and reports how many units
were thinned, left alone or dropped. Score the published, the matched and the full arm side by side.

## 3. Checkpoint identity by content

- **Verify identity by content, never by filename.** Hash the weights and the outputs. In one comparison
  of "two depths of the same model", a coordinate join at 0.0000 offset gave a per-row cosine of 0.007:
  the arms were different checkpoints.
- **Join on rows by key, and print the match rate.** A positional join scored the wrong rows' embeddings
  89 to 99 percent of the time and was printed as science. In another pipeline, labels landed on the
  right row 0.065 percent of the time because one side indexed before a filter and the other after; the
  mis-join produced no error. Assign the row index on the raw table before any filter, join on it,
  refuse positional fallback, and assert an exact invariant (rows pointing at discarded items = 0); a
  ratio guard of 0.9 passed a 0.25 percent offset.
- **Test fixtures interleave the rows a filter drops.** Without them raw and filtered indices coincide
  and the bug is invisible to every test.
- **Check look-alike outputs.** Three variants produced identical-looking plots. The
  diagnostic hashed each variant's weights and computed linear CKA between outputs per readout: the
  default readout bypassed the varied component, so identical plots were expected there and the
  architecture showed only in the other readout.

`scripts/checkpoint_identity.py` hashes each array, joins pairs by key, refuses pairs below a match
rate, and prints linear CKA. On the shipped synthetic check, a rotated copy with shuffled rows read CKA
1.000 when joined by key and 0.062 when joined by position.

Linear CKA is biased upward in high dimension at low N: two independent random 500 x 32 arrays read
about 0.06. For claims of representational convergence, use debiased CKA against a shuffle-trained
null and a stitching cross-check, and name shared causes (same target, data, initialization) before
calling agreement a finding.

## 4. Readout, decision stage and units

- **Score every readout separately and list which one ships.** A regularizer acted on one layer while
  the shipped layer had no loss; the monitoring tripwire watched the student while the teacher shipped.
  Name the readout per deliverable.
- **Compare methods at the same decision stage.** A comparison used one method's raw argmax while the
  other method's labels were already thresholded; it was "inflated/unfair", and every downstream step
  was rebuilt. Read the writer code to see where the final decision is applied, quantify the share of
  rows it changes, and rebuild in order.
- **Units match between label and representation.** Group-level labels transferred and unit-level labels
  did not, because a bin's dominant class is a mixed label: a units problem, not a budget problem.
- **The readout unit can flip the verdict.** One method won every task on one unit and few on another. Report the unit and the pooling operator, and never rank one unit against another with a
  best-of across them.
- **Keep train and eval in one regime.** An evaluation stream had no cap while training capped at 6144
  items, a two-fold shift in reach. Persist every preprocessing parameter in the checkpoint and assert
  it at load; check that each guard distinguishes the cases it guards (a hash of the whole vocabulary
  was identical for two disjoint subsets).
- **Fix a crash without loosening the check.** A strict-load failure was fixed by rebuilding the right
  class and asserting the architecture, explicitly not with `strict=False`, which would have scored the
  wrong readout silently.

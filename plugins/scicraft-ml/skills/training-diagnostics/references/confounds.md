# Confounds and comparisons

## 1. One lever at a time

- Near a collapse basin, change one lever per staged restart, never live. Changing the regularizer weight together
  with another fix could re-open a collapse basin met at step 360. Init and metric changes were gated separately,
  with control arms that each did one: init only, metric only, neither.
- A scalar change with a plausibly large effect runs as its own arm: "it will confound every other arm if bundled."
- For a factorial question use a 2 × 2 design. A five-step ladder could not test reach because every step shared one
  crop width; {short reach, long reach} × {flat, hierarchical} isolates each factor with one comparison.
- Across sizes, vary only the agreed axis ("that would introduce another point of comparison, let's keep all
  the same").
- Keep the previous working model as an arm in every comparison: "does the redesign beat where we started?"

## 2. Before reading any gap between A and B

Write the list of factors that differ:

| Factor | How to verify it is equal |
|---|---|
| checkpoint identity | weight hash; outputs joined by item key; never the filename |
| training steps and data seen | step and sample counters from the log, not the config |
| input budget per unit | count inputs per unit in each arm |
| flags and switches | the resolved config each run echoed at start, diffed |
| readout | which tensor each evaluation read |
| evaluation extent and folds | same items, same folds, same scale |
| metric | same scorer code, same version |
| seed | at least one replicate seed per arm |

For each factor that differs and is not the one under study, add a matched intermediate arm that changes it alone.

## 3. Confounds met in real work

**Input depth.** An export capped inputs at training density, so every representation was built from a 1.5% or a
0.06% subsample of the available inputs. Matching depth by multinomial thinning flipped one verdict and left another
unchanged. The full-depth ceiling was measured below 1. A dense re-export raised split-half reliability of the
representation from near 0 to above 0.9 against a permuted null of +0.002, and reliability saturated past about 32
inputs per unit.

- Procedure: count inputs per unit for each arm; thin the richer arm to the poorer one's budget (multinomial or
  Bernoulli) with model, labels and folds fixed; measure the full-depth ceiling and a saturation curve (2, 4, ...,
  64 per unit); report the published, matched and dense numbers together.
- Prefer more seeds at the same density over raising a cap, since more seeds stay in-distribution.
- For in-context models, compare at a matched number of context rows and features, and measure performance against
  context size before calling a gap a model effect. Suggested, not yet tested in real work.

**Checkpoint mixups.** "Thin versus dense input" compared two checkpoints: on the same items, joined by coordinate to
0.0000, the cosine between the two outputs was 0.007. The fix was a third arm, the dense input thinned back to the
thin depth, so that published to matched measures the checkpoint and matched to dense measures depth. Elsewhere a
5.4-fold floor gap was "the checkpoint, not extent or density". A job directory named for one arm can hold another:
prove from logs which checkpoints exist.

**Window size and extent.** A score peaked at one scale in a small window because a fit/test buffer starved the
window; at whole-sample extent it kept rising past that scale. The windowed picture rendered as noise while the same
embeddings at full extent showed structure, and the windowed metrics missed a real regression that only the full
render exposed. Evaluate on the whole held-out set with blocked folds and enough units per fold; choose a scale that
leaves enough units for low variance. In tabular work, small benchmark subsets with starved folds do the same.

**Different step counts.** A new version at 8k steps was compared with the old one at 15k, with a key feature silently
off in the new one: "reconcile first: re-run matched steps with the feature on before trusting any bar." Step-match
or step-correct, and stage-match when a curriculum is involved. A short run of a large model is worth nothing as a
scaling point.

**Two rulers.** "Tower much worse" compared one metric near 0.2 for one run against a different metric near 0 for the
other. Run the same metric on both, and first check that the metric separates a known-good from a known-bad run.

**Validation across objectives.** A watcher compared validation loss across an injected loss term and issued false
kill decisions. Key comparisons on the config and validation-set hash.

**Readout.** The readout unit flipped a verdict (four of four wins on one unit, one of four on another). Report the
readout and the pooling operator; never pick the best readout per row.

**Silent config drift.** Five arms built an identical network because structural switches were left to defaults,
and switches left to defaults can silently drop features. Write structural switches explicitly into every config
and echo the resolved config at start.

## 4. Noise before verdicts

- Each wave of arms carries one config-identical replicate arm as its noise unit, never borrowed from another wave.
- A difference below 3 replicate standard deviations is printed as a tie, with the SD.
- One two-seed spread exceeded every difference between steps of a ladder.
- Suspiciously uniform numbers are bugs until shown otherwise: equal standard deviations down a column (check the SD
  is over folds, not seeds of one fold), three arms equal to three decimals (check they loaded different
  checkpoints), a too-smooth validation curve (check held-out data is held out: "is held out really valid held out?
  ... why is it such nice line tho?"), identical peak memory across different models.

`stats-reporting` and `ml-evaluation` cover how the final comparison is tested and reported.

## 5. "The new model looks worse": the sequence

From one regression episode, in order of cost:

1. **Same ruler?** Run the same metric on both runs at the same extent and scale.
2. **Same extent?** Evaluate or render both at full extent.
3. **Same readout?** Try the cheapest test that needs no retraining: switch the readout layer and re-predict.
4. **Is the shipped layer supervised and regularized?** Trace which tensors the losses touch.
5. **Same steps, same checkpoint identity, same input budget?** Section 2.
6. **Diff the code** against the last commit that worked.
7. **Decide and record.** A redesign that fails is recorded as a negative result, with its salvage steps
   written down.

## 6. Verdict labels

| Label | Meaning | Comes with |
|---|---|---|
| inconclusive | the question could not be answered | what was missing (for example floor runs never ran) |
| negative | answered, and the answer is no | the setting it was tested in |
| dead | the measurement was degenerate (loss at the floor, variants identical) | the redesign it implies |

A record may move between labels as diagnosis proceeds (one went from inconclusive to dead objective); keep the
history visible in order. Distinguish "deferred on cost" from "refuted on mechanism". A null is a finding when it is
scoped to the tested setting, and a weak or negative result stays in the record with its number.

Redesign when the objective is degenerate: every variant at the trivial floor, or variants bit-identical. Tune when
it is alive but weak: loss below the floor, selectivity small. Then tune the levers that inject the missing signal.

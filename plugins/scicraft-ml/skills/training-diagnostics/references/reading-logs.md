# Reading a training log

What to do between "the curve looks bad" and any statement about the run. The lead case is a self-supervised run
with a moving teacher; the same steps apply to a supervised classifier or an in-context model, where the noise is
smaller but the traps are the same.

## 1. Trace every logged name to its code line

Before interpreting a metric, find the line that computes it. Write the table into the diagnosis:

| logged name | file:line | tensor it reads | reduction | what it would read for a model that learned nothing |
|---|---|---|---|---|
| `loss_pred` | `train.py:412` | predictor output vs teacher target, unit vectors | mean over tokens and d | 0.5/d for a zero prediction |
| `cos_pred` | `train.py:430` | ... | ... | ... |

Why: a metric logged as a prediction "cosine" was computed one layer upstream of the loss and read about 0 for a
whole run. Every conclusion drawn from it would have been about the wrong tensor. The same audit catches:

- a reduction that changes the scale (a mean over d made one loss 64 times smaller than intended);
- a metric logged from the student while the teacher is what ships;
- a docstring that claims something the code does not do ("same grid as eval" over a pooling that was not the
  evaluation's). Trust the YAML and the source, never the prose.

## 2. Windowed medians, never the last row

Per-step training metrics are noisy. In the run that produced this rule, an effective-rank metric moved from 88 to
190 between adjacent logged steps, and the prediction loss from 5.5 to 7.4. Three consecutive last-row reads of
154, 125 and 111 looked like collapse; the trailing 2,000-step medians were 168.7, 168.7 and 169.1. The false alarm
was raised twice in one session.

The procedure:

1. Select one kind of row: training rows, or evaluation rows. Logs that mix both need a filter (`--where`).
2. Deduplicate by step. A resumed run replays steps; keep the last occurrence.
3. For each metric, take the median over the trailing window and over the window before it. The original runs used
   2,000 steps; choose a window that holds at least 20 logged values.
4. Set the change against the spread of the trailing window (the interquartile range). A change well inside the
   spread is not a trend.
5. Print the last row only for contrast, labeled as such.

```bash
S=<skill>/scripts
python3 $S/windowed_medians.py runs/a/train.jsonl --where event=none --keys loss loss_pred loss_reg effrank
python3 $S/windowed_medians.py runs/a/train.jsonl --where event=val --keys val_loss --best-min val_loss --min-points 3
python3 $S/windowed_medians.py runs/a/train.jsonl runs/b/train.jsonl --window 1000 --json medians.json
python3 $S/windowed_medians.py logs/metrics.csv --step-key iter --window 500
python3 $S/windowed_medians.py --selftest
```

Options: `--keys` (default every numeric column), `--step-key`, `--window` in steps, `--where KEY=VALUE`
(repeatable; `none` matches an absent key), `--min-points` (default 20; fewer values in a window is reported as a
problem and the exit code is 1), `--best-min` / `--best-max` (best value ever and the gap to it; use on evaluation
rows only, since the best row of a noisy training metric is noise), `--json`. A requested key missing from the log
prints `absent` and fails; it is never read as zero. Evaluation rows are sparse, so lower `--min-points` for them and
say so.

Medians of one run do not replace a replicate. To call a difference between two runs real, the noise unit is a
config-identical replicate arm (see `confounds.md`).

## 3. Trends need points

- No trend from fewer than 4 to 5 points, and none from the first ~10 steps. Five misreads in one session had this
  shape, and "the 2-3-point read is most seductive precisely when it confirms the thing you just fixed."
- Metrics judged only after warmup. A smoke run of a few hundred steps is a sanity check, never evidence.
- A default is not an observation. Never `.get(key, 0)` a metric and interpret the result. Print `absent`.

## 4. Weighted and self-referential losses

- **Warm-up weights.** When a loss weight ramps over the run, the total loss falls because the weight changes. In one
  campaign about 90% of the loss drop was the regularizer relaxing. Log each term raw, its weight, its value times
  weight, and its share of the gradient into the shared trunk. Never plot the weighted total as a learning curve
  across the ramp; quote the minimum together with the drift, with weight mass and effective rank beside them.
- **Moving targets.** With an exponential moving average teacher, the target moves with the model, and "teacher-
  relative losses fall when the target arrives, not only when the model improves." Pretext loss ran
  anti-correlated with downstream transfer in one campaign. Progress is read on fixed referents:
  - a frozen held-out probe set scored at every evaluation;
  - the random-init twin of the same architecture;
  - the exact initialization scored as its own row ("a trained model can beat a random network and still be worse
    than where it started").
- **Checkpoint choice.** Take the checkpoint by its held-out probe score, never the endpoint by loss. Fix the
  selection rule before looking, and report which rule chose it.
- **Validation loss comparability.** Validation loss compares only within one objective, one mask or augmentation
  distribution, and one held-out set identified by content hash. Three false kill decisions came from comparing
  validation loss across an added loss term; smaller masked holes looked better on validation and were twice as
  bad on the probe; a sampling cap applied upstream changed a validation set thought to be frozen. Build the validation set as a pure
  function of its specification and stamp its hash into every record.
- **Supervised and in-context models.** The same split applies: training loss under label smoothing, mixup or a
  ramped auxiliary term is not comparable across the ramp, and validation loss is comparable only on one fixed
  held-out set. Suggested, not yet tested in real work.

## 5. Guards and tripwires

- A guard that fires all run long carries no news; find out why it fires.
- A guard that cannot fire is not a guard. A collapse tripwire set to effective rank 8 of 64 never fired while the
  collapsed value was about 0.9 of 64. A content hash meant to tell two data subsets apart was byte-identical for
  both, because it hashed the shared array.
- A guard on the wrong tensor is not a guard: attach it to the layer that ships.
- Telemetry must never kill training: when logging fails, drop the record and keep training.

## 6. What to log per step

The logging that would have caught each failure in this skill, from step 0:

- each loss term raw, its weight, its mass (number of valid targets), and its trivial floor from the batch's own
  targets;
- `collapse_margin` (loss minus the loss at the constant solution);
- separation on a fixed probe batch: the mean resultant length of the normalized embeddings (near 1 means every
  vector points the same way) and the spread of class or cluster centroids. The author asked for both checks
  from the start, proper separation and no collapse: "these 2 are super essential";
- gradient norm per module, and the share of each term's gradient into the shared trunk;
- effective rank divided by d, as a canary;
- nuisance R² (position, density, dataset id) and the batch-id variance fraction on a fixed probe batch;
- the retained fraction of input data per step, when any cap can drop data ("a number nobody plots is a number
  nobody sees");
- the resolved config, code commit and seed at start.

Read all of it with windowed medians.

Before the first long run, write a one-page loss note: each term in math and in one plain sentence, its targets,
its negatives if it is contrastive, and its value at the constant solution. The author asked for "what exactly
each loss is and how it's computed, in concrete math, but human words", including "what are the negative
examples here?"

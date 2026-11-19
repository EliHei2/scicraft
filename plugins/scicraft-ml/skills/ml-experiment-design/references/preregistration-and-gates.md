# Pre-registration and gates

Two files govern a campaign: `PREREG.md` (what will be measured and how a row is chosen, frozen before scoring) and
`GATES.md` (every threshold and decision rule, read by whatever decides). Templates: `assets/PREREG_TEMPLATE.md`,
`assets/GATES_TEMPLATE.md`.

## 1. Why

In the source campaign the definition of the reported readout changed several times within days, the row-selection
rule changed repeatedly after data were seen, and the pick moved among rows with no significant paired difference.
The first item of its "if we started over" list was to freeze the measurement chain and the selection rule before
the first candidate existed.

## 2. PREREG.md

Sections, in order:

1. **Endpoint**: the primary measure and the headline count, with the row classes printed in the same table.
2. **Column classes**: rankable, diagnostic, void (kept but never ranked or bolded), each with the dated audit
   that classified it.
3. **Row classes**: frozen pretrained models, models fit on the evaluation data, baselines, controls.
4. **Tie band and win rule**: for example tie band = max(3 x sqrt(sd_A^2 + sd_B^2), 1 x training-seed SD); a win
   is a mean above the band and at least 2 of 3 training seeds individually above the comparator.
5. **Checkpoint selection**: one reported checkpoint per size, declared when its run or cooldown fork launches.
6. **Seeds**: training seeds per size, twin seeds, and which kind of SD each cell reports.
7. **Scoring protocol**: the scorer at the tagged commit, folds, probes (details in `ml-evaluation`).
8. **Firewall**: below.
9. **DEVIATIONS**: dated, append-only, honest when an item was not implemented.

Tag the freeze commit (`git tag prereg-v1`) before the first score file exists. Git timestamps are the receipt;
`scripts/prereg_check.py` verifies that no result file was committed before the tag.

## 3. The two-key firewall

- Key 1: a scoring manifest (config hashes x seeds x step list) committed before scoring.
- Key 2: a wrapper that refuses any (checkpoint, task) pair not in the manifest.
- Results are append-only and every result file carries the manifest hash.
- Allow one declared interim gate, quarantined under `results/selection/`.
- Tuning reads only training-side instruments (an anchor validation set, training logs, quick probes on cached
  held-out data named in advance).
- Watched creep paths: peeking mid-plateau, renaming after a relaunch, probe shopping, seed picking, arm promotion,
  drift of the anchor or selection set.
- When key 2 is not built, say so in DEVIATIONS and review the manifest against the emitted result files by hand.

## 4. Selection

- Benchmark at most 3 pre-named candidates, once. No argmax over kept checkpoints on the benchmark.
- Fix candidates by time or exposure (a step, a number of samples seen), never by score.
- The selection set is never the reported set. Comparator cells are frozen as published and not re-scored.
- Selecting your own variant for a headline is a selection step: report "selected from N variants by rule R".

## 5. Gate before launch

- **The cheapest measurement that could invert the plan comes first.** Run the zero-GPU checks (CPU probes at
  initialization scale, minutes), then a short smoke, then the long run. Effect sizes at initialization order the
  options; they do not predict trained behavior, so read a trained operating point before designing against it.
- **One keep or kill number, defined in advance.** Example from a redesign brief: adopt only if the design beats
  the bar, beats its own floor, and the architecture measurably matters; a falsifier of the form "the loss falls
  below the marginal entropy within 500 steps while the paired shuffled-input run stays pinned at it".
- **Write the STOP rule into the brief** for whoever runs the job: "report this number before proceeding".
- **Pre-stage fallbacks as written configs**: if collapse, restart from the step-5k checkpoint with the
  regularizer raised; if the output blurs, lower the temperature. Decided before, not under pressure.

- **Seed every gate.** A pre-launch gate that compared a real arm with its shuffled control ran unseeded, so its
  margin mixed the effect with seed noise. Call one seeding function (Python, NumPy, the framework, the workers
  of the data loader) at the top of every gate and smoke script, and write the seed into the gate's output.

## 6. GATES.md

Sections, in order:

1. **Timeline.** Fixed dates; nothing new starts after a stated date.
2. **Verdict bar.** What a pass is, stated per column.
3. **Noise bands.** Per-task bands; ties inside a band are ties.
4. **Kill rules** (training arms):
   - judged only after warmup;
   - sustained over 3 consecutive evaluations;
   - a health criterion co-signs (for example the collapse margin turning positive, a fatal in-process guard,
     a starving GPU below 0.60 busy); benchmark evidence alone may only steer;
   - never across a change of objective or config, with every comparison keyed on the config hash.
5. **Steer menu.** A list in order, one change per staged restart, never applied live.
6. **Smoke gate.** Sanity only: finite losses, memory within budget, every loss term carrying mass. Metrics are
   judged after warmup.
7. **Evidence bars.** Counts of evaluations required before a decision, with a degraded-mode clause when compute
   is short, and pre-registered null outcomes ("a four-way tie means X").
8. **Promotion.** A candidate replaces the incumbent only with no significant paired loss on any task and at least
   one significant gain; the incumbent stays on any ambiguity. The champion is a step checkpoint, never an
   endpoint. Name the residual risk (reading the benchmark daily is selection on reported tasks).
9. **Protocol constants.** Steering rows (`ARM-*`) can never enter a paper table (`BANK-*`); tables refuse mixed
   protocol stamps.
10. **Provenance gate** with its own self-test (for example a check that no held-out source appears in training).
11. **Storage**: archive before delete.

## 7. Operations that protect a campaign

- Never kill a running training job to make room for validation. Queue the better configuration at higher
  priority and let it take over.
- Never act on a scheduler reading taken within about 60 seconds of a submit or a kill.
- Never bundle an unrelated fix into a recovery.
- Protective guards fail closed on a read error.
- Gate the long run on measured GPU utilization: busy fraction defined as 1 minus the loader-wait fraction, median
  at least 0.80 to launch.
- Assume the agent session will die and the cluster must not care: watchers run as jobs with STOP files. Cluster
  mechanics belong to `cluster-jobs`.

- **Every operational incident becomes a numbered guardrail** in one file: the incident in one line, its cost,
  the rule and the check that enforces it. Read the file before any launch. Rules written this way stopped five
  repeats of one misread in the source campaign. The shape of that file is defined in the sibling skill
  (`project-structure/references/governing-documents.md`).
- **A gate is the numeric go or stop threshold of a short goal.** The short goal in the project's `GOALS.md`
  names the gate it must pass.
- **Flip a run's status in the registry in the same minute as the submit, the kill or the finish.** After any
  relaunch, confirm that each monitor is bound to the new job: a monitor with a job id typed into it stayed
  green for hours on runs that produced nothing.

## 8. Under a deadline

- Score existing checkpoints before training new ones; stop runs that do not answer the open questions.
- Commit to one recommended configuration.
- Use the cooldown of a WSD schedule as the deadline device: fork it at the latest moment the deadline allows.
- Gate any "first" claim on its interval (`ml-evaluation`).

- **Keep a late anneal fork as the device that guarantees a model.** Branch from the running checkpoint, decay
  the learning rate over a short final stretch, and evaluate that fork while the main run continues.
- **Find the binding stage by measurement before buying compute.** In the source run the data loader was the
  limit and the GPU was idle.
- **Stage one fallback override per failure regime in advance** (out of memory, a stalled loader, a collapse), so
  a failure at night costs one relaunch.

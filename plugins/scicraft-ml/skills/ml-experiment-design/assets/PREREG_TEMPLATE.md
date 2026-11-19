# PREREG: frozen before any new checkpoint is scored

STATUS: DRAFT until the freeze commit tagged `[prereg-v1]`. The tag must predate the first score file; git
timestamps are the receipt (`scripts/prereg_check.py`).

## 1. Endpoint

Primary: [the measure, for example mean rank among frozen pretrained models over the rankable tasks].
Headline count: [for example "leads or co-leads on at least N of M rankable tasks"], with fit-on-eval models,
baselines and controls printed in the same table.

## 2. Task classes

- Rankable: [tasks], classified by [dated audit].
- Diagnostic (reported, not ranked): [tasks and why].
- Void as ranking (kept, never bolded): [tasks and why, for example a trivial null beats every model].

## 3. Row classes

- Frozen pretrained: [models, ours included].
- Fit on the evaluation data: [models].
- Baselines: [raw features, PCA, classical methods].
- Controls: [label-permuted floor, random-init floor rows, destroyed-input controls].

## 4. Tie band and win rule

Tie band per task: max(3 x sqrt(sd_A^2 + sd_B^2), 1 x training-seed SD of [size]).
Win: mean above the band AND at least [2 of 3] training seeds individually above the comparator.
Our cell: mean over the [3] training seeds at the declared step; never best-of-seeds, never best-of-sizes.

## 5. Checkpoint selection

One size, one reported checkpoint: [the fixed step, or the cooldown fork declared at launch].
Selection instruments ([anchor set, quick probes]) are selection only and never appear in a reported table.
Fallback sentence for an undertrained size, written now: "[The largest model reached only N steps at the cutoff
and is reported as an in-progress capacity check in the appendix, not a scaling point.]"

## 6. Seeds

Training seeds per size: [S: 0, 1, 2; M: 0; B: 0]. Perturbation seeds kept separate: [list].
What each ± means, per cell type: [training-seed SD | SD over held-out folds].

## 7. Scoring protocol

Scorer: [script] at the tagged commit. Folds: [grouped by what]. Probe of record: [which]. Details follow
the evaluation protocol of the project.

## 8. Firewall

Key 1: scoring manifest [path] (config hashes x seeds x steps), committed before scoring.
Key 2: [wrapper] refuses any (checkpoint, task) pair not in the manifest. Results are append-only and carry the
manifest hash. One declared interim gate: [which], quarantined under `results/selection/`.
Watched creep paths: peeking mid-plateau, renaming after relaunch, probe shopping, seed picking, arm promotion,
drift of the selection set.

## 9. Adversarial risks (pre-registered)

One row per way this campaign could publish a win that is not there. Each check is fixed before scoring.

| Risk | Why it is live | Check |
|---|---|---|
| [selection on the test benchmark] | [the choice of checkpoint, probe or seed could be made after scores are seen] | [the rule and where it is frozen] |
| [a control borrowed from another wave] | [it was trained under other settings] | [controls rerun under this wave's config hash] |
| [a metric redefined after data] | [the first definition gave an unwelcome number] | [the definition and its code hash are in section 1] |

## DEVIATIONS (dated, append-only)

- [YYYY-MM-DD]: [what changed, why, what it affects, and whether an item was not implemented].

# GATES: every threshold and decision rule of [campaign], in one place

Whatever decides (a person, a script, an agent) reads its constants from this file. Constants inside running
watchers are not refactored mid-campaign; where they differ, the mapping is written here.

## Timeline

[dates of each gate]. Nothing new starts after [date]. Freeze: [date].

## Verdict bar

PASS = [one checkpoint at or above the bar on every reported task] AND [rank condition]. Stretch targets are
tracked separately and are not the bar.

## Noise bands (ties inside a band are ties)

Per task: [band]. Replicate pair: |control seed 0 - control seed 1| per task once it exists.

## Kill rules (training arms)

Judged only after warmup ([steps per size]), sustained over 3 consecutive evaluations, and co-signed by a health
criterion. Benchmark evidence alone may only steer. Never across a change of objective or config; every comparison
is keyed on the config hash.
- [health criterion 1, for example the collapse margin above 0]
- [health criterion 2, for example GPU busy fraction below 0.60]
- [any fatal in-process guard]

## Steer menu (in order, one change per staged restart, never live)

1. [change and its value]
2. [change and its value]

## Smoke gate

Sanity only: finite losses, memory within budget, every loss term carrying mass. Metrics are judged after warmup.

## Evidence bars

[N evaluations per arm before a decision]. Degraded mode when compute is short: [the bar binds on evidence counts,
not steps]. Pre-registered null outcome: [a tie means X].

## Promotion

A candidate replaces the incumbent only with no significant paired loss on any task and at least one significant
gain; on any ambiguity the incumbent stays. The champion is a step checkpoint. Residual risk: [name it].

## Protocol constants

Steering rows are named `[ARM-*]` and can never enter a paper table (`[BANK-*]`). Tables refuse mixed protocol
stamps.

## Provenance gate

[the check that no held-out source enters training], with its own self-test run before each first submission after
a change to the gate script.

## Storage

Archive before delete. [quota and what is kept].

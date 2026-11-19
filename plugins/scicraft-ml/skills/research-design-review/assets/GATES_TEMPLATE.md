# Gates for the design round: [topic]

Status: LOCKED
Date: [YYYY-MM-DD]
Topic: [topic] gates
Written before any variant is built or any score is read. Amendments are dated and append-only below.

## G0. The gating measurement (runs first; can stop the whole round)

Measure: [the one cheapest number that could invert the plan. Usually the trained operating point: the value
of the target loss term in the last [n] steps of the shipped run, read from its log, against its trivial
floors.]
Command: `[exact command]`
STOP if: [condition, e.g. "the trained loss is already at or below the best per-group constant floor"]. Report
the number before anything is built.

## G1. Equivalence (before anything is submitted)

With every new switch off, the shipped configuration reproduces [the loss curve and final loss terms / the
outputs] of [reference run] to within [tolerance, set from the reference code's own run-to-run difference].
A failed G1 voids every later comparison. Do not proceed past it.

## G2. The keep or kill number (one number, defined here)

Keep a variant only if ALL hold:
1. [primary metric on the deliverable] beats [bar] by more than [noise band, e.g. the two-seed spread].
2. It beats its own floor: [floor run, e.g. the feature-shuffled control trained with the same pipeline].
3. The architecture matters: [check, e.g. readouts of variant and base differ, CKA below 0.99].
4. No regression on [the existing metric of record] beyond [band].

Kill it if: [condition]. Anything else is INCONCLUSIVE, and the record names the run that would settle it.

Check before locking: the metric separates a known-good checkpoint from a known-bad one, and the gate is
reachable within the configured steps and budget.

## G3. Floors logged every step

| floor | closed form | logged as |
|---|---|---|
| predict zero | [expression] | [key] |
| best global constant | [expression] | [key] |
| best per-group constant (never with singleton groups: that is an oracle) | [expression] | [key] |
| position-only or covariate-only, held out | [fit] | [key] |

Also log the mass behind each loss term: a loss of 0.0 with zero mass means "no valid target", never "solved".

## G4. Per-item falsifiers

| item | class | expected before -> after | sanity ceiling | falsified if |
|---|---|---|---|---|
| [item] | [BC-DELIV / BC-COMPONENT / BC-LOSS / LEARN / ZERO] | [numbers, probe] | [value above which the forward pass is broken] | [one line] |

## Inputs that do not count

Training loss of a self-referential objective, aggregate deltas without pairing, single-row peaks, fewer than 4
to 5 points of any trend, anything read in the first [n] steps or before warmup ends.

## Amendments (dated, append-only)

- [YYYY-MM-DD]: [change], [reason], written before [which data] was seen.

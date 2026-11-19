# The decision record, locked versions and verdicts

Template: `assets/DECISION_RECORD_TEMPLATE.md`. Script: `scripts/check_chain.py`.

## The one-page post-critic decision document

The source round produced about twenty files. The one that mattered opened: "This file supersedes [the hand-off
draft, section 4] and [the decisions draft]. Both of those were written before the adversarial phase ran, and
the four critics overturned enough of them that reading them first will mislead you. Everything below is
post-critic. One page of decisions, then where each one is argued." And: "Read this file. The other nineteen are
the evidence."

Its sections, in order:

1. **The one thing that changed.** A small table of quoted probe rows that reframed the round, with the scope it
   applies to. "A null there will be misread as 'arrangement does not help', when what it means is 'arrangement
   does not help at that scale'."
2. **Build order.** `| # | item | LOC | minutes vs baseline | why (measured before -> after) |`. Say which items
   move the shipped deliverable by construction, and which cost about 10 LOC and zero minutes and should land
   regardless.
3. **The lead's ideas, and what happened to each**, the verdict in the heading: "right, and the campaign was
   wrong"; "one half builds, the other dies"; "the loss already is one, at a fixed concentration".
4. **What is now dead, and do not spend a run on it**, each with the measurement that killed it.
5. **Fixes now motivated by measurement**, when a probe turned an idea into a requirement.
6. **Numbers to correct wherever they are reused.** `| wrong | right | source |`. One benefit quoted from a paper
   was re-pegged downward because the quoted figure belonged to a different-resolution variant.
7. **The one thing still blocking everything**, with the command that unblocks it.
8. **Where each thing is argued.** `| file | what it is |`, pre-critic drafts marked superseded.

A correction owed to the lead is written in the first person and fixed in every earlier document that carried
it: "A correction I owe you: I initially cited [X]. They don't."

## Supersedes chain and locked versions

**Two design rounds ran on the same day. The penultimate one was recovered first and half implemented
(two components built) before the later record was found, and the work was reverted.** Since then:

- Every design document carries a header in its first lines: `Status: LOCKED`, `Status: SUPERSEDED-BY <file>`
  or `Status: DRAFT`, and `Date: YYYY-MM-DD`; optionally `Topic:`.
- Exactly one document per topic is LOCKED. Build only from it.
- Before building, grep for later records and run the chain check:

```bash
python3 scripts/check_chain.py design/                    # names the file to build from
python3 scripts/check_chain.py design/ --require-locked   # fails when nothing is locked yet
```

It reports missing headers and dates, broken SUPERSEDED-BY targets, cycles, more than one LOCKED document, a
superseded document dated after its successor, and a draft newer than the locked head (a later round may be
open).

- A frozen record keeps a banner naming exactly what superseded it and where the current truth lives. Notes
  open with "SUPERSEDED, see X" and, for removed things, "do not look for X; it is gone".
- Superseded drafts are archived (moved), not deleted, so a correction can be audited. Inside a living register,
  superseded text stays as "-old" and withdrawn rows stay struck through with the date and the reason.
- A fresh-chat entry point (`HANDOFF_<topic>.md`) names the locked record; "start any fresh chat there".
- Reversals are logged inline in order (RESOLVED, RE-RESOLVED, FINAL) and never erased. A partial reversal in
  a standing instruction is one dated line pointing at its note.

**A new direction gets a new name.** "don't call this v4. it's another thing!" A conceptually new model is not
the next version number of the old one. The code name stays stable; an aspirational name lives in documents
only; the paper-facing name changes at the end.

**Keep the previous working model as an arm.** The next version was compared against the last working commit,
checked out in its own worktree: "does the redesign beat where we started?" Earlier, the cheap flat fix landed
first so that "flat X, then the new design Y" was the result. The lead overrode an audit that wanted the earlier
models deleted: "they were good models, don't lose them".

## Redesign or tune

Reconstructed from three episodes; the decision rule itself was written down by the agent, not by the lead.

| what the measurements show | verdict | why |
|---|---|---|
| the loss equals a trivial floor for every variant, or the variants' outputs are bit-identical | **redesign** | "the fix is a redesign, not a rerun": every variant of one design sat at exactly 0.5/d |
| the objective's global minimum is the collapsed or constant solution (computed in closed form) | **redesign the objective's form** | anti-collapse weights and pool sizes cannot repair a degenerate objective; switching to a discriminative form flipped the sign of the collapse margin |
| below the floor, no collapse, but the signal you need is tiny (selectivity near 0) | **tune the levers that inject the missing signal** | "NOT collapse, NOT an eval bug, the objective didn't put [the needed identity] in" led to four targeted levers, not a new architecture |
| a fitted extra component's gain is mostly a scalar rescale | **tune one weight, drop the component** | 97.5% of a learned component's gain came from a scalar; one weight change (0 LOC) captured it |
| a shipped choice measures within a few percent of the best alternative | **protect it; do not sweep** | the shipped masking scheme was within 8% of the best, so "do not sweep the masking ratio" |
| a family of loss weights returns ties | **stop tuning weights** | "the whole weight family returned ties at plus or minus 0.01"; spend the budget on architecture, masking and data ordering |
| the new design looks worse | **diagnose before deciding** | same ruler, same extent, cheapest readout switch, trace which tensors the losses touch; the hierarchical variant in the source was then recorded as a negative result with three salvage steps |

When the redesign has run its course, return to the reliable base: "recycle the working base ... reliable >
fancy", with the recycled base kept as the baseline arm. Change one lever at a time near a collapse basin.

## Verdicts: inconclusive, negative, dead

Three labels, each with a next action, never collapsed into one:

| label | meaning | example of the next action |
|---|---|---|
| **inconclusive** | the question could not be answered; say what was missing | "the floor runs were missing, an execution failure": run them |
| **negative** | the question was answered, and the answer is no | record it as future work; do not present it as a win |
| **dead** | the measurement itself was degenerate | redesign the objective or the metric; one record was retitled "DEAD-objective (was INCONCLUSIVE)" after diagnosis |

Rules that go with them:

- **A null is a finding, scoped to the tested setting.** "A null result is reported as a null." "Do not
  synthesise a conclusion the numbers do not support."
- **Deferred on cost is not refuted on mechanism.** Write which one it was.
- **Do not present a weak result as a win.** It stays in the record, with its number, as negative or
  inconclusive. A result that contradicts the claim changes the claim.
- **A metric must separate a known-good run from a known-bad one** before it can issue any verdict. A clustering
  agreement score read near 0 for every run, good or bad, and triggered a false alarm.
- **A post hoc change to a selection rule is disclosed with its timestamp, and both readings are reported.**
  The campaign's success metric was redefined five times and its row rule three times after data were seen; the
  lesson the lead endorsed was to freeze both before the first candidate.

## Cut as fake-able

Keep a list of features removed because they can fake the result, each with what would justify bringing it back.
The entries in the source: a regularizer applied to the full input ("fakes convergence"), an inverse-frequency
weighted target, a graph cache, and a bumped sample count, all "cut as fake-able or premature (do not re-add
without evidence)". A compiler pass was rejected after measurement (net negative from graph breaks). The list
lives in the decision record, so the next round sees it before proposing.

## Settled levers and known defects

- **Settled-levers index.** One row per lever: HELPS, HURTS, NULL, NEVER-ISOLATED or NEVER-RUN, with [MEASURED,
  n] or [ASSERTED], the receipt, and the cheapest settling run. "Before proposing any experiment, find its lever
  in the index. If it has a verdict, the proposal must cite a defect in the control or be a confirmatory seed of
  a single-run effect. If the lever is absent, say so explicitly."
- **Known-defects register.** `| # | severity | attack | evidence | reading rule |`, severity BLOCKING (a number
  would be wrong), HIGH (a claim overstated) or MEDIUM (a caveat a reviewer will raise). "A row here is a defect
  we know about and have chosen not to fix yet ... but it imposes a reading rule on any table we publish." Read
  it before quoting any number.

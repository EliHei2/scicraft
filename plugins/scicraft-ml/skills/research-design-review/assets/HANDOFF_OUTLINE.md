# [Project]: [the job in one line]. Hand-off for the [fresh session / cluster-side agent]

Version [n], [YYYY-MM-DD]. It replaces every earlier copy.
Paste line for the receiver: "Read [path]/HANDOFF_[TOPIC].md in full and carry it out, starting with section 1."

**Audience:** [the agent and the repository path on its machine].
**Author:** [which session wrote this], branch [branch] @ [commit]. Pushed; pull before you start.
**Deliverable:** [one sentence, e.g. "a second version behind config switches that default to the current
behavior, launched as a separate namespaced arm and reported side by side against the current arm"].
**Do not touch:** [the running job, its namespace, its outputs]. Do not stop it, do not reuse its namespace.

## 0. Read this first, in this order

1. [THE_DESIGN.md]: the decisions. It wins on every conflict between design documents.
2. [GATES.md]: the numbers that decide.
3. [GUARDRAILS.md, quoted here by id with the text of each binding rule] and [the repo instruction file]: they
   win on style, scope and hard constraints, and `GUARDRAILS.md` wins over every other document.
4. [critic report], only for the evidence behind a ruling. [Pre-critic drafts]: background only; do not build
   from them.

If you doubt a claim, read the .out file. If a decision hangs on a number that does not exist, write one small
probe and commit its output rather than guessing.

## 1. The one measurement that gates everything (before any code)

[What to read or run, exactly.] If [stop condition], say so immediately and stop. Report this number before
proceeding. Also confirm [available hardware] and [the state of the untouched run].

## 2. What exists and works: do not rebuild it

| thing | where | state |
|---|---|---|
Environment defaults: [list]; do not re-derive them. Cost reality: [one run = n minutes]. Do not economize on
arms; economize on wall-clock serialization.

## 3. What was established (numbered facts, each with its probe)

1. [fact] (`[probe].out`).
2. The trap, with its exact scope: [e.g. "never add a position embedding in front of a linear pool"; inside
   attention it works].
3. Documents that disagree with the config: [claim | file:line | truth]. The yaml is authoritative.

## 4. Structural blocker to clear first

Make every new mechanism a config switch whose default is the current behavior, so the existing arm reproduces.
[Name the hidden coupling, e.g. "a new key missing from the launcher's config writer silently keeps its default
in every submitted job"; echo the resolved config into the run log.]

## 5. What to build (ranked)

| # | item | where (file:line) | new config key | default | class |
|---|---|---|---|---|---|
For each item: the measured before -> after with its probe; cost (LOC, minutes, parameters); two hedges;
**Falsified if:** [one line]. A scalar change with a plausibly large effect runs as its own arm.

### Decisions that are easy to get wrong

[Ruling, source.] If you disagree after reading both sources, say so explicitly; do not silently pick.

### Explicitly out of scope (do not build these)

| proposal | why it dies or waits |
|---|---|
Ideas beyond this list go under "Proposals" in your report, not into code.

## 6. The ladder

Serial first, alone: [item], then re-baseline. Then concurrently: [items]. Then only if [condition]: [item].
If you can only run one thing: [item].

## 7. How to run

One namespace TAG per arm, never reused after the model changes (stale done-markers will skip stages and score
an old checkpoint against a new config). The floor arm is not optional. Never clean another namespace.
[Exact commands, or a pointer to the project's job-submission skill.]

## 8. Testing is half the job (land the tests with the code)

(a) Equivalence: switches off reproduces the current arm bit for bit, or within [tolerance]. Run it before
submitting anything. (b) Per-item falsifiers with expected numbers and sanity ceilings. (c) The missing null on
the deliverable, run on the existing trained checkpoint first so the new version has a trained baseline.

## 9. Gates

G0 reproduction (do not proceed past a failure), G1 the new probe, G2 floors, G3 the existing metric unchanged,
G4 tripwires. Thresholds are in [GATES.md].

## 10. Hard constraints and traps

[Constraints: a change that violates one is rejected.] Traps, each with its incident: do not write anything you
care about to a temporary folder; do not reuse a TAG; do not trust a docstring over the yaml; verify that the
synced file is the one running.

## 11. Report back in ONE markdown file at [path]

1. The gating number from section 1, first.
2. What was built (file:line, LOC, config key) and what was not built, with the reason.
3. Equivalence: yes or no, with the two curves.
4. The null-probe table. This is the headline.
5. The metric of record, new beside old; wall-clock and peak memory per arm.
6. Per mechanism: KEPT, KILLED or INCONCLUSIVE, and for inconclusive, the run that would settle it.

Do not synthesize a conclusion the numbers do not support. If the new version does not move [the probe], say
so plainly: that is a real finding, worth more than a mechanism that quietly reverts.

## 12. Ask the operator only if

1. [a cap would be exceeded]. 2. [a gate cannot be met]. 3. [a constraint must be broken to progress].

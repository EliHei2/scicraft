# The anatomy of a brief, element by element

Each element below gives the rule, a worked example from machine-learning work, and the incident or practice it
comes from. The running example is a hand-off to an agent on a training cluster that must build a second version
of a model behind config switches and launch it beside a run that is already training.

## 1. Header

```
# <Project>: <job in one line>. Brief for the <where> session
Version 2, <weekday date> (<which side wrote it>). It replaces every earlier copy.
```

Why: a remote agent once ran an older and broader prompt. It was noticed only because the agent mentioned a
"section 3" that existed in the old version alone. Since then the old file is renamed `*_superseded.md` and every
brief carries its version and date.

For a paste-in brief, the first line under the title says how to use it: "Paste everything below the line into
the session on the cluster. It is self-contained."

## 2. The job and the done-tests

Write one paragraph of job. Quote the operator's bar. Then list the tests that define done, each one a check that
someone can run.

Example from a model release:

> Done when these four tests pass. 1. One minute: a person who has never seen the package reads the top of the
> README, installs, pastes six lines, and has an embedding and a figure. 2. Ten minutes: a fresh agent with only
> the README and the docs runs the three queries and draws the three views without opening the source.
> 3. Two minutes on the hosted demo: a fresh agent uploads the example file and gets its results. 4. Nothing
> needs an apology: a reader who knows the paper finds each part of the method in the code under the paper's
> name. No dead options, no leftover experiment, no unexplained constant.

Then state what the job is not. The release brief said: "This job is engineering, not a campaign. No
preregistration documents, no steward or judge agents, and no planning or report documents beyond the ones this
brief names." A training campaign earlier that year had used stewards, judges and a 61-stage pipeline. The
release did not need any of that, so the brief cut it.

State what is running and must not be touched in the first paragraph: "A pre-training run of the current model is
already running. Do not touch it, do not kill it, do not reuse its namespace."

## 3. Names and places

| Name | Value and rule |
|---|---|
| `WORK` | the job's folder (exists; this brief is in it). Scratch, logs, golden files, state. |
| `CLEAN` | the new repository (create). Fresh history. |
| `CKPT` | checkpoint store, about 500 GB quota, shared with another project |
| `CAMPAIGN` | the research repository. Read only: never checkout, switch, stash or worktree in it. Another session may be working under one subfolder; never touch it. |
| Checkpoint of record | run `<run id>`, step `<n>`, with its config and code commit taken from the run's manifest |

Why: a brief that names "the latest checkpoint" gets whichever checkpoint the receiver finds first. Two more
incidents belong here as traps. In one, the dataclass defaults disagreed with the canonical YAML. In another, a
new config knob was missing from the launcher's list and silently kept its default in every job. The brief names
which file is canonical: "The yaml is canonical. Never reason from the dataclass defaults. Do not trust a docstring
over the yaml."

## 4. Reading list with precedence

```
## 0. Read this first, in this order
1. DESIGN.md: the decisions. Start here. One page; it supersedes the two older synthesis docs.
2. gates_run.md: the four probes that were finally run, and the reframe that changed the build order.
3. refutation.md section 7: the ranked build with lines of code and minutes per item.
4. probes/*.out: every number in those documents is quoted from one of these. If you doubt a claim, read the
   .out; if a decision hangs on a number that does not exist, write one small probe instead of guessing.

HANDOFF_v1.md and DECISIONS_v1.md are pre-critic and partly overturned. Use them only for background in sections
1 to 3. DESIGN.md wins on every conflict. The repository's CLAUDE.md and GUARDRAILS.md still win on style, scope
and hard constraints.
```

`GUARDRAILS.md` sits above every document, the brief included (the governing documents are defined in the sibling
skill, `project-structure/references/governing-documents.md`). Other forms that worked: the documents as a
numbered list headed "in order of authority", and "its 'Overriding rule'
section wins over anything else". In a figure brief: "sources of truth newest first; if two sources disagree, the
higher one wins". Put rejected drafts behind a plain label: "Current answers, rejected as off-target and LLM-like.
Do not build on them."

## 5. Numbered rules

The rules a long brief needs, from the release brief:

1. **Disk.** Measure first and keep a DISK.md. No storage tier may fall below 15% free. Set caps on what this job
   adds (for example a 100 MB repository, a 12 GB environment, 20 GB of golden files). Above a cap, ask first.
   Delete your own intermediates once a result is verified, and report what you removed.
2. **Deletion.** Only inside folders this job created may anything be deleted, moved, renamed or rewritten.
3. **Privacy.** Name what never reaches published files: cluster paths, logins, queue names, in-house sample
   names, internal run vocabulary, assistant traces (CLAUDE.md, `.claude/`, attribution lines). Never print a
   token or a remote configuration.
4. **Provenance.** No code copied from a non-commercial or copyleft source into a permissively licensed package.
   THIRD_PARTY.md lists every derived file.
5. **Claims.** Name who may write numbers. In a writer and worker split, the worker writes no benchmark number,
   rank or comparison into prose.
6. **Compute.** Check the queue first. Leave other jobs alone. Name your jobs `<prefix>-<front>-<what>`. Use
   resume-safe launchers. Report GPU hours per front. Scheduler details belong to `cluster-jobs`.
7. **No pushes** from the remote side.
8. **Gates.** "A gate is passed when its check, run from a clean shell, prints the measured value. Put the command
   and the value in STATUS.md. If a gate fails, say so with the numbers and stop that front."
9. **Scope.** "Build what this brief names. An idea beyond it goes under Proposals in STATUS.md, not into code."

## 6. Stage 0 and the gating measurement

From the model-redesign brief, verbatim in shape:

> **The one measurement that gates everything. Do this before you write any code.** Nobody has ever read a
> trained value of this loss term; every number in the design is at initialization. Read the training logs of
> the running arm and report the loss terms, the effective rank, milliseconds per step and peak memory: the
> trained operating point. The trivial floors to compare against are: predict-zero, the best global constant, and
> the best per-batch constant (this one is the bar). **If the trained loss is already at or below the
> per-batch-constant floor, say so immediately and stop.** Report this number before proceeding.

Other stage-0 forms: "Find the release checkpoint, its code commit and the exact inference settings. If any of the
three cannot be identified with certainty, tell the operator at once." Golden files go in before any refactor:
fixed inputs, outputs in float32 and under autocast, loss terms and gradients on CPU with deterministic
algorithms, each run twice to record how far the old code is from itself. That difference is the noise floor, and
every tolerance is set from it.

## 7. Work units

```
### A. <front name>
Goal. <one sentence>
Method. <numbered steps>
Gates.
- A1 <name>: <check> prints <value>; passes at <threshold>.
- A2 ...
Interface. <the fixed lines users will type; what is frozen>
Falsified if: <the observation that kills this item, with its number>
Expected: <metric> moves from <before> to <after>.
```

Thresholds that were used: per-item cosine at least 0.99999 (report minimum and median); loss and gradient
agreement within 1e-4 relative L2, "or ten times the old code's own difference from itself if that is larger"; a
fold score within the tolerance measured in stage 0. A ranked build table gives item, file and line, the new
config key and its default. Each switch defaults to the current behavior, so the running arm stays bit-identical
when the switch is off.

Testing is "half the job, not an afterthought". (a) Equivalence: bit-identical with the switches off, run before
anything is submitted. (b) A falsifier per item, with expected numbers and a sanity ceiling. (c) The missing null
built on the deliverable and run first on the existing checkpoint.

## 8. Decisions that are easy to get wrong

> Document A argues for applying the change to q, k and v; document B argues against; the refutation (section 4)
> rules for q and k only. Follow that, and if you disagree after reading both, say so explicitly rather than
> silently picking.

Write the trap with its exact scope. A trap stated as "never add positional encoding" was too broad and nearly
killed a correct idea. The true scope was "never add it in front of a linear pool". Keep the counter-case that
shows where the trap applies.

## 9. Out of scope and traps

```
### Explicitly out of scope. Do not build these.
- <item>: <one-clause reason>

### Proposed and rejected. Do not spend a run on these.
| proposal | why it dies | evidence |

### Traps
- Do not write anything you care about to /tmp. A previous session lost an entire workflow's output that way.
- Do not reuse a namespace tag. A stale `.done` marker skipped stages and evaluated an old checkpoint against a
  new config.
- A new config knob that is not in the launcher's list keeps its default in every job without a warning. Make the
  training script echo the resolved switch values into its log.
- Verify that the file you synced is the file that runs.
```

## 10. Order and dates

Serial items first, then parallel, then conditional. Add "If you can only run one thing: <it>". Use a date table
for multi-day jobs (stage 0 by day 1; gates by day 4; documentation by day 8; final audits by a named date). The
give-up order names what goes first and what never goes ("never the gates, the quickstart, the model files").

## 11. Report contract

From the redesign brief:

> Report back in one markdown file: the trained operating point first; what was built (file and line, lines of
> code, config key) and what was not built and why; equivalence yes or no; the null-probe table (the headline);
> the existing metric beside the new; wall-clock and memory per arm; per mechanism kept, killed or inconclusive
> plus the run that settles it. Do not synthesise a conclusion the numbers do not support. If the change does not
> move the probe, say so plainly. That is a real and publishable finding.

For audits: "Counts: 0 critical, 2 major, 8 minor (4 of them QUERY)", then the five most important findings (ID,
severity, file:line, problem, exact fix), then the path of the full findings. For book and paper audits: "Final
message: number of findings by severity, number fixed, and the items that need the author's decision."

Ask for three things in research-agent reports: a confidence level, a "Not determined" list, and the path of a
replay script.

## 12. Write to disk as you go

> Create your output file with a section skeleton in your FIRST tool call, then fill it one section at a time. A
> file with three sharp sections beats a perfect report that dies in your context.

For a worker on another machine: "Write each file as soon as it is done, so the laptop can fetch partial
results." The lead synthesizes in its own loop and does not leave synthesis to the last agent. When a subagent
cannot write files in the harness at hand, it puts the full findings in its final message and the lead saves
them. A killed agent can still have delivered, so the lead checks the declared path before relaunching.

## 13. Ask the operator

> Decide what you can and record it. Ask the operator only for: (1) exceeding a cap or the disk floor; (2) a gate
> that cannot be met; (3) an unclear licence of an input.

Decisions the brief left open go one line each into DECISIONS.md. The release brief also required "go" before any
irreversible step, such as archiving the old tree.

## The state file for long jobs

> This job runs for two weeks and your context will be reset more than once. Keep STATE.md current: what is done,
> what is running (job ids, log paths), what is next, what is open. After any reset read this brief and STATE.md
> before anything else.

Add STATUS.md, sent at every milestone and at least daily. Add NOTES.md from the other side, which is read at
every milestone and answered in STATUS.md.

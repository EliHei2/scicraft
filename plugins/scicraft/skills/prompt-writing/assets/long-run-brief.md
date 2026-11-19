# [Project]: [the job in one line]. Brief for the [where] session

Version [N], [weekday date] ([which side wrote it]). It replaces every earlier copy.

## 1. The job

[One paragraph: what to deliver and by when.] The operator's words ([date]): "[the request, verbatim]". On the
bar: "[the standard, verbatim]". [Reference exemplars the operator named.]

[What is running and must not be touched: jobs, a baseline run, another session's folder. "A run of the current
model is already training. Do not touch it, do not kill it, do not reuse its namespace."]

[Who does what: "You build everything that needs this machine. The other session publishes and writes the final
wording. Files move between us through the hand-off folder (section 8)."]

This job is done when these [N] tests pass. You run them in section 9.
1. [A check someone can run, with its time budget. Example: "One minute. A person who has never seen the package
   reads the top of the README, installs, pastes six lines, and has a result and a figure."]
2. [...]
3. [...]

What binds this job, quoted from the project's governing documents so you need not open them to know them:
- Short goal [S<n>] from `GOALS.md`: "[its text, with its due date and its gate]".
- Guardrails from `GUARDRAILS.md`: [G<n>] "[rule text]"; [G<m>] "[rule text]". `GUARDRAILS.md` wins over every
  other document, this brief included.
- Definition of done from `GUIDELINES.md`: "[its checks, verbatim]".

This job is [engineering, not a campaign]. No [planning documents, steward or judge agents] beyond what this brief
names.

## 2. Names and places

| Name | Value |
|---|---|
| `WORK` | [path]. Exists; this brief is in it. Scratch, logs, golden files, reports, your state file. |
| `CLEAN` | [path] (create). [The deliverable repository, fresh history.] |
| `SOURCE` | [path]. Read only: never checkout, switch, stash or worktree in it. [Another session works under X: never touch it.] |
| `STORE` | [path] ([quota], shared with [what]) |
| `ENV` | [one environment, its name and location; what it is for and what it is not for] |
| Of record | [run id, step, config file, code commit], taken from [the run's manifest]. Nothing about it changes. |
| [Name] | [value, and the one constant to change when it changes] |

## 3. Rules

1. Disk. Measure before you write; keep `$WORK/DISK.md` with quota, used and free per storage tier. No tier
   may fall below [15]% free; if a step would cause that, stop and tell the operator. Caps on what this job adds:
   [CLEAN 100 MB, ENV 12 GB, golden files 20 GB]. Above a cap, ask first. Delete your own intermediates once a
   result is verified, and report what you removed.
2. Deletion. Only inside the folders you create for this job may anything be deleted, moved, renamed or
   rewritten.
3. Privacy. Published files never contain: [cluster paths, logins, queue names, in-house sample names, internal
   run vocabulary such as X and Y, reviewer content, assistant traces (CLAUDE.md, .claude/, attribution lines)].
   The hand-off folder never contains [in-house data, credentials]. Never print a token or a remote configuration.
4. Provenance. Nothing in [CLEAN] is copied from code under a non-commercial or copyleft license. `THIRD_PARTY.md`
   lists every derived file with its license.
5. Claims. [Who may write numbers. "You write no benchmark number, rank or comparison anywhere; the other session
   adds results from the paper of record."]
6. Compute. Check the queue first and leave every job that is not yours alone. Name your jobs
   `[prefix]-<front>-<what>`. [Scheduler rules: one submission per task, resume-safe launchers.] Report GPU hours
   per front.
7. No pushes. Nothing goes to [public hosts] from this machine.
8. Gates. A gate is passed when its check, run from a clean shell, prints the measured value. Put the command and
   the value in `STATUS.md`. If a gate fails, say so with the numbers and stop that front. Never ship "close
   enough".
9. Scope. Build what this brief names. An idea beyond it goes under "Proposals" in `STATUS.md`, not into code.

## 4. How to work

- State. This job runs for [two weeks] and your context will be reset more than once. Keep `$WORK/STATE.md`
  current: what is done, what is running (job ids, log paths), what is next, what is open. After any reset read
  this brief and `STATE.md` before anything else. `$WORK/DECISIONS.md` gets one line per choice this brief left
  open.
- Agents. Work as a lead with one agent per front, at most [three] at a time. Each front in section 6 can be handed
  over as it stands, together with sections 2 and 3. An agent reports measured numbers, and you check its gates
  yourself before accepting. Keep [the shared artifact] in one pair of hands. Give mechanical work (link checks,
  leak scans, notebook execution, input fixtures) to a cheaper model. The audits of section 9 go to fresh agents
  that have not seen this brief.
- Writing. Every agent writes its findings to a file in `$WORK` with a section skeleton in its first tool call.
  If an agent cannot write files, it puts the full findings in its final message and you save them.
- Reporting. `STATUS.md` in the hand-off folder at every milestone and at least once a day.
- Asking. Decide what you can and record it. Ask the operator only for what section 10 lists.

## 5. Stage 0, before any front

1. Read, in this order:
   1. [document]: [why]. Start here.
   2. [document]: [why].
   3. [records folder]: every number in the documents above is quoted from these. If you doubt a claim, read the
      record; if a decision hangs on a number that does not exist, write one small probe instead of guessing.

   [Older documents] are superseded and partly overturned; use them only for [background]. [Document 1] wins on
   every conflict except one: `GUARDRAILS.md` wins over every document. The repository's CLAUDE.md still wins on
   style and scope.
2. The gating measurement. [Name the number and where to read it.] [Why it gates.] If [it is at or beyond the
   threshold, with the number], say so immediately and stop. Report this number before proceeding.
3. Identify [the checkpoint, the commit and the settings of record]. If any cannot be identified with certainty,
   tell the operator at once.
4. Golden files in `$WORK/golden/`, before any change: [fixed inputs; outputs in each precision; loss terms and
   gradients on CPU with deterministic algorithms]. Run each twice and record how far the old code is from itself.
   That difference is the noise floor; every tolerance below is set from it.
5. `DISK.md`, then the first `STATUS.md`.

## 6. The fronts

### A. [Front name]

Goal. [One sentence.]

Method.
1. [Step.]
2. [Step.] After every round, run gates A1 to A[n]. A round that breaks a gate is reverted.

Gates.
- A1 [name]: [check] prints [value]; passes at [threshold, for example per-item cosine at least 0.99999; report
  minimum and median].
- A2 [name]: [loss terms and gradients within 1e-4 relative L2, or ten times the old code's own difference from
  itself if that is larger].

Interface. [The lines users will type, which are fixed.]

Expected. [metric] from [before] to [after].

Falsified if: [the observation that kills this item, with its number].

### Decisions that are easy to get wrong

- [Decision]: [document X] argues [this], [document Y] argues [that]; [document Z] rules [this]. Follow that, and
  if you disagree after reading both, say so explicitly rather than silently picking.

### Explicitly out of scope. Do not build these.

- [Item]: [one-clause reason].

### Proposed and rejected. Do not spend a run on these.

| Proposal | Why it dies | Evidence |
|---|---|---|
| [ ] | [ ] | [record] |

### Traps

- Do not write anything you care about to /tmp. A previous session lost an entire workflow's output that way.
- [The file that is canonical when two disagree: "The yaml is canonical. Never reason from the dataclass
  defaults."]
- [A hidden coupling: "A new config key that is not in the launcher's list silently keeps its default in every
  job. Make the training script echo the resolved values into its log."]
- Do not reuse a namespace tag. Verify that the file you synced is the file that runs.

## 7. Order and dates

Stage 0, then [A]. When [the interface is frozen and A2 has passed]: [B, C] in parallel.

| When | What |
|---|---|
| day 1 | stage 0 done: gating number reported, golden files, tolerances |
| day [n] | [gates] pass; [release candidate 1] in the hand-off folder |
| [date], noon, at the latest | all audits pass; `final/`; `REPORT.md` |

If you can only run one thing: [it]. If time runs short, give up in this order: [first], [second]. Never [the
gates, the core deliverable].

## 8. Hand-off

```
from_[this side]/
  STATUS.md        at every milestone and at least once a day: done, measured numbers, open questions, Proposals
  rc1/ rc2/ final/
from_[other side]/
  NOTES.md         read at every milestone; answer in STATUS.md
```

Transfer verbs: [copy, check, list] only, with checksums. Never sync, move, delete, purge or any delete flag. Never
in the hand-off folder: what rule 3 excludes, and logs.

## 9. Final audits, by fresh agents without this brief

1. Newcomer: given only [the README and the docs], do tests 1 and 2 of section 1 in a new environment. Every
   stumble is fixed in the docs or the code, not explained away.
2. Break it: [given only the running service, try five inputs of its own choosing].
3. Leak scan of everything published against rule 3. Zero hits. Keep the output as `LEAKSCAN.txt`.
4. Consistency from a clean clone: [gates] re-run.
5. Numbers: each line of `FACTS.md` traced to its file.
6. Guardrails: each rule of `GUARDRAILS.md` reported as pass, fail or not applicable, with its check.

Output: `$WORK/final/REPORT.md`, in this order: the gating number from stage 0; each gate with its measured value; per item kept,
killed or inconclusive, with the run that would settle it; what was built and what was not, and why; GPU hours
and disk per front; what is open. Do not synthesize a conclusion the numbers do not support. A null result is
reported as a null, scoped to the setting tested.

## 10. Ask the operator

- Before exceeding a cap of rule 1 or the disk floor.
- If a gate cannot be met.
- If [the license of an input is unclear].

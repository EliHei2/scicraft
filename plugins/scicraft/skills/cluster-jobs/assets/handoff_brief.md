# [Project]: [the job in one line]. Brief for the cluster session

Version [N], [date] ([laptop side]). It replaces every earlier copy.

Paste nothing else. This file is self-contained. Read it in full before acting.

## 1. The job

- What to deliver, in one sentence: [deliverable: files, tables, figures, a checkpoint].
- The operator's words that set the bar, quoted and dated: "[quote]" ([date]).
- Done when these checks pass, each a command that prints a value:
  1. [check 1: command, expected value]
  2. [check 2]
- Running now and not to be touched: [job names or ids, directories of earlier runs].
- What this job is not: [for example "no new experiments", "no refactor", "no planning documents"].

## 2. Names and places

| Name | Path or id | Rule |
|---|---|---|
| CODE | [synced code tree] | read-only, synced from the laptop; never edit here |
| PY | [absolute interpreter] | the only interpreter jobs call |
| DATA | [input root] | read-only |
| OUT | [run directory for this job] | yours; one subdirectory per run, named by its parameters |
| CKPT | [checkpoint of record, with its hash or commit] | read-only |
| INBOX | [folder the laptop pulls from] | write reports here |

Code of record: [branch] at [commit] (CODE/CODE_COMMIT). If they disagree, stop and say so.

## 3. Rules

1. Compute. Check the queue first and leave every job that is not yours alone. Name your jobs
   `[prefix]-<what>`. [No job arrays: one submission per unit.] Resume-safe launchers. Every job
   sources the environment block (thread caps, short local TMPDIR, PYTHONNOUSERSITE=1). Calibrate
   on one unit before any fan-out. Report GPU hours.
2. Disk. Measure before you write. Never let a filesystem fall below [15]% free; if a step would,
   stop and ask. Delete only your own intermediates, and only after the result they fed is
   verified. Report what you removed.
3. Deletion. Only inside folders this job created may anything be deleted, moved or renamed.
4. Privacy. [What may never leave the cluster.] Never print a token or a credential.
5. Claims. Numbers come from stored records and are reported with the command that produced
   them. Do not synthesize a conclusion the numbers do not support. A null is a finding.
6. No pushes. Nothing leaves for a shared repository from the cluster.
7. Gates. A gate is passed when its command, run from a clean shell, prints the measured value.
   Put the command and the value in STATUS.md. If a gate fails, say so with the numbers and stop
   that unit of work. Never ship "close enough".
8. Scope. Build what this brief names. Ideas beyond it go under "Proposals" in STATUS.md.
9. Decisions that change what an experiment means (a loss term, a split, a default, a filter)
   are proposed, not made. Write the trade-off and wait.

## 4. How to work

- State. Keep OUT/STATE.md current: done, running (job ids, log paths), next, open. After any
  context reset read this brief and STATE.md before anything else.
- Decisions. OUT/DECISIONS.md, one line per choice this brief left open.
- Agents. A lead plus at most [3] helpers, one per unit of work. Check each helper's gate
  yourself before accepting it. One writer per file. Audits go to fresh agents that have not seen
  this brief.
- Reporting. INBOX/STATUS.md at every milestone and at least once a day.

## 5. Stage 0, before anything else

1. Read, in this order: [doc 1] (why), [doc 2] (why). [Doc 1] wins over [doc 2] on any conflict.
   Do not build on [superseded drafts, by name].
2. The gating measurement: [one cheap number]. If it is [stop condition], report it and stop.
   Report this number before writing any code or submitting any job.
3. Preflight: `bash [path]/preflight.sh --python $PY --src $CODE --marker [string]` must print
   PREFLIGHT PASS.
4. First STATUS.md.

## 6. Work units

For each unit:

- Goal: [one sentence].
- Method: [what to run; the exact command or script].
- Gate: [number and threshold, with the noise floor it was set from].
- Falsified if: [the observation that kills the idea].
- Out of scope: [list, each with a one-clause reason].
- Traps: [each with the incident that taught it, for example "do not write to /tmp: a session
  lost a whole run's output there"].

## 7. Order

Serial first: [units]. Then concurrent: [units]. If you can run only one thing: [unit].
Give-up order when time runs out: [units, last first].

## 8. Hand-off channel

```
INBOX/
  STATUS.md       measured numbers, open questions, proposals
  [results]/      one folder per unit, with the command that produced each file
```

Transfer verbs allowed: copy only, with checksums. Never sync with delete, move or purge. Logs and
raw data never travel.

## 9. Report contract

One markdown file, INBOX/REPORT.md:

1. The gating number from stage 0, first.
2. Per unit: kept, killed or inconclusive, with the run that settles it and its numbers.
3. What was built (file and line) and what was not built, and why.
4. Wall time, peak GPU memory (from the framework) and peak host memory per job type.
5. What failed, with the log line.

Report outcomes faithfully: if a check was skipped, say so.

## 10. Ask the operator

Only when:

- a disk floor or cap would be crossed;
- a gate cannot be met;
- a decision under rule 9 is needed.

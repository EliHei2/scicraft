# Long and overnight campaigns

For work that outlives one context window: an overnight sweep, a week of cluster runs, a two-week release
job, an agent left alone while the user writes something else.

## 1. Files that survive a reset

A job that runs for days will have its context reset more than once. The brief that ran a two-week job said:
"Keep STATE.md current: what is done, what is running (job ids, log paths), what is next, what is open. After
any reset read this brief and STATE.md before anything else."

| File | Holds | Updated |
|---|---|---|
| `STATE.md` (`assets/STATE.md`) | done, running, next, open, decisions, the user's rules, proposals, volatile paths | after every unit and every launch |
| `JOURNAL.md` (`assets/JOURNAL.md`) | one row per attempt, including crashes, with its intent written before it starts | before and after every attempt |
| `STATUS.md` | what the user reads: progress, numbers with the command that printed them, problems | at every milestone and at least daily |
| `NOTES.md` from the user | instructions sent while the job runs | read at every milestone, answered in STATUS.md |
| `DECISIONS.md` (or the Decisions block of STATE.md) | one line per routine choice made without asking | when the choice is made |

The journal design follows an autonomous-research harness the author adapted: every attempt is a row with an
intent field, crashed attempts included. Its greedy hill climb and its "never stop" rule were rejected for
pre-registered work.

## 2. Keep the language model off the critical path

In the unattended design that ran a 61-stage, 18-gate campaign, "the LLM is never on the critical path": a
standard-library DAG driver advanced the stages, three redundant drivers kept it alive, and the agent ran
beside it for triage, gate decisions and writing. The layers:

| Layer | Runs | May do |
|---|---|---|
| L0 driver, no language model | every 10 min | submit ready stages, reconcile with the scheduler, refuse a duplicate pending or running job, grep the synced code for a fresh-code marker |
| L1 triage, cheap model | every 2 h | retry a failed stage or void it, nothing else |
| L2 analyst, strongest model | daily | read summaries, open or close gates by the pre-registered criteria |
| L3 writer | daily after the results freeze | draft from generated tables only; never type a number |

Budgets went into the design: at least 5 and at most 25 GPU jobs a day, submitted when the shared cluster is
least loaded, never on a low-priority queue that can preempt. The agent ran in a sandbox, and only code and
documents were synced to the cluster, never results. That design was built and verified and then held back,
because six items still needed the user's decision. Holding a ready campaign for open decisions is the right
call.

For a smaller job the same idea is one script, one command:

- Stages `prep | smoke | sweep | eval | figures | all`, each skip-if-done through a state file
  (`.state_<name>/<stage>.done`), and fail-safe: a failed unit is skipped so that partial results still
  render ("so we have some stuff at least to look at tomorrow").
- A sentinel is invalid when its input is newer. A stale `.done` once skipped stages and evaluated an old
  checkpoint against a new config; an upstream success sentinel kept a fix from ever taking effect.
- A smoke on one job before any expensive sweep. A rewrite of the data path got "a one-job cluster smoke
  BEFORE the unattended ~30-GPU-h sweep".
- Every gate reachable under the configured budget. A stage gate set at 200 steps per episode was never
  reached by any arm (0 of 7 completed the curriculum; 7 of 7 did at 24).
- Each variant in its own namespace (one tag per arm, never reused after a model change). A new direction
  never overwrites a running job or a prior good model.
- Daemons detached from the session (parent PID 1), with resume-safe launchers.

## 3. Chain the last step into one detached command

A background job outlives the session that started it. Three sessions died together on a usage limit; the
final step had been chained into one detached command, which finished four minutes after the sessions ended:

```bash
nohup sh -c 'until ! pgrep -f prep_step; do sleep 5; done; ./render_a.sh; ./render_b.sh; echo DONE' \
  > logs/final.out 2>&1 &
```

Write it on one line when the user has to paste it. After any death, check the modification times of task
outputs against the last record of the session before re-running anything (`scripts/harvest_agents.py --tasks`).

## 4. Gates decided before the data

A gate decision written after the data arrives fits whatever happened to land. The campaign wrote its
criteria at 23:40 for a 07:30 gate, "to prevent morning-me from pattern-matching on whatever happened to land
(today's three-point 'monotone' trends broke at the fourth point)". The block:

```text
PRE-REGISTERED DECISION CRITERIA FOR [gate] (written [time], BEFORE the data)
1. [criterion, ordered by priority, with its threshold]
2. [...]
Does not count: aggregate deltas, single-row peaks, training loss.
Noise: a move under 2x the standard error is noise. [Or: the spread of two seeds.]
Action if passed: [one command]
Action if failed: [one command]
```

Then the verdict as its own record: "GATE VERDICT ... AWAITING OPERATOR CONFIRMATION" with the exact command,
and after the user's word "GATE EXECUTED (on operator's word)". Recommend; do not switch an irreversible
direction alone.

## 5. Process weight

The research campaign used stewards, judges, pre-registration documents and a 61-stage DAG. The later
engineering job (a release) said: "This job is engineering, not a campaign. No preregistration documents, no
steward or judge agents, and no planning or report documents beyond the ones this brief names." Keep
pre-registration for decision gates in research. Cut the ceremony for engineering.

## 6. Two sessions, two machines

When one session can run things (a cluster, a GPU machine) and another cannot (a laptop with no GPU and no
data), split the roles and say so in every brief:

- The laptop session writes; the cluster session supplies numbers from stored records, runs and scores, and
  writes one file per question as soon as it is done, so the laptop can fetch partial results.
- Under a deadline the running side scores existing checkpoints before training new ones and stops runs that
  do not answer the open questions.
- Sync metrics, never checkpoints or large arrays, to the laptop.
- The two sides may audit each other's outputs; one of them is the writer of each artifact.
- Never send the same request to both sessions. The author did once, got two versions, and feared an
  overwrite.

The brief, transport and paste-line patterns for that hand-off belong to the `prompt-writing` and
`cluster-jobs` skills.

## 7. Background jobs on one machine

For a batch of local runs that the session waits on:

- A runner script (`run_all.sh`) chains the jobs and writes `done.flag` last.
- Wait on the flag, or on the last expected row, in the background or with the harness's monitor tool,
  never with a foreground sleep:
  `until grep -q '<last row>' out.tsv; do sleep 10; done`.
- Exit code 144 was what a killed background job returned. After it, or after a session limit, restart from
  the log and skip the rows already written.
- After a shared engine changes, `ps -axo pid,lstart,command` shows which runs started before the change.
  Rerun only those.
- Stop agents that spend the allowance on lower-priority work. When resuming an agent after a network error,
  say so in the resume message: "the earlier stop was a network error, not a problem with the work."
- **Write shell commands in the form the permission allowlist matches.** Commands with an inline environment
  assignment in front (`VAR=1 python3 run.py`) did not match an allowlisted `python3` pattern and were
  stopped by the safety check. Set the variable inside the script or a wrapper and call the plain
  interpreter.

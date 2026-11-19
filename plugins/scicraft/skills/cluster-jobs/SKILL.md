---
name: cluster-jobs
description: Prepares and runs work on a shared batch cluster (LSF or SLURM) from a laptop whose agent cannot log in, so job files, sync and copy-paste commands work on the first paste and the run survives failures. Use it whenever anything is trained, swept, evaluated or processed on a cluster or GPU nodes, even when the scheduler is not named: "give me the command for the cluster", "how much memory should I ask for", "my job is stuck in PEND", "it got TERM_MEMLIMIT", "the merge never started", "set it up to run overnight", "write a handoff for the cluster Claude", "get the results back". Holds the division of labor (the agent prepares, the user runs), sync rules, the per-job environment block with a reason per line, calibrate-then-fan-out, dependencies and zombie jobs, resume-safe launchers, GPU model pinning, a recovery table, the hand-off brief and unattended campaigns, with tested scripts and templates. Prefer performance-tuning for speed and large-data for out-of-core data.
---

# cluster-jobs

How to get work onto a shared batch cluster from a laptop, when the agent on the laptop cannot
authenticate to the cluster and the user pastes what it prepares. Distilled from a year of the
author's runs on an LSF GPU cluster: hyperparameter sweeps and training of a self-supervised model,
evaluation fans over many datasets, billion-row sharded jobs, overnight pipelines and an unattended
multi-day campaign. Almost every rule below is something that failed on paste, died hours in, or
sat pending for a night. The LSF commands are the ones used in real runs; each has its SLURM
counterpart, marked where it rests on no real run.

> **PRIME DIRECTIVE: hand over files and one command set that works on the first paste, and never
> ask for a resource you have not measured.** The agent writes, lints and dry-runs; the user runs.
> One unit runs first, its peak is read, and only then does the fan-out go.

The failures that cost the most:

1. **Commands that fail on paste.** Placeholder paths (`/path/to/env/bin/python`), a flag the
   installed version does not have, an unbound variable on line 85, a laptop path in a cluster job,
   a script that submitted nothing. The author asked for "copy paste non-bs commands" more than ten
   times. Sections 1, 3 and 11.
2. **Resources guessed instead of measured.** Too low ends in a memory-limit kill; too high, or a
   busy queue, leaves the job pending; a host-RAM number read as GPU memory asked for cards far
   larger than needed. "These are very expensive gpus, I don't wanna stop there and end up with
   nothing." Section 4.
3. **A run that cannot survive one failure.** A merge waiting on a failed job pends forever; a
   relaunch resubmits finished work or overwrites a run the author had looked at; an overnight
   launch dies with the ssh session. Sections 5, 7 and 10.

## 0. Before starting

Collect by reading the project and earlier job scripts; ask only for what cannot be found, in one
message:

- **The scheduler and the site's rules**: LSF or SLURM; queues or partitions with their wall
  limits; per-GPU caps on cores and memory; whether job arrays are allowed; the valid GPU model
  strings; which filesystems hold code, inputs and results, and their quotas.
- **The paths on the cluster**: where the code is synced to, the absolute path of the
  environment's interpreter, the input data, the results area. Real paths, from earlier scripts or
  notes the user keeps locally. Never invent one.
- **The unit of work**: one config, one seed, one dataset shard, one split. How many there are.
- **Measured peaks**, if any run of one unit exists: wall time, peak host memory, peak GPU memory
  read from the framework.
- **What is running now** and must not be touched, and which earlier outputs the author has seen.
- **The machine split**: what may run on the laptop (static checks, small CPU tests) and what
  must not ("don't try to run it locally, it needs a GPU"; a large local analysis crashed the
  laptop once).

## 1. Who runs what

- **The agent prepares; the user runs.** The agent cannot ssh, rsync or submit (the cluster needs
  the user's key and login). It writes job files and hands over exact commands; the user pastes
  them or runs them inline with `! <cmd>`. "don't ssh! you give me the rsync and the command for
  the cluster." When the agent sits in a sandbox on the cluster itself, the same holds: it leaves
  linted job bodies and one launcher a human runs from a normal login shell.
- **Deliver a command set in this order**, each line saying which machine it runs on: (1) the sync
  from the laptop, (2) the preflight on the cluster, (3) the calibration submit or the launch, (4)
  the status command. One block per machine, nothing to fill in.
- **No placeholders in anything handed over.** Resolve every path from earlier scripts and notes.
  "is this hardcoded or you give me an example?" If a value is truly unknown, stop and ask for it;
  do not ship `<your_env>`. `scripts/lint_job.py` fails on `[brackets]`, `/path/to`, `<your...>`
  and laptop paths.
- **Check every flag against the installed version.** Flags that existed on one branch failed on
  the cluster with `Unknown option` three times in one day. Read `--help` of the exact install the
  job will call, or its source at the synced commit.
- **No hard-coded resources in scripts.** Memory, GPU size, cores, wall and per-unit budget are
  set in the command, and the script aborts if one is missing: "I also told you not to hard-code
  the memory." The queue may be clogged tomorrow and the user must be able to change the ask
  without editing code.
- **Run nothing heavy on the laptop.** Local checks are `bash -n`, `py_compile`, imports, linting
  and tests that need no GPU. Training never runs on a CPU: "don't run training of torch models on
  cpu".
- **Offer the user the slow work that can run in parallel.** "if I need to fetch or compute sth from
  the cluster let me know can do in parallel!" Compute small things locally from stored records;
  write anything larger as a ready prompt for the compute side with a budget of about one hour.
  Mark every number you derived yourself (a one-sided p value doubled to two-sided, in the
  instance) as awaiting confirmation until the side that owns the records confirms it.

## 2. Sync the code

```bash
# on the laptop
bash scripts/sync_up.sh ~/work/myproj/ <host>:<cluster code dir>/ --stamp --marker "<string only the new code has>"
```

- **`rsync -rtvu` on the project tree, never `--delete` there.** `-u` skips files that are newer
  on the cluster, and `--delete` would wipe outputs that exist only there. `sync_up.sh` refuses a
  bare `--delete`.
- **Always exclude** `.git`, `__pycache__`, `*.pyc`, `.DS_Store`, data, runs and results, build
  and test caches. An rsync in the other direction once overwrote `.git/config` and the `origin`
  remote vanished twice in a session; check `git remote -v` before any push.
- **Send code only when the tree holds more.** "if I rsync the full thing it also pushes other
  stuff. could you make sure it's just the code files?" `--code-only` sends `.py .sh .yaml .yml
  .toml .cfg .json .txt`.
- **Prove the sync landed.** A module deleted on the laptop stayed on the cluster (no `--delete`)
  and produced a ghost error; a job ran old code because the sync had not finished. Grep for a
  marker string only the new code contains (`preflight.sh --marker`), and print the commit:
  `--stamp` writes `CODE_COMMIT` because `.git` is never sent.
- **Mirror code with `--delete`, then check the expected symbols exist.** A code-only directory
  that never holds outputs (`src/`) is mirrored so a deleted module cannot linger as a ghost:
  `sync_up.sh --mirror --code-only --marker <string>`. Then remove `__pycache__` on the far side
  and grep for the symbols the new code defines (the script prints both commands). Never
  `--delete` into data, results, state or snapshot folders.
- **Paste-safe transfer commands.** One line each, no backslash continuations: a two-line rsync
  pasted without its `\` took the second source as the destination and overwrote a 9.9 GB file.
  Never pass `--partial` to the macOS system rsync (2.6.9): placed before `-e "ssh ..."` it
  swallowed the `-e` and broke a fetch script. Keep the options in one shell array that the dry run
  and the real run share, so the real run does what the dry run showed.
- **Give every sync or fetch script a self-test against a mock source and destination.** Run it
  with `/bin/bash` and the system tools (an agent's `grep` may be a shell function), and after the
  test list where the files landed: one nested rsync put them a level too deep.
- **Sync to a node that shares the filesystem with the submit host**, and quote remote globs: an
  unquoted `*` failed under zsh with "no matches found".
- **Results come back by copy, never by sync.** Pull into a local inbox; copy verbs only; nothing
  is deleted on either side. `scripts/pull_results.sh` copies a cluster outbox into an inbox;
  `scripts/fetch_capped.sh` measures a larger fetch first and stops above a size cap or below a
  free-disk floor (section 9 and `references/handoff.md`).

## 3. The job script

Start from `assets/job_lsf.sh` or `assets/job_slurm.sh` (one unit per job, resume-safe) and
`assets/job_env.sh` (the environment block). Each line of the block exists because something broke:

| Line | Why |
|---|---|
| `PY=/abs/path/env/bin/python`, then `"$PY" -m pkg` | login shells differ; a bare `python` found another interpreter. Call the module, not a console script |
| `PYTHONNOUSERSITE=1` | `~/.local` packages shadowed the environment. Set per job: added globally once, it broke a script whose dependency lived in `~/.local` |
| `PYTHONPATH=$CODE_SRC` first, and `job_env_assert_source pkg` | an editable install shadowed the synced code, and one figure mixed two code versions. The assert aborts if `import pkg` is not under the synced tree |
| `OMP_ MKL_ OPENBLAS_ NUMEXPR_ NUMEXPR_MAX_ RAYON_ POLARS_MAX_THREADS=<cores>` | a fat node has hundreds of cores; with only OMP set, one job ran 691 threads and hit its memory limit |
| `MALLOC_ARENA_MAX=2` | one malloc arena per thread bloats resident memory |
| `UCX_MEMTYPE_CACHE=n UCX_TLS=sm,self` | segfaults with UCX-based GPU stacks on multi-GPU nodes |
| `TMPDIR=/tmp/<user>_<jobid>` | Unix socket paths cap at 108 characters, so a deep `TMPDIR` crashed DataLoader workers; on NFS it left `.nfs*` files |
| `set -euo pipefail` | two pasted scripts failed on unbound variables (`arch`, `SFX`) only after submission |
| provenance lines (host, interpreter, commit, GPU) | "how do I know it's the new code it's running?" |

- **`source ~/.bashrc` is allowed, never relied on.** The absolute interpreter is what makes the
  job reproducible.
- **Check on compute nodes, not login nodes.** A login VM without the CPU features of the compute
  nodes gave a misleading "cannot load module more than once" error from NumPy; a bare
  `import numpy` in a short batch job showed the real cause.
- **A package that initializes the GPU at import hangs on a CPU node.** Keep CPU steps (merges,
  plans) free of that import; a merge job on a CPU queue hung for hours on it.
- **Every run writes to its own directory, named by its parameters**: `<root>/<dataset>/runs/
  lr3e-4_wd0p1_s2/`, never `run01`. "I think it might have overwritten on some stuff." A new
  direction gets its own namespace; a non-default setting goes into the run name.
- **Lint before handing over**: `python3 scripts/lint_job.py job.sh [--no-arrays]`.

## 4. Calibrate on one unit, then fan out

There is no safe default for memory, GPU size or per-unit budget. Too low ends in a memory-limit
kill; too high, or a big queue that is busy, leaves the job pending.

1. **Run one unit**, the smallest real one: `launch_units.sh ... --only <unit>`.
2. **Read its peaks.** Host memory from the scheduler (`bjobs -l` MAX MEM, `sacct` MaxRSS). GPU
   memory from the framework, because the scheduler reports host memory only: log
   `torch.cuda.max_memory_allocated()` at the end of the run. Reserved memory is allocator noise;
   peak allocated is the footprint (4.3 GB allocated against 8.3 to 10.2 GB reserved in one run).
   The `run_meter.py` of `performance-tuning` records wall, host and GPU peaks for any command.
3. **Scale from the measurement**: request = measured peak x a modest margin (1.3 was used when
   extrapolating from a crop: peak x (N / n) x 1.3), and check the extrapolation against any
   measured anchors. Peak GPU memory is often close to linear in the unit's size, and sometimes
   flat: one job's GPU memory stayed at 8 to 10 GB across units of 13M to 52M rows, and the
   "20M rows need 25 GB" figure it replaced had been host RAM read as GPU memory.
4. **Then launch everything** with the measured numbers in the command.

- **Ask honestly.** "some margin is good, but that's too much!" The smallest GPU that fits
  schedules fastest: a 4.3 GB peak asked as about 11 GB lands on dozens of common cards instead of
  a handful of large ones. An oversized memory ticket shrank the eligible hosts and sat pending for
  over two hours.
- **When queues are busy, submit a spread**: several unit sizes on several GPU sizes, each to its
  own output directory, and keep whichever lands first. "go from small sets and small gpus ... a
  pool that gives us the best chance to get this into the queues." The spread changes how the work
  is cut, never what is computed; say which one was kept, and kill the rest once one has landed. Many small parallel jobs beat
  one big serial one (about 7 to 8 h on 4 GPUs against 13.3 h on 1).
- **Justify every flag.** "asking 10 gpus?? for what??" One multi-GPU request once ran every unit
  on a single GPU; one single-GPU job per unit fixed it.
- **Smoke-test before an expensive sweep.** One short job (a few hundred steps, one shard) on the
  real cluster before any unattended multi-GPU-hour run (one rewrite of a data path got a one-job
  smoke before a sweep of about 30 GPU hours).
- **Before blaming size, tabulate failures by GPU model, node and size.** Failures blamed on memory
  were 36 of 36 on one card type; two runs of near-identical size had opposite outcomes.

`references/calibration.md` has the arithmetic, the failure tables and the retry ladder.

## 5. Fan out, dependencies and zombies

```bash
# on the submit host: one job per unit, resume-safe, merge gated on all of them
bash scripts/launch_units.sh --scheduler lsf --job job.sh --units units.txt --out <run dir> --merge merge.sh
```

- **One job per unit, as a loop, when arrays are forbidden.** The author's site forbade job arrays;
  `launch_units.sh` submits a loop of single jobs and records each id in
  `<run dir>/launch/<time>/jobs.tsv`.
- **Resume-safe means rerunning the launcher submits only what is missing.** A unit is finished
  when `<run dir>/<unit>/.done` exists, written last and only after the output was checked. The
  launcher also refuses to resubmit a unit whose job is still pending or running.
- **A sentinel goes stale when its input changes.** A `.done` served old output after the model was
  retrained in place; another kept a fix from taking effect. Delete the sentinel and the stale
  output when the input is newer.
- **A `done()` dependency on a failed job never fires.** The dependent stays pending forever
  ("dependency never satisfied"), looks alive, and holds the subtree. It bites hardest when one
  merge waits on many producers. Two remedies, both in use:
  - `ended()` / `afterany` (the default in `launch_units.sh`), with the merge refusing an
    incomplete set itself (it counts the `.done` files and exits non-zero). The later campaign
    design used `ended()` everywhere and linted generated jobs for `done(`.
  - `done()` / `afterok` (`--dep done`), and when an upstream fails: kill the dependent, fix and
    rerun the upstream, resubmit the dependent.
- **Blocking submit for a prep step whose output later jobs need**: `bsub -K` or `sbatch --wait`.
  Then poll for the file: NFS close-to-open lag means a file written on a compute node may not be
  visible on the submit host the instant the job returns (poll 30 x 2 s).
- **Launchers pre-flight every path, run `bash -n` and `set -u`, and print what they submitted.**
  "it does not submit anything!" A typo must abort in seconds with nothing queued.
- **Detach long launchers**: `nohup bash launch.sh > launch.log 2>&1 & disown`. Parallel chains run
  as background processes waited on by explicit PID (section 8).
- **Training survives requeue only if it resumes.** Write checkpoints as it goes; a requeued or
  wall-killed job resubmits the same script and resumes from the last checkpoint. "does it write
  intermediate results as it goes?"

Scheduler syntax side by side, with the SLURM column's status: `references/scheduler-commands.md`.
Launcher detail: `references/launchers.md`.

## 6. Pin the GPU model

- **Pin the model, not only the memory.** A memory-only request can land on a card model that
  breaks the workload: one GPU geometry library failed about 90% of the time on one architecture
  and never on two others. LSF: `-gpu "num=1:gmodel=<string>"`; SLURM: `--gres=gpu:<type>:1` or
  `--constraint=<feature>` (site-specific; suggested, not yet tested in real work).
- **Verify the model string before an unattended run.** A wrong string pends forever waiting for a
  card that does not exist. Read the site's documentation and check that a test job actually
  becomes eligible.
- **LSF traps**: `gmem` without a unit is read as MB, so `gmem=10.7` places on any card; `gmem` and
  `gmodel` together can conflict and never start; a multi-GPU job without `span[hosts=1]` spreads
  ranks across hosts and a standalone rendezvous hangs at init. `lint_job.py` checks all three.
- **Exclusive or shared GPU mode is site policy: read the site's documentation and follow it.** Shared
  mode (`j_exclusive=no`) schedules faster where a site allows it, and the author's early runs used
  it. The site's own documentation later turned out to make exclusive mode mandatory, and a skill
  that said otherwise had to be corrected. Never settle this from an old job script.
- **Low-priority, preemptible queues were banned for unattended runs**: a preemption near a large
  checkpoint is expensive, and a preempted row in a results table is void.

## 7. Monitor and recover

```bash
bash scripts/track.sh --out <run dir> --units units.txt --scheduler lsf   # done/total, missing, live, failing logs
```

| Symptom | Cause | Do |
|---|---|---|
| `TERM_MEMLIMIT` / `OUT_OF_MEMORY` | over the memory request | raise memory to measured peak x 1.5, or shrink the unit; resubmit only the failed units |
| `TERM_RUNLIMIT` / `TIMEOUT` | over the wall limit | double the wall up to the queue cap, else a longer queue; resume from checkpoint |
| everything pending | busy queue, or a request that cannot be met (wrong model string, memory above the queue's cap, a too-large single-host ask) | `bjobs -p` / `squeue -t PD -o "%i %j %r"` for the reason; lower the ask to the measured peak + 30%, drop the model pin, then change queue |
| dependent pending forever | its upstream failed under `done()` | kill it, fix and rerun the upstream, resubmit it |
| finished, output missing on the submit host | NFS lag | wait and poll (grace about 3 min) before calling it a failure |
| Python traceback | a code bug | retry once for a transient import or NFS error, then fix the code; never rerun unchanged |
| same numbers from runs that should differ | stale code, or one config silently ignored | grep for the marker, check the provenance lines; treat a coincidence as a bug until a check clears it |
| "8 GPUs asked, moves like 1" | units serialized on one GPU | one single-GPU job per unit |

- **Stuck or slow?** Read the step counter twice, 3 minutes apart: rising means advancing,
  identical means stuck. Report done out of total ("N / K units done, merged").
- **Grep logs before explaining**: `grep -lE 'TERM_MEMLIMIT|OUT_OF_MEMORY|CUDA error|Killed|Traceback' logs/*`.
- **Recover the exact submitted command from a job id** (`bjobs -l`, `bhist -l`, `scontrol show
  job`) before resubmitting.
- **Report measured peak GPU memory and end-to-end wall time** with the results, per unit size.

`references/monitoring.md` has the full table, the one-liners and the recovery steps.

## 8. Shared machines: process hygiene

- **Kill by explicit PID**, never by pattern: `pkill -f <pattern>` can take other users' and your
  own unrelated processes with it.
- **zsh does not word-split `$VAR`**, so `kill $PIDS` silently kills nothing; list PIDs explicitly
  or use an array.
- **Bash job control (`jobs`, `wait -n`) silently does nothing under `nohup`**: start background
  workers, keep their PIDs in an array, and `wait "$pid"` for each.
- **Wait for other users' heavy processes**: a queue script that waits while a foreign process
  holds more than 10 GB avoids an OOM kill under contention.
- **Make heavy sweeps resumable**: write results per item as they finish (an incremental TSV), skip
  what is done, because OOM kills under contention are routine.
- **Check `bjobs` / `squeue` first and never touch a job that is not yours.** `bkill` only ids from
  your own launch record.

## 9. Hand-off to a cluster-side agent

When an agent session runs on the cluster itself, the laptop writes its brief.

- **One self-contained file, delivered with one paste line**: `scripts/push_brief.sh BRIEF.md
  <host> <dir> [--hold LATER.md]` checks the files, sends them and prints "Read <dir>/BRIEF.md in
  full and carry it out, starting with stage 0."
- **Results come back with one line too**: `scripts/pull_results.sh <host> <outbox> results/inbox`
  copies only new or changed files, deletes nothing, and prints the head of STATUS.md.
- **Order** (`assets/handoff_brief.md`): the job and its done-tests; names and places; rules; how to
  work; stage 0 with the one cheap measurement that can stop everything; work units with gates and
  falsifiers; order; hand-off channel; report contract; when to ask.
- **Done means a command that prints a value**, recorded in STATUS.md. "Never ship 'close enough'."
- **Protect what is running**: list the jobs and directories that must not be touched; new work
  gets its own namespace and defaults to current behavior.
- **One writer per file.** The same request sent to the laptop and the cluster sessions produced
  two versions and a feared overwrite. The cluster supplies numbers and audits; the laptop writes.
- **Semantic decisions go back to the author.** A change to a loss, a split, a default or a filter
  is proposed with its trade-off, never made silently (the record shows five such decisions
  surfaced and none taken unilaterally).
- **Check every claim the cluster agent returns** at its source before using it; a "completed"
  with an empty result is not a result.

`references/handoff.md` has the skeleton with the reason for each part, the pick-up brief and the
report contract. Brief writing in general: `prompt-writing`.

## 10. Unattended campaigns

For runs over days, a plain script drives the campaign and the agent is called only on a schedule
or on a failure. "If it dies, stalls, is rate-limited, or is stopped by the human, the DAG keeps
advancing."

- **The driver has no model in it**: a standard-library script that reads a stage graph, asks the
  scheduler what is alive, marks stages done from verified sentinels and submits what is ready.
  Running it twice submits nothing twice.
- **The agent works at fixed times with fixed powers**: a cheap triage call every 2 h that may only
  retry or void; one analyst call a day that may open a gate only by naming an evidence file and
  its numbers; a writer that may never invent a number.
- **No gate opens by timeout or default.** A stalled campaign is visible and safe; a defaulted gate
  publishes a result nobody decided on.
- **Three ways to keep the driver alive**: a `nohup` supervisor on the submit host, a
  self-resubmitting heartbeat job with a delayed start (survives a reboot of the login node), and
  scheduler chains with `ended()` for sub-graphs fixed at submit time.
- **One file stops everything**: `STOP` halts new submissions everywhere; only a human creates or
  removes it.
- **Enforce budgets in the submit path**: daily job floor and cap per queue (at least 5 and at
  most 25 GPU jobs a day in the author's design), a GPU-hour cap, a disk floor below which nothing
  is submitted, off-peak submission.
- **A failed stage is published as void, with its reason.** Never retried forever, never dropped.
- **For one night, one script**: stages `prep | smoke | sweep | eval | all`, skip-if-done state
  files, fail-safe so partial results still render. "one .sh file that I'll put on run, wake up
  tomorrow and it has my results."

`references/campaigns.md` has the loop table, the state contract, the failure and retry tables and
the overnight-script pattern. `assets/dag_driver.py` (the driver) and `assets/lint_dag.py` (the graph
check) are the code to start from; copy them into the campaign repository.

## 11. Check before handing anything over

In this order:

1. `python3 scripts/lint_job.py <every job and launcher> [--no-arrays]`: zero errors; each warning
   fixed or named in the message.
2. `bash -n` on every script (the linter does it), and a `--dry-run` of the launcher, which renders
   each unit's job and prints the exact submit lines.
3. Every path in the command set is real and resolved, every flag checked against the installed
   version, the commands grouped by machine.
4. The calibration unit is the first thing submitted, unless measured peaks are already in hand
   (then say where they came from).
5. Read the rendered job of one unit with your own eyes: queue, memory, wall, GPU line, output
   paths, interpreter.
6. Say plainly what was not run: nothing was submitted from the laptop, and anything the agent
   could only check statically.

## 12. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| placeholder paths in commands | "you have all the paths" | resolved paths, a linter that fails on placeholders |
| the agent running things over ssh | "don't ssh! you give me the rsync and the command" | files plus one command set the user pastes |
| memory hard-coded in scripts | "I also told you not to hard-code the memory" | explicit overrides that abort when missing |
| oversized requests | "gmem 100 is too much"; "asking 10 gpus?? for what??" | the calibration unit, measured peak x margin |
| a stop-and-hope overnight launch | "save my sleep by being more careful" | preflight, smoke test, resume-safe launcher |
| many manual steps for a night run | "I just wanna put on run and go do sth else" | one script with stages and skip-if-done |
| a full-tree rsync | "make sure it's just the code files" | `--code-only`; `--delete` only in a code mirror |
| the cluster's installed package | "make sure in the command or script you run this version" | absolute interpreter, synced tree first, an import assert |
| outputs overwritten by a rerun | "save somewhere else so ... it does not overwrite" | one directory per run, named by parameters |
| low-priority queues for long runs | "never lowprio!" | standard queues; preemption voids a row |
| a GPU mode taken from an old job script | the site documentation said otherwise | the mode the site documents, checked before the first submission |
| the LLM driving the campaign | "self-maintained and decision safe" | a plain driver; the agent on schedule and on failure |

## Scripts and assets

Bash scripts need bash 3.2 or later (tested on 3.2) and run where their header says: on the laptop
(`sync_up.sh`, `push_brief.sh`, `pull_results.sh`, `fetch_capped.sh`) or on the submit host
(`preflight.sh`, `launch_units.sh`, `track.sh`). `lint_job.py`, `dag_driver.py` and `lint_dag.py`
are standard-library Python 3.9 or later. Nothing here has been run
against a real scheduler from this package: the scheduler calls were exercised with stand-in
`bsub`, `bjobs`, `sbatch` and `squeue`.

| File | Does |
|---|---|
| `scripts/lint_job.py` | placeholders, laptop paths, syntax, wall, memory, queue, gmem units, gmem with gmodel, multi-GPU host span, `--delete`, bare python, arrays, thread caps, TMPDIR, `done()` |
| `scripts/launch_units.sh` | one job per unit, skip done and live units, calibration with `--only`, merge gated with `ended()` or `done()`, dry run, LSF and SLURM |
| `scripts/track.sh` | done out of total, missing units, live jobs, logs with failure patterns |
| `scripts/sync_up.sh` | `rsync -rtvu` with the excludes, `--code-only`, `--stamp`, marker check, refuses a bare `--delete`; `--mirror` for a code-only directory |
| `scripts/preflight.sh` | interpreter, code tree, marker, import resolves under the synced tree, inputs, disk floor; OK or STOP |
| `scripts/push_brief.sh` | sends a brief and prints the paste line |
| `scripts/pull_results.sh` | copies a cluster outbox into a local inbox, new or changed files only, deletes nothing, refuses a destination outside an inbox, prints the STATUS.md head; `--self-test` |
| `scripts/fetch_capped.sh` | size-gated, resumable rsync fetch the user runs; dry-run measure, cap and free-disk floor, prints `FETCH DONE`; `--self-test` |
| `assets/dag_driver.py` | campaign driver: stages from a JSON registry, required-input check, sentinels with input and output hashes, gates that need evidence, `ended()` chains, STOP; `--self-test` |
| `assets/lint_dag.py` | fails on `done(` dependencies, unknown stage ids, cycles, unknown and unreachable gates, missing scripts, unbraced expansions; `--self-test` |
| `assets/job_lsf.sh`, `assets/job_slurm.sh` | one resume-safe unit per job; SLURM form untested in real work |
| `assets/job_env.sh` | the environment block, provenance lines, import assert |
| `assets/handoff_brief.md` | the brief for a cluster-side agent |

## Reference files

- `references/scheduler-commands.md`: LSF and SLURM side by side, directives, dependency forms, the LSF traps.
- `references/calibration.md`: measuring one unit, extrapolating, honest requests, spreads, failure tables, the retry ladder.
- `references/launchers.md`: resume-safe launchers, sentinels, duplicates, merges, blocking steps, requeue, fetch watchdogs and checkpoints, the first-node input check.
- `references/monitoring.md`: the recovery table in full, status one-liners, stuck versus slow, what not to touch while a job runs, process hygiene.
- `references/handoff.md`: the cluster-side brief, the pick-up brief, delivery, taking results back (pull, capped fetch, ctime, overwrite recovery) and the report contract.
- `references/campaigns.md`: the unattended campaign design, the driver and graph lint in `assets/`, and the overnight script.

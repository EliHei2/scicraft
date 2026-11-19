# Launchers, sentinels and dependencies

## The shape that worked

A driver repository holds no copy of the package; it runs a checkout synced to the cluster and
proves it runs that checkout. Its scripts, in the order of a run:

```
config/<run>.env      every path, budget and resource; overridable from the environment;
                      no default for memory or budget (the script aborts if one is missing)
scripts/preflight     validate inputs before any GPU hour is spent (GPU-free)
scripts/plan          build the job plan by streaming (GPU-free), for example balanced shards
scripts/run_*.sh      plan -> one job per unit -> merge
scripts/validate_*    prove the sharded result equals the full result on a small crop
scripts/track.sh      status snapshot
CODE_COMMIT           branch and commit of the synced code, stamped before the sync
```

The README has a "60-second version": calibrate one unit on one GPU, read the peaks, launch all.

## Resume-safe

- **Rerunning the launcher submits only what is missing.** Each unit checks for its sentinel and
  exits 0 if present; the launcher skips units with a sentinel and units whose job is still pending
  or running under the same name.
- **The sentinel is written last, atomically, after the output is checked**: `test -s <output>`,
  then write `.done.tmp` and `mv` it to `.done`. A killed job leaves no sentinel.
- **A sentinel can carry what it vouches for**: the campaign design stored `{sha256, bytes, rows}`
  per declared output and verified it on first sight; a truncated output renamed the sentinel to
  `.done.bad` and counted an attempt.
- **Invalidate a sentinel when its input is newer.** A `.done` served a stale result after the model
  was retrained in place; an upstream success sentinel kept a fix from ever taking effect (26 jobs
  had died on one missing key, the fix landed, and nothing reran until the sentinel and the stale
  store were removed).
- **"but it says it's already done, what should I remove to redo these?"** Print, for each skipped
  unit, which sentinel caused the skip, so a redo is one `rm` of named files.

## Refusing duplicates

- Before submitting, ask the scheduler whether a job of the same name is pending or running
  (`bjobs -J name -o "jobid stat" -noheader`; `squeue -h -n name -o "%i %T"`) and skip it.
- The campaign design added two more layers: the job id recorded in the same write that moves a
  stage to "submitted", and a per-stage lock directory created with `mkdir` (atomic on NFS, where
  `open(O_EXCL)` is not).
- Give every run one job-name prefix, `<project>-<front>-<what>`, so its jobs are identifiable and
  nothing else is touched.

## Merges and dependencies

- **`done()` / `afterok`**: the dependent runs only if every upstream succeeded. If one fails, the
  dependent pends forever, holds a slot, looks alive, and stalls the subtree silently. Recovery:
  kill it, fix and rerun the failed upstream, resubmit the dependent.
- **`ended()` / `afterany`**: the dependent runs when every upstream has ended in any state, so it
  must check completeness itself. The merge counts the expected outputs and exits non-zero with
  "n of K done" if any is missing. The later campaign design used `ended()` for every chain and
  linted generated jobs for `done(`.
- **A merge must not import a package that initializes the GPU** if it runs on a CPU queue: it hangs.
  Write the merge with the data library alone.
- **Write the merge atomically**: to a temporary file, then `os.replace`, and refuse unless all K
  parts are present.
- **Record the terminal job id** (the merge, or the single job that merges internally) in a file in
  the run directory, so a downstream step can wait on it: `bsub -w "done($(cat OUT/.segjob))"`.

## Blocking steps and NFS

- A plan step whose output the launcher needs: `bsub -K` (LSF) or `sbatch --wait` (SLURM, suggested,
  not yet tested in real work). It ties up the shell, so the launcher itself runs under `nohup`.
- **Poll for the file after the blocking job returns.** A file written on a compute node may not be
  visible on the submit host at once (NFS close-to-open). The launcher polled 30 times 2 s:
  `for _ in $(seq 1 30); do [[ -s "$PLAN" ]] && break; sleep 2; done`.
- Parallel independent pipelines: run each blocking chain as its own background process, keep the
  PIDs in an array, `wait "$pid"` for each and report which one failed.

## Overnight launch

```bash
nohup bash launch.sh > launch.log 2>&1 & disown
```

`nohup ... & disown` detaches the launcher from the terminal, so it and the jobs it submits keep
going after the laptop closes. Before that:

- **Pre-flight every path** and submit nothing if one is missing: the launcher prints `[ok]` or
  `[MISS]` per path and aborts in seconds on a typo.
- **`bash -n` and `set -u`** on every script; two unbound variables (`arch`, `SFX`) broke pasted
  overnight scripts on consecutive days.
- **Print what was submitted**, with job ids, and the one command that shows status.
- **Fail-safe**: a failed unit is skipped and recorded so that the morning still has partial
  results to look at.

## Requeue and checkpoints

- A training job that may be preempted, wall-killed or deliberately stopped writes a checkpoint as
  it goes and resumes from it when the same script is resubmitted.
- One training script exited with code 75 on a stalled data fetch and left a sentinel so that the
  next segment ran with zero loader workers once; the requeue resumed from the checkpoint.
- **A data-fetch watchdog exits with the requeue code when a fetch stalls, and its timeout sits
  above the longest storage stall measured on that filesystem.** A timeout below it requeues
  healthy jobs in a loop. Measure the stalls first (log fetch durations for a day), then set the
  timeout above the longest one.
- A "conservative configuration" that reproduces the old behavior bit-identically is a different
  run, not a resume: give it a new run directory.
- "bkilling is very painful": before stopping an expensive run, check that a checkpoint exists, or
  ask for a debug flag that writes one.

## The first node checks its inputs

- **Before any stage runs, assert that the data store and every checkpoint the graph will read
  exist**, and fail the submission otherwise. A graph launched against a missing checkpoint spends
  its retry budget and reports "void: attempts exhausted", which hides the cause.
  `assets/dag_driver.py` blocks a stage whose `require` paths are missing and files an incident.
- **After a code mirror** (`sync_up.sh --mirror`), remove `__pycache__` on the far side and grep
  for the symbols the new code defines before submitting.
- **When the launcher embeds a config, diff its values against the committed config file and
  refuse on any drift.** An embedded copy that differs from the committed file trains something no
  one reviewed.
- The one-command launch from the laptop that did all three had modes
  `prep | smoke | sweep | all | status | clean`, with resume-safe stages behind sentinels.

## Running the code you shipped

- `PYTHONNOUSERSITE=1`; the synced tree first on `PYTHONPATH`; call `"$PY" -m pkg`, never the console
  script, which may belong to an editable install elsewhere.
- Inside every GPU job, assert that `pkg.__file__` lies under the synced tree, else abort
  (`job_env_assert_source`). An editable install can shadow `PYTHONPATH`.
- Stamp the commit before the sync (`sync_up.sh --stamp`); a synced tree without `.git` logged
  `git_commit=unknown`.
- A release built on the cluster takes its code with `git archive <sha> | tar -x`, never with a
  checkout, switch, stash or worktree in a tree another session uses.

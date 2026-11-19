# Monitoring and recovery

## Status in one command

```bash
bash scripts/track.sh --out <run dir> --units units.txt --scheduler lsf
```

It prints done out of total, the missing units, the run's live jobs, and the log files that carry
a failure pattern; exit 0 complete, 1 incomplete, 2 incomplete with failures in the logs.

The one-liners it stands for:

```bash
bjobs -w -u $USER | grep <prefix>                     # LSF: this run's jobs
squeue -u $USER -o '%.12i %.9T %.40j %R' | grep <prefix>   # SLURM (suggested, not yet tested in real work)
ls <run dir>/*/.done | wc -l                         # units done
grep -lE 'TERM_MEMLIMIT|TERM_RUNLIMIT|OUT_OF_MEMORY|CUDA error|Killed|Traceback' <run dir>/logs/*
```

Report progress as "N / K units done, merged: yes or no", and add the measured peak GPU memory and
end-to-end wall time per unit size to the results.

## Stuck or slow

```bash
tail -n 1 <run>/metrics.csv; sleep 180; tail -n 1 <run>/metrics.csv
```

A rising step number means advancing; an identical one means stuck. For a job without a metrics
file, `bpeek <id>` (LSF) or `tail` of the output file twice.

## Recovery table

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| `TERM_MEMLIMIT` / `OUT_OF_MEMORY` | request below the peak; or unpinned threads | log tail; thread caps present in the job? | memory x 1.5 or a smaller unit; resubmit only failed units (the launcher skips done ones) |
| `TERM_RUNLIMIT` / `TIMEOUT` | wall too short | elapsed against `-W` / `--time` | wall x 2 up to the queue cap, else a longer queue; resume from checkpoint |
| all jobs pending for hours | busy queue, or a request no host can meet | `bjobs -p` / `squeue -t PD -o "%i %j %r"` | lower memory to peak + 30%, drop the model pin, then change queue; a spread of sizes |
| pending, reason names a resource | wrong GPU model string; memory at a queue edge; too many cores for one host | the reason text; the site's limits | fix the string; one unit below the edge; fewer cores |
| dependent pending forever | upstream failed under `done()` / `afterok` | `bjobs -l` "never satisfied"; SLURM reason `DependencyNeverSatisfied` | kill the dependent; fix and rerun the upstream; resubmit the dependent |
| done in the scheduler, output absent on the submit host | NFS attribute cache | `stat` the parent directory | wait about 3 minutes and look again before calling it a failure |
| Python traceback | code bug | first traceback line in the `.err` | one retry for a transient import or NFS error, then fix the code; never resubmit unchanged |
| hang at start on a CPU node | a package that initializes the GPU at import | where it stops | keep CPU steps free of that import |
| "cannot load module more than once" on a login node | login node lacks CPU features the build needs | bare `import numpy` in a short batch job | run checks on compute nodes |
| a multi-GPU job as slow as one GPU | units serialized on one device | "K units over 1 GPU" in the log | one single-GPU job per unit |
| results identical across runs that should differ | stale code; a config key ignored; the same checkpoint | marker grep; provenance lines; weight hashes | resync; fail loudly on unknown config keys; compare by content |
| auth error from every scheduler command | the shell is a sandbox without the setuid auth helper | `bjobs` answers "External authentication failed" | run the launcher from a normal login shell |

## Before resubmitting anything

1. Read the log of the failed job; quote the line.
2. Recover the exact submitted command: `bjobs -l <id>` / `bhist -l <id>` (LSF), `scontrol show job
   <id>` (SLURM, while it is known).
3. Treat a coincidence as a bug until a one-line check clears it: identical statistics across splits
   led to a row-overlap check; "fewer cells than the reference" turned out to be swapped labels;
   "8 GPUs asked but it moves like 1" was a real bug.
4. Change one thing, resubmit only what failed, and record the change in the run's notes.

## Process hygiene on shared machines

- Kill by explicit PID. `pkill -f <pattern>` matches more than you mean, including other users'
  notebooks.
- zsh does not word-split `$VAR`: `kill $PIDS` silently fails. Use an array or list the PIDs.
- Under `nohup`, bash job control (`jobs`, `wait -n`) silently does nothing: keep the PIDs and
  `wait "$pid"` for each, in pairs or bands.
- A queue script that waits while a foreign process holds more than 10 GB of memory avoids being
  OOM-killed under contention.
- Heavy sweeps write one result row per item as it finishes (an incremental TSV) and skip what is
  done, because OOM kills under contention are routine.
- `bkill` / `scancel` only ids from your own launch record; check the queue before touching
  anything.
- Never write anything you care about to `/tmp` on a login node: a session lost a whole workflow's
  output there. `/tmp` is for the job's own `TMPDIR`, which dies with the job.

## Running jobs: what not to touch

- **Never edit a bash script while a job runs it.** Bash reads the file as it goes, so the job
  executes a mix of old and new lines. Write the change to a new file and point the next submit at
  it.
- **Give each incarnation of a job its own log name** (the job id in the name: `%J`, `%j`), so a
  relaunch never appends to or overwrites the log of the last one.
- **Detect a hand-off by content, not by a file name appearing.** A file can exist while it is
  still being written; check a final marker line or a row count before the next step reads it.
- **Never act on a scheduler read taken within about 60 s of a submit or a kill.** A stale pending
  read once led to killing the replacement job just submitted; the scheduler had not caught up.
- **Diagnostics can be the fault.** A periodic faulthandler dump added to forked data-loader
  workers caused the segfaults it was added to catch. When a crash pattern starts together with a
  diagnostic, remove the diagnostic first.
- **Do not bundle an unrelated fix into a recovery.** When the recovered run behaves differently,
  nobody can tell which change did it.

## Disk

- Measure before writing: quota, used and free per filesystem, at every milestone.
- Never let a filesystem fall below 15% free; stop and ask instead.
- Code and inputs live on scratch; results go to a persistent project area; checkpoints on a
  quota-limited tier get cleaned once the result they fed is verified, and the removal is reported.
- An unattended driver refuses to submit work that writes to a nearly full tier (the design used a
  floor of 80 GB free and paged a human below 40 GB) and never deletes anything automatically.

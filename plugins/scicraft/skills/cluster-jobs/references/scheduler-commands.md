# Scheduler commands, LSF and SLURM side by side

The LSF column is what the author's runs used. The SLURM column gives the counterpart for a lab on
SLURM. **SLURM column: suggested, not yet tested in real work** (the evidence behind this skill is
LSF only). Check each SLURM form against the site's documentation and one test job before an
unattended run.

## Submitting and watching

| Task | LSF (used in real runs) | SLURM (suggested, not yet tested in real work) |
|---|---|---|
| submit a job file | `bsub < job.sh` | `sbatch job.sh` |
| submit and get the id alone | parse `Job <123> is submitted` (`sed -n 's/.*Job <\([0-9]*\)>.*/\1/p'`) | `sbatch --parsable job.sh` |
| set the name on the command line | `bsub -J name < job.sh` | `sbatch --job-name=name job.sh` |
| blocking submit (prep step) | `bsub -K < job.sh` | `sbatch --wait job.sh` |
| run after one job succeeds | `bsub -w "done(123)" < job.sh` | `sbatch --dependency=afterok:123 job.sh` |
| run after several succeed | `-w "done(1) && done(2) && done(3)"` | `--dependency=afterok:1:2:3` |
| run after jobs end, any state | `-w "ended(1) && ended(2)"` | `--dependency=afterany:1:2` |
| delayed start | `bsub -b HH:MM < job.sh` (compute with `date -d '+30 minutes' '+%H:%M'`) | `sbatch --begin=now+30minutes job.sh` |
| my jobs, wide | `bjobs -w -u $USER` | `squeue -u $USER` |
| pending jobs and why | `bjobs -p -u $USER` | `squeue -u $USER -t PD -o "%.12i %.30j %.25r"` |
| state of one named job | `bjobs -J name -o "jobid stat" -noheader` | `squeue -h -u $USER -n name -o "%i %T"` |
| full detail, peak memory | `bjobs -l <id>` (MAX MEM is host memory) | `scontrol show job <id>`; after the end `sacct -j <id> --format=JobID,State,Elapsed,MaxRSS,ReqMem,ExitCode` |
| tail a running job | `bpeek <id>` | `tail -f` the file named by `--output` (written live) |
| history and exit reason | `bhist -l <id>` | `sacct -j <id> --format=JobID,State,ExitCode,DerivedExitCode` |
| kill | `bkill <id>` | `scancel <id>` |
| interactive shell on a node | `bsub -Is bash` | `srun --pty bash` |
| job id inside the job | `$LSB_JOBID` | `$SLURM_JOB_ID` |
| job array | `-J name[1-N]` (forbidden at the author's site) | `--array=1-N` (check the site's policy) |

## Directives

| Request | LSF | SLURM (suggested, not yet tested in real work) |
|---|---|---|
| name | `#BSUB -J name` | `#SBATCH --job-name=name` |
| queue / partition | `#BSUB -q <queue>` | `#SBATCH --partition=<partition>` |
| cores | `#BSUB -n 10` | `#SBATCH --cpus-per-task=10` |
| memory reservation and limit | `#BSUB -R "rusage[mem=80G]"` and `#BSUB -M 80G` | `#SBATCH --mem=80G` |
| one host | `#BSUB -R "span[hosts=1]"` | `#SBATCH --nodes=1` |
| wall time | `#BSUB -W 48:00` | `#SBATCH --time=48:00:00` |
| one GPU of a given model | `#BSUB -gpu "num=1:j_exclusive=<per site policy>:gmodel=<string>"` or `-m <host group>` | `#SBATCH --gres=gpu:<type>:1` or `--gpus=1 --constraint=<feature>` |
| logs | `#BSUB -o logs/%J.out` and `-e logs/%J.err` (`%J` = job id) | `#SBATCH --output=logs/%x.%j.out` (`%x` name, `%j` id) |

Command-line options override directives on both schedulers; `launch_units.sh` sets the job name
on the command line for that reason.

## What the termination looks like

| Event | LSF | SLURM (suggested, not yet tested in real work) |
|---|---|---|
| over the memory limit | `TERM_MEMLIMIT` in the log and `bhist -l` | state `OUT_OF_MEMORY`; "oom-kill" in the log |
| over the wall limit | `TERM_RUNLIMIT` | state `TIMEOUT`; "DUE TO TIME LIMIT" in the log |
| dependency can never be met | dependent stays `PEND`; `bjobs -l` says "Dependency condition invalid or never satisfied" | dependent stays `PD` with reason `DependencyNeverSatisfied` unless submitted with `--kill-on-invalid-dep=yes` |
| preempted or node lost | exit 130, 137 or 143 with no `TERM_*` reason | state `PREEMPTED` or `NODE_FAIL` |

## LSF traps met in real runs

- **`gmem` without a unit is megabytes.** `gmem=10.7` asks for 10.7 MB, so the job lands on the first
  GPU of any size and the request means nothing. Write `gmem=10.7G`.
- **`gmem` and `gmodel` together** can conflict, and the job may never start. Use one of them.
- **A wrong `gmodel` string** pends forever instead of failing. Verify it against the site's list
  and watch the first job become eligible.
- **A queue may refuse a memory value at its edge.** At the author's site one GPU queue never started
  a job asking exactly 40 GB of GPU memory; 39 worked. Read the site's limits; when a job pends with
  no reason, try one unit below the edge.
- **A multi-GPU job without `span[hosts=1]`** gets ranks on different hosts; NCCL falls back to the
  network and a standalone rendezvous (bound to localhost) hangs at `init_process_group`, burning the
  wall clock in silence.
- **Per-GPU caps** on cores and host memory are site policy that other users rely on. Scale the cap
  by the number of GPUs requested when checking a multi-GPU job.
- **`bjobs -w` columns shift for pending jobs** (the execution host is empty), so parse
  `bjobs -o "jobid stat job_name"` instead of positional columns of the wide view.
- **The agent's sandbox may not authenticate to the scheduler** even on a cluster node (external
  authentication needs a setuid helper the sandbox lacks). The agent then leaves linted job bodies
  and one launcher, and a human runs it from a normal login shell.

## Shell traps on the way

- zsh expands an unquoted `*` in a remote rsync path locally and fails with "no matches found":
  quote remote globs.
- zsh does not word-split `$VAR`: `kill $PIDS` kills nothing, and `PY="env X=1 python"` is one word.
  `export` variables on their own line.
- `set -u` turns a missing variable into an error at the line that uses it; without it, an unset
  `$OUT` becomes an empty string and output lands in `/`.

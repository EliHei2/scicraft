# Long runs: resumable drivers, incremental writes, sharding, caches

Working detail for section 7 and section 9 of SKILL.md. Scheduler syntax and job dependencies are
in `cluster-jobs`.

## The shape of a resumable driver

`assets/resumable_driver.py` is a working frame. Copy it, replace `process()`, keep the rest:

```bash
python3 resumable_driver.py run    --units units.txt --out runs/lr_3e-4_bs_256 --shard 0/4   # one job per shard
python3 resumable_driver.py status --units units.txt --out runs/lr_3e-4_bs_256               # done / total
python3 resumable_driver.py merge  --units units.txt --out runs/lr_3e-4_bs_256               # refuses until all done
```

The rules it encodes:

- **Independent units.** Each unit (a shard, a split, a file, a parameter setting) reads its own
  input and writes its own output directory. The units are the parallelism; no unit waits for
  another.
- **Skip what is done.** Rerunning the same command finishes the missing units and touches none
  of the finished ones. "Bkilling is very painful" and losing a night of expensive GPUs to a late
  failure were the reasons.
- **A sentinel written last.** The unit's outputs are written first, each through a temporary
  file and `os.replace`; the sentinel comes after them. A killed unit has no sentinel and reruns.
  The merge writes to `name.tmp` and renames, because a killed merge must not leave a truncated
  file that resume logic and every later step would treat as complete.
- **The sentinel knows its inputs.** It records a fingerprint of the input and a hash of the
  parameters. A sentinel without them served a stale result after the model behind it was
  retrained in place, and another made a fix never take effect. Invalidate when the input is
  newer or the parameters differ.
- **Incremental writes.** One line per finished unit, appended and flushed at once
  (`progress_shard<I>of<N>.tsv`). The author's question, "does it write intermediate results as
  it goes?", has to be answerable with yes.
- **Merge refuses partial input.** Merge checks that units 0 to K-1 all exist and are non-empty,
  and lists the missing ones. When the units are disjoint (disjoint feature subsets over one
  shared row index), the merge is a plain concatenation; if a key repeats, that is a bug to report,
  and the rule for which copy wins is written down (the old merge kept the highest score and
  warned).
- **Sharding by position modulo N** (`--shard I/N`) needs no coordination. Job arrays are not
  allowed on every cluster; a loop of independent jobs plus a merge job that waits on them works
  everywhere.
- **Exit codes propagate.** End each job with `rc=$?; ...; exit $rc`. A job that ended with
  `echo "done rc=$?"` was marked successful after failing and released its dependents.

## Submit scripts

The rules below come from one audit of a batch pipeline's shell wrappers, where each mistake had
already cost jobs.

- **Write `${VAR-default}` where an empty value must stay empty.** `${VAR:-default}` also replaces
  a variable that is set to the empty string, so a deliberate empty override (no extra flags, no
  filter) silently becomes the default.
- **Abort when the submit command fails or returns no job id.** Check its exit status, then parse
  the id from its output and stop if the parse is empty; a dependent submitted against an empty id
  either never runs or runs at once. Parse with a portable pattern: `grep -o '[0-9][0-9]*'` works
  in every grep, the GNU-only `\+` does not.
- **A dependent that stays pending forever means its upstream exited.** Kill it, fix the upstream,
  and rerun the resume-safe submit; finished units are skipped.
- **Accept shared flags on either side of the subcommand.** Give every subparser one parent parser
  that holds `--verbose`, `--dry-run` and the like, so `tool --verbose run` and `tool run --verbose`
  both parse. A flag in the position the parser did not expect killed 84 of 126 jobs.

```python
def common(sub=False):
    c = argparse.ArgumentParser(add_help=False)
    c.add_argument("--verbose", action="store_true",
                   default=argparse.SUPPRESS if sub else False)
    return c

p = argparse.ArgumentParser(parents=[common()])
sub = p.add_subparsers(dest="cmd", required=True)
sub.add_parser("run", parents=[common(sub=True)])
```

  The subparser's copy needs `default=argparse.SUPPRESS`. With one shared parent and ordinary
  defaults, the subparser's `False` overwrites a `--verbose` given before the subcommand, and the
  flag is lost without an error (checked on Python 3.10).

- **Symlink large inputs that a step does not modify** instead of copying them per unit. A 6.5 GB
  image had been copied into each of 14 unit directories for nothing.

## Before the full run

1. **Smoke one unit** (`--shard 0/K` on a short list, or `--subset 0`), on the real hardware,
   with the real data. The author's standing order was a smoke before any full training. An unattended sweep
   of about 30 GPU hours waited for a one-job smoke of the rewritten data path.
2. **Preflight** with a script that prints `OK` or `STOP: <what to fix>` for the code version,
   the input paths, the interpreter and the parameters, before anything is submitted. Log the
   imported module's file path in every job: one figure once mixed two code versions because one
   step ran the installed package and another the synced source.
3. **Plan the units from a streamed census** (sizes per key, heaviest key against the budget;
   see `streaming.md`), and check the plan file before submitting.

## While it runs

- Status one-liners that report done out of total (units with a sentinel, merged yes or no).
- A stuck-or-slow test: read the step counter or the progress file, wait a few minutes, read it
  again. Rising means advancing; identical means stuck.
- A grep of the logs for out-of-memory, device errors and memory-limit kills.
- A way to recover the exact submitted command from the job id or the log head.
- **Wait in the background on a loop that ends on success or on a crash**, so the session is
  notified either way and nobody polls by hand. For a job that appends one row per finished item
  to a TSV with a header:

```bash
until [ $(( $(wc -l < out.tsv) - 1 )) -ge 240 ] || ! pgrep -f my_job.py; do sleep 10; done
```

  A job that writes a flag file at the end uses `until [ -f done.flag ]; do sleep 30; done`
  instead. A loop that tests only for success never ends after a crash.
- **One lock file per dataset in the job script**, so a queued duplicate of the same dataset exits
  at start instead of writing into the same outputs.
- **Report resources in numbers**: memory and swap used ("swap 7.2 of 8 GB"), free disk ("6.5 GB
  free"), from `ps`, `free` or `vm_stat`, and `df -h`. Never delete anything to free space without
  asking the user first.

## Run directories

- **One directory per run; nothing overwrites.** "I think it might have overwritten on some
  stuff" followed a second submission writing into the first one's directory.
- **Dataset first, then runs named by parameters**: `<root>/datasets/<dataset>/runs/<param-named
  run>/` and `<root>/summaries/`. Names carry the parameter values with `p` for the decimal point
  and `neg` for minus (`lr_3p0e-4`, `scale_neg0p5`), never `run01`.
- **A new direction gets a new name and a new namespace.** Never overwrite a running job's
  directory or a model that was good.
- **Never rename or delete an output the user has seen**; a variant gets a new name.

## A lab notebook entry per attempt

One entry per attempt, failures included ("keep the failures; they're the most useful
entries"): absolute date, goal, code commit, mode, data and output paths, resources requested,
the exact command, PASS or FAIL with the reason, measured peak RAM, peak GPU memory and wall time,
the validation result, notes.

## Caches keyed by content

A cache or a "skip if done" check is only as good as its key.

- **Key by content, not by name.** "Thin versus dense" turned out to compare two different
  checkpoints with similar names; joining the outputs on coordinates showed it. Identify a model
  by a hash of its weights and a dataset by a hash of its bytes, never by file name.
- **Hash the part that differs.** A stored subset hash covered the whole shared vocabulary array,
  so it was byte-identical for two different subsets and guarded nothing. A guard is real only if
  it fails on the case it exists for; test that it does.
- **Store every parameter that shapes the output with the cache, and assert it at load.** A cap
  that training applied and evaluation did not, a window size asserted at training and not at
  inference, and graph parameters missing from the checkpoint each shifted results silently.
- **Reuse cached artifacts when only analysis is asked for.** "we have some files already, don't
  reproduce fields and prediction"; "no rerunning ... just evals". Recompute only what changed.
- **Freshness checks.** After a crash or another agent's session, a manifest may have been
  regenerated under you. Check derived files against their inputs (a `--check` mode, a hash
  recorded at creation) before trusting them.
- **Freeze one contract artifact and verify it by checksum.** When results must be regenerable,
  keep one long table (one row per method, dataset and metric) as the contract, store its md5 in
  the repository, and fail the pipeline when a regeneration does not match. Verify the cheap tail
  (aggregate to table) first; rerun expensive stages only after it matches.

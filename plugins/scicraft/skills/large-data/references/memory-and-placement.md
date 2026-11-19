# Memory profiles, hardware placement, threads and temp directories

Working detail for sections 5 and 6 of SKILL.md. Scheduler commands, queue names and GPU
selection belong to `cluster-jobs`; this file is about what to measure and what to request.

## Measure one unit before scaling

1. Pick one unit of the real work: one shard, one split, one file, at the size the full run
   will use.
2. Run it under `scripts/peak_memory.py run --units N --json mem.jsonl -- <command>`. It records
   wall time, the peak RSS of the largest process (getrusage) and the peak RSS summed over the
   process tree (sampled with `ps`; worker pools only show up here). In a test with three worker
   processes the largest process read 0.22 GB and the tree 0.90 GB.
3. Run a second size (half or double). Then `peak_memory.py fit mem.jsonl --full-units M
   --margin 1.3` fits memory against size and predicts the full peak.
4. For GPU memory read the framework's own peak inside the job:
   `torch.cuda.max_memory_allocated()` after `torch.cuda.reset_peak_memory_stats()` at the start.
   `max_memory_reserved` is the caching allocator's pool (8.3 to 10.2 GB against a true peak of
   4.3 GB once) and is not the footprint. `peak_memory.py run --gpu` samples `nvidia-smi`, which
   counts every process on the card; use it only when the framework peak is unavailable.
5. Record the measured numbers next to the run (the notebook entry of `long-runs.md`) and size
   the request from them.

Why each step exists:

- **A scheduler's "Max Memory" is host RAM.** A figure of "20M rows needs 25 GB" was host RAM
  read as GPU memory. The GPUs requested from it were far larger than needed.
- **Memory is often not linear in unit size.** A planning document said GPU memory was "roughly
  linear" in split size. The measured profile was flat at 8 to 10 GB across splits of 13 to 52
  million rows: the fixed cost dominated. The measurement wins over the document. `fit` prints a
  warning when the measured sizes are nearly flat.
- **Extrapolate, then check against anchors.** For an external tool the working formula was
  mem_full = peak x (N / n) x 1.3, from a crop of n = 20 million rows, checked against a table of
  measured runs "rather than trusting either one alone".
- **Some peaks hide outside the framework.** A GPU library with its own memory pool does not
  appear in `torch.cuda.max_memory_allocated`. When the job uses one, add its own statistics or
  sample the device.

## Request what was measured

- **Request measured x a modest margin.** "Some margin is good, but that's too much!" was the
  author's answer to a request sized far above a measured anchor. A margin of 1.3 was the
  working value.
- **The smallest machine that fits starts first.** A job with a measured 4.3 GB peak that asked
  for 10.7 GB was eligible for about 40 common GPUs instead of about 8 large ones. When queues
  are busy, submit a spread of sizes (split counts, card sizes), each writing to its own output
  directory, and keep whichever finishes.
- **No hard-coded resources in scripts.** Memory, card size and rows per split are inputs set in
  the command. A script that cannot run safely without them aborts when one is unset ("I also
  told you not to hard-code the memory").
- **More, smaller parallel units beat bigger serial ones.** Four GPUs took roughly half the wall time of
  one for the same billion-row job.
- **Check that a multi-device request uses the devices.** A job that asked for 8 GPUs ran all its
  splits over one ("8 gpu ask but it moves like it's only 1 gpu"). One process per device, or one
  job per split, made the parallelism real.

## Tabulate failures before naming a cause

Failures blamed on memory were a library bug on one GPU model: 36 of 36 failures happened on
that card, and two runs with nearly identical split sizes had opposite outcomes. "GPU type
dominates, not split size." Before raising memory, put every failed and finished unit in one
table with its size, device model, node, software version and exit reason, and look for the
factor that separates them.

## Where each step runs

Compute the bottleneck of the step, then place it:

| Step | Bound by | Runs on |
|---|---|---|
| streaming join or group-by over 10^8 to 10^9 rows | RAM | a large-memory CPU node with many cores (a streaming join killed on a normal node was moved to one) |
| model training, encoding, prediction | GPU | the smallest GPU that fits the measured peak |
| graph community detection with a GPU implementation | GPU | GPU |
| marker scoring, merges, plotting, census | CPU, light | a small CPU job, or the laptop on a slim derivative |
| anything on the full table | RAM | never the laptop: a GB-scale analysis crashed it; check free memory first (`vm_stat` on macOS, `free -g` on Linux) |

- **Training runs on a GPU, never silently on CPU.** Gate training behind a device check with an
  explicit opt-in flag for CPU; a forward pass routed to a CPU queue ran about 10 times slower.
- **Keep CPU-side tools free of GPU-initializing imports.** A package that initialized a GPU
  memory pool at import hung every CPU job that imported it; a workflow's verify phase stalled
  six retries, about 9 hours. Write merges and checks with plain Polars and NumPy, without
  importing the GPU package.

## Profile before optimizing

The first lever is usually thread oversubscription, not the model. Eight data-loader workers
inherited the scheduler's core pinning and ran about 80 threads on 10 cores. One line per
worker, `torch.set_num_threads(1)`, was the dominant fix, worth 10 to 20 times per step. Time
each phase with synchronized timers before changing an algorithm, and re-verify the results
after a speed change: cutting a sample count for speed once weakened a regularizer and two of
four runs collapsed. Detail belongs to `performance-tuning`.

## Thread caps

Every numeric library starts one thread per core by default. Set all of them to the job's core
budget before Python imports them:

```bash
source assets/thread_env.sh 16      # caps POLARS, OMP, MKL, OPENBLAS, NUMEXPR, RAYON, VECLIB; MALLOC_ARENA_MAX=2
```

or, in Python, set `os.environ` at the top of the entry script before importing NumPy or Polars
(as `assets/resumable_driver.py` does). A job with only `OMP_NUM_THREADS` set reached 691 threads
on a 256-core node and was killed for exceeding its memory limit.

## Temp directories

- **Short and local.** `TMPDIR=/tmp/<tool>_<user>_<jobid>`. Data-loader workers open Unix
  sockets under `TMPDIR`, and a socket path may not exceed 108 characters; a deep or network
  temp path crashed every worker with an unhelpful error.
- **Local disk, not network storage**: network file systems leave `.nfs*` files that block
  cleanup.
- **Clean it at exit** (`trap 'rm -rf "$TMPDIR"' EXIT`).
- **Per-script environment flags.** `PYTHONNOUSERSITE=1`, added globally for one tool, broke
  another whose dependency lived in the user site. Set flags in the script that needs them.
- **Multi-GPU segfaults in communication libraries**: `UCX_MEMTYPE_CACHE=n` and
  `UCX_TLS=sm,self` fixed them in one stack.

## Process hygiene on a shared machine

- Kill by explicit PID, never by a pattern (`pkill -f ipykernel_launcher` kills other people's
  kernels).
- zsh does not split `$VAR` into words, so `kill $PIDS` silently fails; list the PIDs or use an
  array.
- Bash job control (`jobs`, `wait -n`) does nothing under `nohup`; wait on explicit PIDs.
- When other heavy processes share the machine, start the next band only after they are gone
  (a queue script that waits while any foreign process holds more than 10 GB), and make the sweep
  resumable, because out-of-memory kills under contention are routine.

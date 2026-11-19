# Calibrating resources

There is no safe default for memory, GPU size or per-unit budget. Measure one unit, then ask.

## 1. The calibration run

1. Pick the unit: the smallest real unit of the work (one config at its real batch size, one
   dataset shard, one split). A toy input measures nothing.
2. Submit it alone with a generous but bounded request: `launch_units.sh ... --only <unit>`, or the
   launcher's own calibration flag (the author's sharded launcher had `--subset N`: one unit, one
   GPU, no merge).
3. When it ends, read:
   - **host memory** from the scheduler: `bjobs -l <id>` MAX MEM, `sacct -j <id> --format=MaxRSS`
     (SLURM, suggested, not yet tested in real work);
   - **GPU memory** from the framework, because the scheduler reports host memory only:
     `torch.cuda.max_memory_allocated()` at the end, reset with `torch.cuda.reset_peak_memory_stats()`
     before the model is built so weights and the largest activation are both inside the peak.
     Reserved memory (`max_memory_reserved`) is the caching allocator's pool; allocated is the
     footprint. One run: 4.3 GB allocated, 8.3 to 10.2 GB reserved;
   - **wall time**, end to end, and the GPU the job actually landed on (`nvidia-smi` in the
     provenance lines; the `run_meter.py` of `performance-tuning` records all four);
   - for stacks with their own allocator (RAPIDS memory manager), torch's peak misses those
     allocations; read the stack's own counter or `nvidia-smi` during the run.
4. Write the numbers down beside the unit size, in the project's notes: the next request comes from
   this table.

## 2. From one unit to all of them

- **Request = measured peak x margin.** The extrapolation rule used for an external tool: calibrate
  on a crop of n rows, then `mem_full = peak x (N / n) x 1.3`, and sanity-check the result against a
  table of measured anchors "rather than trusting either one alone".
- **Check the shape of the curve with two sizes before extrapolating far.** GPU memory is often
  close to linear in the unit size, and sometimes flat: one job stayed at 8 to 10 GB of GPU memory
  for units of 13M to 52M rows. The figure it replaced ("20M rows need 25 GB") was host memory read
  as GPU memory.
- **"some margin is good, but that's too much!"** A request for 13M rows sized at twice the
  measured need for 20M rows was sent back. Keep the margin modest and say what it is.

## 3. Honest requests schedule faster

- **The smallest card that fits.** A peak of 4.3 GB requested as about 11 GB lands on dozens of
  common GPUs instead of the handful of largest ones.
- **An oversized memory ticket is a scheduling failure.** A job needing a few hundred MB asked for
  250 GB, which shrank the eligible hosts, and it sat pending for over two hours.
- **Ask only for what the step uses.** A CPU step goes to a CPU queue; a GPU forward pass routed to
  a CPU queue ran about 10x slower. Cores are justified by threads actually used ("would it really
  help to go for 8 cores??"). A step that needs no GPU gets none ("it's literally cpu").
- **Use the environment that already exists.** Before building a new environment for a step,
  check whether one on the cluster already holds the libraries. "we don't need single cell rapids,
  we have [the method's] env": the method's own environment carried the GPU clustering and
  dataframe stack. A new environment adds version drift and a setup job.
- **When the big queue is clogged, go smaller and wider.** More, smaller parallel units beat bigger
  serial ones: about 7 to 8 h on 4 GPUs against 13.3 h on 1 for the same work. Submit a spread:
  several unit counts (for example 5, 10, 20, 40, 80 splits) on several GPU sizes, each writing to
  its own output directory, and keep whichever lands first. The spread changes how the work is cut,
  never what is computed. Record which one was kept and kill the others.

## 4. Before naming a cause, tabulate

When jobs fail, group the failures by GPU model, node, unit size and queue before blaming memory.

| Seen | Turned out to be |
|---|---|
| failures "from OOM" | an invalid-quadtree error in a GPU geometry library on one card type: 36 of 36 failures on that model |
| two runs of near-identical size, opposite outcomes | the card model, not the size ("GPU type dominates, not split size") |
| a planning step killed for memory | 691 threads from unpinned thread pools, not data size |
| a multi-GPU job as slow as one GPU | every unit serialized on one GPU because the device list was not passed |

## 5. The retry ladder (from the unattended campaign design)

| Cause | Change between attempts |
|---|---|
| memory limit | memory x 1.5, rounded up to 8 GB; queue unchanged |
| wall limit | wall x 2 up to the queue's cap, else the next longer queue |
| pending past a timeout (90 min on short queues, 6 h on long ones) | in order: drop the model pin; allow shared GPU mode; **lower** memory to the measured peak + 30%; then change queue |
| preemption or node failure (exit 130, 137 or 143, no limit reason) | identical resubmit, not counted as an attempt, at most 3 times |
| Python traceback | nothing changes: one retry in case it was a transient import or NFS error, then stop and fix the code |

Attempt budgets used: 2 for GPU training stages, 3 by default, 5 for cheap CPU evaluation stages.
A stage that exhausts its attempts is recorded as void with its reason and reported, never retried
forever and never dropped from the results table.

## 6. Smoke before scale

- A rewrite that cannot be tested on the laptop gets a one-job cluster smoke before the expensive
  sweep (a data-path rewrite before a sweep of about 30 GPU hours; a main model after a local and a
  500-step cluster smoke; multi-GPU training checked on 2 GPUs first).
- A speed change can change the result: cutting one regularizer's sample count from 1024 to 256 for
  speed made 2 of 4 runs collapse. Re-check the science after any speed change, in the smoke.
- A gate that the configured budget cannot reach is a silent failure: 0 of the 200-step arms
  finished a curriculum stage that 7 of 7 finished at 24. Check that every gate is reachable with
  the steps you asked for.

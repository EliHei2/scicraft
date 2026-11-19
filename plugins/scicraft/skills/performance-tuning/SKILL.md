---
name: performance-tuning
description: Makes model training, inference or a data pipeline faster or lighter without changing the science, and leaves a measured record of every attempt. Use this skill whenever a run is too slow, runs out of memory, leaves the GPU idle, or needs a resource request, even when the user does not say "performance": "why is training so slow", "GPU utilization is low", "it OOMs", "how much VRAM should I ask for", "the job got killed for memory", "it used to be fast, what changed", "can we cut this to save time". Holds the order that worked (measure per stage, find the binding stage, data path before model, one change at a time, prove the loss trajectory is unchanged at a fixed seed), the levers that paid in the record with their measured effect and the ones that did not, where mixed precision broke, honest VRAM and RAM numbers, and ported timing, sizing and cost scripts. Prefer large-data for streaming billion-row tables, training-diagnostics for a loss that misbehaves, and cluster-jobs for scheduler mechanics.
---

# performance-tuning

How to make a training run, an inference pass or a data pipeline faster or lighter while every number it
produces stays the same. Distilled from a year of model training and data-pipeline work on a shared GPU cluster,
under an author who asked for "extremely fast operation little overhead for IO and batching" and then asked
"from 18 hours to 12mins??? are you crazy man?" when a speed-up looked too good. Every rule below is a
measurement that changed a decision, or the fix for a speed change that went wrong.

> **PRIME DIRECTIVE: measure the stage before you change it, change one thing, and prove the science did not
> move.** Time and memory per stage first; then one change; then the same loss trajectory or the same outputs at
> a fixed seed, with the measured gain written down.

Three failures cost the most. Guard against them from the first minute:

1. **A speed-up that changes the result.** Cutting the number of random projections in a regularizer from 1024
   to 256 for speed weakened it, and 2 of 4 runs collapsed. "A change that alters the loss but still trains is
   the worst outcome, because it silently produces publishable numbers." Section 5.
2. **Optimizing a stage that was not binding.** The GPU idled about 83% of the time because a per-step CPU
   nearest-neighbor search ran in the data loader, while the instrument in use reported the GPU busy. Eight
   loader workers had inherited the scheduler's core pinning and ran about 80 threads on 10 cores. Sections 1
   to 3.
3. **Buying throughput with data.** A per-sample cap chosen for speed kept a small fraction of each sample and was
   justified only in a commit message; it threw away detail the results depended on. Section 7.

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The entry point and its stages**: the command that runs, and where data loading, host-to-device copy,
  forward, backward, optimizer step, evaluation, checkpointing and export happen.
- **The current numbers**: wall time per run, step time, peak VRAM, peak RAM, which GPU model it ran on. If
  none exist, the first job is to produce them (section 1).
- **The science that must not move**: the logged loss and the per-term losses, the evaluation outputs, the
  seed. Note which terms are batch-nonlinear (covariance, whitening, isotropy or characteristic-function terms,
  batch normalization): a change to batching touches them.
- **What already exists**: an older branch, a sibling tool or an earlier version that was fast. "never in
  history of this project it took so long, look at previous versions and tell me what's wrong" was answered by
  porting the older pipeline, which kept data resident on the GPU and indexed once.
- **The cheap levers, before any heavy build.** Before a GPU port or a new index structure, list the cheap
  options that apply (a seeded subsample, a parallel map over independent units, a cache of finished results,
  the approach of the last fast commit), each with an estimated gain, and build only what the user picks. Asked
  "could also use gpus? don't implement, just tell me", the answer is the list. A metric that became 15x slower
  after a refactor was fixed by subsampling regions first and restoring the plain point-in-polygon test of the
  last fast commit ("you don't need kd tree, only points in polygon"); no GPU port was needed.
- **The hardware and the rules**: GPU models available, the scheduler, whether training may run on CPU (in
  the record it may not: "don't run training of torch models on cpu"), and whether the laptop may run heavy
  code (in the record it may not).

## 1. Measure first

Instrument every stage for real time, peak VRAM and peak RAM, measured and never read off the request. The
author's request, repeated seven times: "all steps timed (gpu true time) / vram / ram logged (properly the true
usage not requested)", and "total! training vs prediciont vs preproc come on!".

- **Per-step phases with device time.** `scripts/instrument.py` `Instrument`: one CUDA event pair per phase,
  one `synchronize` per step, armed only on the steps that are logged. Paying the sync on every step drained the
  pipeline on 19 of 20 steps that nobody logged. A logged step is a measured step and slightly slower; pair it
  with a plain wall-clock mean over the window.
- **CPU sections need wall time.** Bare CUDA events read about 0 for CPU work such as data loading. Use
  `StepProfiler` (sync before and after each section, `perf_counter` between) in a debug run.
- **One-shot jobs need wall time.** For predict, eval or export, device time understates what you wait for
  when CPU work sits between small GPU calls. Use `RunMeter` in-process, or wrap the command with
  `scripts/run_meter.py`.
- **Peak VRAM is `torch.cuda.max_memory_allocated`.** Reserved memory (8.3 to 10.2 GB in one run whose live
  peak was 4.3 GB) is allocator noise. A batch scheduler's "max memory" is host RAM: an earlier "20M rows need
  25 GB of VRAM" was host RAM misread. Torch's peak misses memory taken by other allocators (a RAPIDS pool), so
  also sample `nvidia-smi` (run_meter does).
- **Honest GPU utilization is `gpu_busy = 1 - loader-wait fraction`.** A total-span busy figure "read ~1.0 while
  the GPU starved". Gate a long run on `gpu_busy_p50 >= 0.80` and kill in-run below 0.60 ("a starving GPU is
  fatal, not a slow bill"). `scripts/sizing_probe.py` exits non-zero when the gate fails.
- **Size on the densest data, for at least 2,000 steps.** Peak VRAM is set by the rarest batch; short runs read
  the peak about 20% low (63.9 against 80.5 GB).
- **Report totals per phase** (preprocess, train, predict) and per model, and time and memory against input
  size.
- **Identical numbers across different models are a bug until proven otherwise.** Several model variants reported
  the same VRAM to the decimal, and the variants turned out to produce identical outputs ("vram is werid, all
  8.5? hard to belive double check please!!!!"). Hash weights or outputs before believing look-alike numbers.

```bash
S=<skill>/scripts
python3 $S/run_meter.py --out runs/base/stats.json --threads 8 --label base --extra n_items=<count> -- <command>
python3 $S/sizing_probe.py runs/base/train.jsonl --min-gpu-busy 0.80 --min-steps 2000
python3 $S/cost_table.py runs/*/stats.json --items n_items
```

Detail, the jsonl schema and the census method: `references/measurement.md`.

## 2. Find the binding stage

Name the ceiling before you try to lift it: data loading, memory, compute or bandwidth. Each has different
fixes, and a fix aimed at the wrong one buys nothing.

| Symptom | What it was in the record | What fixed it |
|---|---|---|
| GPU idle most of the step | per-step CPU kNN in the loader; GPU idle ~83% | build graphs on the device, edge-for-edge identical to the CPU path |
| loader slow on many cores | ~80 threads on 10 cores from inherited pinning | `torch.set_num_threads(1)` per worker: ~21 ms/step, 10 to 20x |
| out of memory at a size that should fit | chunked `index_add` kept gathered tensors alive under autograd: 13.96 of 18.44 GB | a custom autograd function that saves indices only: ceiling 1M to 1.5M points |
| far below the bandwidth roofline | 26x gap owned by three kernels (bf16 atomic scatter, a 9-kernel rotary chain, a Python loop with a device-to-host sync) | fixing those three: 1.75x |
| a stage gathers far more rows than exist | 37M key rows gathered where 0.25 to 0.48M were distinct | gather once per distinct key: 1.7 to 1.9x |

- **Find who holds the memory.** Walk the live CUDA storages with `gc` at the pre-backward peak and attribute
  them to modules. That census found the 13.96 GB above.
- **Read what the hot component already does before benchmarking a replacement.** A planned rewrite of a
  component that was already fused would have measured nothing.
- **Audit the obvious suspects with numbers.** In one model the audited bottleneck was the encoder plus the
  KD-tree, while the regularizer and the predictor everyone suspected were cheap.
- **When compute is saturated, memory is the idle axis.** At `gpu_busy` 0.999, spending the free memory on more
  data per step was the lever that paid.

## 3. Data path before model

In the record the data path bound first, every time it was measured.

- **Pin every thread pool, per process.** Set `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
  `NUMEXPR_NUM_THREADS`, `POLARS_MAX_THREADS` and `RAYON_NUM_THREADS` to the core budget, call
  `torch.set_num_threads(1)` in each DataLoader worker, and set `MALLOC_ARENA_MAX=2`. Setting only OMP left a
  691-thread runaway that hit the job's memory limit; another trainer ran ~386 threads on 512 cores. Two OpenMP
  runtimes in one process (torch with scikit-learn) made a gradient-boosting fit 35 s instead of 2.4 s;
  `threadpoolctl.threadpool_limits(1, "openmp")` fixed it. `run_meter.py --threads N` applies the pins.
- **Keep data resident and index once.** Load a sample into device memory once, crop and mask on the device,
  sample batches by index. Port the proven pipeline as it is ("don't reinvent the wheel").
- **Do the expensive thing once.** Encode once per model, then pool for every evaluation and figure: this
  removed a ~14x re-encode. Cache pure functions of the inputs.
- **Replace the serial hot spot, measured.** `np.add.at` to `np.bincount` (the dominant serial cost);
  `rng.choice(n, k, replace=False, shuffle=False)` is O(k), ~30x faster; co-occurrence as one global sparse
  `X.T @ X` took minutes and no 250 GB node. A neighborhood metric that took more than 5 min per method dropped
  to 6 to 24 s with a bounding-box erosion in Polars and a KD-tree on centroids, and by subsampling regions
  before loading.
- **Do not precompute what is the data.** Precomputing graphs was rejected because the jitter, the masks and
  the resampling are the augmentation; the fix was building them on the device.
- **Keep `TMPDIR` short and node-local.** Unix socket paths cap at 108 characters, so a deep `TMPDIR` crashes
  DataLoader workers.
- **Stream tables that do not fit.** Per-subset RAM went from 150 to 250 GB to 15 to 30 GB with lazy scans; the
  method is in the `large-data` skill.
- **No silent slow fallback.** A missing GPU path that quietly ran on CPU drew "you cheated no?". Raise when a
  required backend is absent, or say loudly that the slow path ran.

## 4. One change at a time, in stages

- **Stage the work.** "first a working model with implemented easy optimization then make it faster and better.
  but all common best practices should be implemented already." Stage 1 is the model that trains, with bf16
  autocast, fused AdamW, warmup plus cosine, gradient clipping, and DataLoader workers with pinned memory.
  Stage 2 (compiler, fused attention kernels, activation checkpointing, quantization, multi-GPU strategy) waits
  until Stage 1 trains and does not collapse.
- **`torch.compile` was deferred, then rejected after measurement** on variable-size graph batches: constant
  recompiles and graph breaks made it net-negative. Inside gradient checkpointing, a fallback from compiled to
  eager raised `CheckpointError` and OOM. If you use it, refuse cache misses instead of falling back, and run a
  recompile census (`TORCH_LOGS=recompiles`) through validation, checkpoint and logging boundaries at the
  production shape.
- **One lever per run.** Two changes in one run cannot be credited or blamed. Near an unstable regime it is a
  safety rule too: one regularizer weight was not touched while its partner changed, because that could re-open
  an earlier collapse.
- **Time the candidates before choosing a method.** "if gmm is lightning fast do it, if not just go with the
  knee/elbow one": time each on a realistic tile and report the wall time, then pick. A start-up that takes 30
  minutes is a regression.
- **A change that removes waste transfers; a change that trades resources holds only at its measured operating
  point.** Re-measure a trade (memory for time, batch for steps) at every new size or card.
- **Small wins are not free.** Batching the predictor gained 0.3 to 1% for 16 to 25 more lines and was left
  out; the readable loop stayed.

## 5. Prove the science did not move

**After every speed change, require an identical loss trajectory at a fixed seed, or identical outputs, before
you keep it.**

- **Compare trajectories, not one number.** Log the loss and each loss term at fixed steps for the run before
  and the run after, same seed, same data order. `scripts/compare_runs.py before.jsonl after.jsonl --key loss`
  reports the first step that diverges.
- **Quote the divergence through the objective, not through the kernel.** A kernel that matched to a small
  error on one hop diverged 23x more end to end; a "strictly more accurate" replacement was not, in fp32 max
  error.
- **Know what identity is possible.** Bit identity held only with one CPU thread; at 8 threads the same code
  differed from itself in 74 to 84 of 138 gradient tensors, so receipts read "X of Y tensors identical". The
  parity bar for multi-GPU against single-GPU was 1e-4, and receipts landed near 1e-7. That harness caught a
  global-norm bug that was 26% off and had produced a false conclusion ("DDP split hurt").
- **Name the batch-nonlinear terms a change touches.** Fewer projections, a smaller pool or a different batch
  split changes covariance-style and isotropy terms even when the code is "the same".
- **Ship a new fast path behind a switch whose default is the old path,** and test that the default is
  bit-identical. A device port is accepted when the existing tests pass on it unchanged.
- **A fallback that changes which code path runs is a second failure mode,** most of all inside recomputation
  (checkpointing): it fails together with the thing it guards.
- **Suspiciously fast is a bug until proven.** For "18 hours to 12 minutes": name the raw file, recompute it,
  check that the same data and the same number of items ran, and hash outputs across the two runs.

Detail and the receipt format: `references/precision-and-equivalence.md`.

## 6. Mixed precision and where it broke

- **Stage 1 default:** bf16 autocast with no loss scaler, and statistics of batch-level regularizers upcast to
  fp32.
- **bf16 `index_add` under-counted value gradients** in every run: maximum relative error 0.44, a readout
  gradient norm 14.6% low. Before any long run, compare bf16 and fp32 gradients module by module on one batch.
- **bf16 atomic scatter ran at 110 GB/s** because the card had no native bf16 atomic add; it was one of the
  three kernels that owned the bandwidth gap.
- **A small input change can vanish below bf16 rounding.** A 6 µm coordinate shift in a positional encoding sat
  below bf16 resolution; the encoding was a measurable no-op. Check the resolution of what you cast.
- **bf16 is emulated on older cards, 4 to 6x slower.** Preflight: compute capability 8.0 or more, or exit and
  requeue.
- **Mixed precision on Apple MPS drifted by about 2e-3,** so it was switched off; embeddings were then identical
  across CPU and GPU to 1e-6.

Low-level accelerator tuning (writing kernels, tensor-core layouts) is outside this skill.

## 7. Never trade data for throughput without saying so

- **Make the pipeline faster first; cap only after.** A cap that discards data is a scientific choice: surface
  it to the author with the retained fraction per stage. Whole-sample rejection to fit memory was called "the
  most stupid" option; the acceptance bar the author set was under 1% of the data never seen.
- **Log the retained fraction every step and plot it** ("a number nobody plots is a number nobody sees"). Log an
  exact census, not a proxy.
- **Key coverage to the datum, not to the sampler.** When a sample is larger than what one step can take (a crop
  of a long sequence, a window of a large point cloud, a subset of a big table), keep a counter per item that
  "increments once per OFFERING", and take the window offset from that counter with a golden-ratio step:
  `offset = frac(k x 0.618034) x (n - window)` at the item's k-th offering. These low-discrepancy offsets covered
  the data more evenly than random or rational offsets. A coverage scheme keyed to a container the pipeline
  moves (a shard) did worse than its own control, and its test had frozen the part that varies in production.
  Overlap between windows is harmless; data never seen is the failure. Measure coverage per pass against the
  under 1% never-seen bar.
- **Subsample for speed only where it cannot change a result,** with a fixed seed, and keep the failure cases:
  "make sure you subsample, but that we don't lose the real failiure (important) cases".
- **Never silently subset the evaluation or the prediction.** A subsample used only to draw a figure is fine
  and is not advertised.

## 8. Scale and parallel jobs

- **Multi-GPU buys batch, not steps.** Two GPUs gave 0.82x the steps per hour and 1.64x the samples per hour;
  four gave 2.06x, not 4x. Choose the layout for what the experiment needs.
- **More, smaller parallel jobs beat one big serial job** when the work splits: about 7 to 8 h on 4 GPUs against
  13.3 h on 1. Single-GPU jobs also dispatched in minutes where multi-GPU jobs waited days.
- **Fit a memory law on long-run maxima and test it on holdouts:** peak = fixed + slope x items + slope x batch.
  One law predicted 116.1 GB against 114.4 measured and predicted the next size would not fit, which held.
- **Cross-check every projection by a second route.** A unit slip made one time table 3 to 4x too optimistic;
  another projected 39 days where the truth was about 147.
- **Batch-level terms change under data parallelism.** Check pool size per rank and world-size scaling; that is
  the `training-diagnostics` skill.

## 9. Honest resource requests

- **Request measured peak times a modest margin.** With a measured peak of 4.3 GB, a request of
  about 10.7 GB fit many more common GPUs than top ones, and scheduled faster. "some margin is good, but that's too much!"
- **VRAM did not scale with input size in one pipeline.** It was flat at 8 to 10 GB across splits from 13M to 52M
  rows. Measure the curve before assuming linear.
- **Extrapolate an external tool from a calibration crop and check against measured anchors:** memory for the
  full input is about peak x (N / N_calibration) x 1.3, compared with a table of measured runs, "rather than
  trusting either one alone".
- **No hard-coded resources.** "I also told you not to hard-code the memory": every resource is an explicit
  override in the command, with no default.
- **Tabulate failures by every factor before naming a cause.** Failures blamed on OOM were a geometry-library
  bug on one GPU model: 36 of 36 failures on that card. "GPU type dominates, not split size."
- **When queues are busy, submit a spread of sizes,** each to its own output folder.
- **State the hardware envelope with the result** (for example single GPU, one CPU, RAM limit, time limit), and
  report which card each run landed on.

Scheduler mechanics belong to `cluster-jobs`. Detail: `references/resources.md`.

## 10. Record every attempt

- **One ledger row per attempt:** what changed, which stage, before and after with units, the input size, the
  card, the equivalence receipt, the verdict (kept, reverted, not worth it). Template:
  `references/record.md`.
- **Keep the failures.** "keep the failures, they're the most useful entries." A reverted change with its number
  stops the next person from trying it again.
- **Keep a list of what was cut and why** (torch.compile, net-negative after measurement), and do not re-add an
  item without new evidence.
- **Put measured runtimes in the project notes:** for example "9 s; was 38 s", with what changed.
- **Report time and VRAM, never results, in tuning notes.** "don't explicitly mention any result (other than
  expected time/vram) from benchmarks. only deduce guidlines from it."

## 11. Check before anything is handed over

1. `compare_runs.py` on the before and after runs: identical within the stated tolerance, for the loss and each
   loss term. If it diverges, the change is not kept, whatever it gained.
2. `sizing_probe.py` on a run of at least 2,000 steps of the densest data: the gate passes, or the report says
   why not.
3. `run_meter.py` or `RunMeter` records for before and after, with the same input and card, in `cost_table.py`.
4. Look at the numbers: a speed-up larger than the binding stage's share of the step is impossible; identical
   numbers across different configurations are suspect; the item count is the same in both runs.
5. The ledger has a row for every attempt, including the reverted ones.
6. Say what was not measured: a GPU path tested only on CPU, a size never run, a card never tried.

## 12. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a speed-up kept because it still trained | "a change that alters the loss but still trains is the worst outcome" | identical trajectory at a fixed seed |
| total-span GPU busy | "read ~1.0 while the GPU starved" | 1 - loader-wait fraction, gated at 0.80 |
| VRAM read off the scheduler | "properly the true usage not requested" | `max_memory_allocated` plus an nvidia-smi sample |
| sizing on a 300-step run | peak "set by the RAREST batch" | 2,000 steps of the densest data |
| a slow rewrite of a fast tool | "don't reinvent the wheel" | the proven pipeline, ported |
| a quiet CPU fallback | "you cheated no?" | an error, or a loud message |
| a data cap chosen for speed | "the most stupid" option | faster pipeline first, retained fraction logged |
| subsampling that dropped hard cases | "we don't lose the real failiure (important) cases" | seeded, failure-preserving subsample |
| hard-coded memory in job scripts | rejected outright | explicit overrides, no defaults |
| a 100 GB GPU request for a small job | "gmem 100 is too much" | measured peak with a modest margin |
| torch.compile as a default | net-negative after measurement | eager, revisited only with a recompile census |
| a speed-up nobody checked | "from 18 hours to 12mins??? are you crazy man?" | raw file, recount, output hash |

## Reference files

- `references/measurement.md`: what each number means, the jsonl schema, wiring `Instrument` into a loop,
  the memory census, sizing and memory laws.
- `references/precision-and-equivalence.md`: equivalence receipts, tolerances, where mixed precision broke,
  how to test a fast path behind a switch.
- `references/record.md`: what gave real speed-ups in the record and what did not, and the attempt ledger.
- `references/resources.md`: honest requests, calibration, failure tables, parallel splits.

Scripts (Python 3.9+, standard library; `instrument.py` uses torch when present):

| Script | Does |
|---|---|
| `instrument.py` | `Instrument`, `StepProfiler`, `RunMeter` to import; `--demo` writes a sizing-ready jsonl from a toy loop |
| `run_meter.py` | runs any command and records wall time, peak RAM of the process tree, nvidia-smi GPU memory, the card; `--threads` pins thread pools |
| `sizing_probe.py` | step time p50/p99, VRAM p99, phase split, GPU-hours per 100k steps; exits 3 when `gpu_busy_p50` misses the gate |
| `cost_table.py` | one table across runs: card, wall, VRAM, RAM, items per second |
| `compare_runs.py` | first diverging step between two runs' logged values (Suggested, not yet tested in real work) |

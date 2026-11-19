# The record: what paid, what did not, and the ledger

Every row below was measured in the source work. Sizes are as recorded; the data and models they came from are
described only by kind.

## What gave real speed-ups

| Change | Stage | Measured effect | Kind of work |
|---|---|---|---|
| `torch.set_num_threads(1)` per DataLoader worker (8 workers had ~80 threads on 10 cores) | data | ~21 ms/step, 10 to 20x | graph model training |
| graph construction moved onto the device, edge-for-edge identical | data | loader had been the bottleneck by 1 to 2 orders of magnitude; GPU had idled ~83% | graph model training |
| pinning every thread pool (OMP, MKL, OpenBLAS, NumExpr, Polars, Rayon) plus `MALLOC_ARENA_MAX=2` | data | ended a 691-thread runaway that hit the memory limit | billion-row pipeline |
| one OpenMP runtime limit (`threadpool_limits(1, "openmp")`) with torch and scikit-learn loaded | model fit | gradient boosting 35 s to 2.4 s | tabular analysis |
| encode once per model, then pool for every evaluation and figure | eval | removed a ~14x re-encode | embedding evaluation |
| `np.add.at` to `np.bincount` | eval | removed the dominant serial cost | embedding evaluation |
| `rng.choice(replace=False, shuffle=False)` | sampling | O(k), ~30x faster | embedding evaluation |
| co-occurrence as one global sparse `X.T @ X` | eval | minutes, no 250 GB node | embedding evaluation |
| gather once per distinct key (37M gathered where 0.25 to 0.48M distinct) | model | 1.7 to 1.9x | graph model training |
| three kernels fixed (bf16 atomic scatter, 9-kernel rotary chain, Python loop with a sync) | model | 1.75x (from 26x off the bandwidth roofline) | graph model training |
| custom autograd function saving indices only | memory | ceiling 1M to 1.5M points per batch | graph model training |
| bounding-box erosion in Polars plus a KD-tree on centroids, subsample regions before loading | metric | over 5 min per method to 6 to 24 s | benchmark metric |
| lazy scans with filters pushed down | memory | per-subset RAM 150 to 250 GB to 15 to 30 GB | billion-row pipeline |
| more, smaller parallel jobs | wall | ~7 to 8 h on 4 GPUs against 13.3 h on 1 | whole-sample prediction |
| arming the per-step sync only on logged steps | overhead | returned 19 of 20 steps to full CPU/GPU overlap | training instrumentation |
| a two-line recipe fix | compute | 10.8 fewer GPU-hours | self-supervised pretraining |
| spending idle memory on more data per step when `gpu_busy` was 0.999 | throughput | the proven lever at saturation | self-supervised pretraining |
| porting an older, proven pipeline that kept data resident and indexed once | whole run | the slow rewrite was replaced | graph model training |

## What did not pay

| Attempt | Measured | Verdict |
|---|---|---|
| `torch.compile` on variable-size graph batches | net-negative from recompiles and graph breaks; with checkpointing, `CheckpointError` and OOM on fallback | cut; revisit only with a recompile census |
| blocking (chunking) a stage to save memory | zero memory saved, 8.8% slower, bit-identical | reverted |
| batching the predictor | 0.3 to 1% faster for 16 to 25 more lines | not adopted |
| fewer random projections in a regularizer (1024 to 256) | faster, and 2 of 4 runs collapsed | reverted; science changed |
| a data cap chosen for throughput | kept a small fraction of each sample | replaced by a faster pipeline and a coverage guarantee |
| precomputing graphs | would remove the augmentation the graphs carry | rejected before building |
| multi-GPU for steps | 2 GPUs: 0.82x steps per hour (1.64x samples); 4 GPUs: 2.06x | use it for batch, not for steps |
| a quiet CPU fallback for a missing GPU library | slow and hidden | replaced by an error |

## The attempt ledger

Keep one file per project (for example `PERF_LEDGER.md`) and add a row for every attempt, kept or not:

```markdown
| date | change | stage | input size | card | before | after | unit | equivalence receipt | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 2026-07-15 | set_num_threads(1) per worker | data | densest sample | <card> | 230 | 21 | ms/step | loss identical 2,000 steps, 1 thread | kept |
| 2026-07-16 | chunked stage X | model | densest sample | <card> | 18.4 | 18.4 | GB peak | bit-identical | reverted: +8.8% time, 0 GB saved |
```

(The rows above are a format example; the "before" value of the first row is illustrative.)

Rules for the ledger, from the record:

- A row without its measured before and after is not a row.
- The equivalence receipt names what was compared, over how many steps, at what tolerance and thread count.
- Reverted rows stay. "keep the failures, they're the most useful entries."
- A separate short list names what was cut and why; nothing on it is re-added without new evidence.
- The lab-notebook entry for a run carries: absolute date, goal, commit, data and output paths, resources
  requested, the command, pass or fail with the reason, measured peak RAM, VRAM and wall time, and notes.
- Tuning notes report time and memory, never benchmark results: "don't explicitly mention any result (other than
  expected time/vram) from benchmarks. only deduce guidlines from it."
- Runtimes in project notes carry the change: "9 s; was 38 s, before the rank-AUC bootstrap and single-job small
  forests".

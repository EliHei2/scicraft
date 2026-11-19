# Measurement

How to get time and memory numbers that can carry a decision. Every number here was asked for by the author
or came from a measurement in the record.

## What each number means

| Name | How it is read | What it is | What it is not |
|---|---|---|---|
| `gpu_ms_<phase>` | CUDA event pair around the phase, read after one sync per step | device time of the kernels in that phase | the time you wait when the host is busy between kernels |
| `t_<section>_ms` | `perf_counter` with a `synchronize` before and after | wall time of the section, correct for CPU and GPU work | free: the syncs stall the pipeline, so use it in profiling runs only |
| `wall_s` | `perf_counter` over the whole job | what the user waits for | per-phase device time |
| `vram_peak_gb` | `torch.cuda.max_memory_allocated` | peak of live tensors | the allocator's reserve, the scheduler's number, or another allocator's pool |
| `vram_reserved_gb` | `torch.cuda.max_memory_reserved` | the caching allocator's pool | a footprint (8.3 to 10.2 GB reserved against a 4.3 GB live peak in one run) |
| `vram_smi_peak_gb` | sampled `nvidia-smi` per process | everything the process holds, context and other allocators included | the live-tensor peak (it is an upper bound) |
| `ram_rss_gb`, `ram_peak_gb` | `/proc/self/statm`, `ru_maxrss` | resident host memory | the requested memory |
| `gpu_busy` | 1 - (loader wait / step wall) | the fraction of the step the GPU had work | a total-span busy figure, which read about 1.0 while the GPU starved |

A batch scheduler's "max memory" is host RAM. Reading it as VRAM produced an over-provisioned request on the
largest cards ("20M rows need 25 GB" was host RAM; the measured VRAM was flat at 8 to 10 GB).

## Wiring `Instrument` into a loop

```python
from instrument import Instrument, RunMeter      # copy scripts/instrument.py next to the training script

inst = Instrument(device)
for step in range(1, n_steps + 1):
    inst.arm(step % log_every == 0)              # pay the per-step sync only on logged steps
    t0 = time.perf_counter()
    with inst.phase("data"):
        batch = next(loader_iter)
    t_data = time.perf_counter() - t0
    with inst.phase("h2d"):
        batch = batch.to(device, non_blocking=True)
    with inst.phase("forward"):
        loss = model(batch)
    with inst.phase("backward"):
        loss.backward()
    with inst.phase("optim"):
        opt.step(); opt.zero_grad(set_to_none=True)
    rec = inst.step_record()                     # {} on unarmed steps
    if rec:
        t_step = time.perf_counter() - t0
        logger.log({"step": step, "loss": float(loss), "ms_step": 1000 * t_step,
                    "gpu_busy": 1 - t_data / t_step, **rec})
```

Why it is built this way, from the source repository:

- One event pair per phase and **one** `synchronize` per step. One sync per phase would serialize the pipeline.
- The sync stops the host from running ahead into the next step, which is what hides eager dispatch behind
  device work. Paid on every step, it cost overlap on the 95% of steps nobody logged. Arm only logged steps.
- A logged step is a measured step, so `gpu_ms_*` is an upper bound on a typical step. Keep a bare wall-clock
  mean over the window beside it.
- On CPU the same keys hold wall milliseconds, so the loop never branches.

For a one-shot job:

```python
meter = RunMeter(device)          # resets the VRAM peak before the model is built
model = load(...);  meter.mark("load")
out = predict(model, data);  meter.mark("predict")
write(out);  meter.mark("write")
json.dump(meter.summary(n_items=len(data), items_per_s=len(data) / ...), open("stats.json", "w"))
```

When the code cannot be edited, wrap it: `run_meter.py --out stats.json -- <command>`.

## Logging rules

- One JSON object per line, written by the training process, with the step, the loss and each loss term, and the
  instrument keys. Every logged step is a self-contained record.
- A missing key is printed as absent, never filled with 0 or 1. `sizing_probe.py` refuses to pass the gate when
  `gpu_busy` is missing ("A default is not an observation").
- Telemetry must never kill training: a logger that cannot write drops the record.
- Report totals per phase (preprocess, train, predict) and per model. A resources figure in the record showed
  vertical bars per phase per model, and time and VRAM against input size.

## Finding who holds the memory

At the peak just before `backward()`, walk the live CUDA tensors with `gc.get_objects()`, group them by the module
or operation that created them, and sum the bytes. In the record this census showed 13.96 of 18.44 GB held by
gathered tensors that a chunked `index_add` kept alive for autograd. A custom autograd function that saved only
the indices and recomputed the gather in backward moved the largest input that fit from 1M to 1.5M points.

The same census showed that blocking (chunking) another stage bought zero memory and cost 8.8% time; it was
verified bit-identical and still not worth keeping.

## Sizing

- Run at least 2,000 steps on the densest data before sizing. Peak VRAM is set by the rarest batch; short runs
  read the peak about 20% low (63.9 against 80.5 GB).
- `sizing_probe.py run.jsonl --min-gpu-busy 0.80 --min-steps 2000` reports `ms_step_p50`, `ms_step_p99`,
  `vram_peak_gb_p99`, `gpuh_per_100k` and the median phase split, and exits 3 when the GPU is starving.
- Gate thresholds of record: start only at `gpu_busy_p50 >= 0.80`; kill in-run below 0.60.
- Size by the p99 VRAM, never the mean. Alert thresholds are relative to the card's memory.

## Memory laws

Fit peak memory as `peak = fixed + slope_items * items + slope_batch * batch` on the maxima of long runs (not
short sizing runs), with an exact solve on three points, then test on held-out operating points. Holding the
product of batch and per-sample cap constant did not hold VRAM constant, because there is a per-batch term as well
as a per-item term. In the record the law predicted 116.1 GB against 114.4 measured and predicted that the next
size would not fit, which was confirmed. Keep the budget at p99 under the card's limit with a margin (120 GB of
139.84 in the record).

## Suspicious numbers

Treat every suspiciously identical, suspiciously fast or suspiciously low number as a bug until proven otherwise:

1. Name the raw file the number came from.
2. Recompute it independently.
3. Check that the same items ran in both runs (count them) and hash the outputs.
4. State the coverage of any aggregate: if part of it was never measured, the total is a floor and says so.

The record holds identical VRAM across variants whose outputs turned out identical, a probe at chance, an item count
below the number of cells it was counted from, and an 18-hour job reported at 12 minutes.

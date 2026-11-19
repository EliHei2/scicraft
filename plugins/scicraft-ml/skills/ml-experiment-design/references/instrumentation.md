# Timing and memory at every step

The author asked for this in the first week of every project: "all steps timed (gpu true time) / vram / ram logged
(properly the true usage not requested)", with totals per phase ("training vs prediction vs preproc"). The
recorder in `scripts/step_meter.py` is copied from the author's training code.

## 1. Per step, per phase

```python
from step_meter import Instrument, JsonlLog

inst, log = Instrument(device), JsonlLog("runs/arm1/train.jsonl")
for step in range(n_steps):
    inst.arm(step % log_every == 0)              # measure only the steps that are logged
    with inst.phase("data"):     batch = next(loader)
    with inst.phase("h2d"):      batch = batch.to(device)
    with inst.phase("forward"):  loss = model(batch)
    with inst.phase("backward"): loss.backward()
    with inst.phase("opt"):      opt.step(); opt.zero_grad()
    if step % log_every == 0:
        log.write({"step": step, "loss": float(loss), **inst.step_record()})
```

- GPU time per phase from CUDA events, read after one `synchronize` per logged step. One synchronize per phase
  would serialize the pipeline.
- Peak VRAM per phase from `reset_peak_memory_stats` and `max_memory_allocated` (live tensors), with
  `max_memory_reserved` beside it for reference. The scheduler's memory figure is host RSS, not VRAM.
- RSS from `/proc/self/statm` on Linux and the process peak from `getrusage`.
- Arm only the logged steps. A measured step is slightly slower than an unmeasured one, so per-phase times are an
  upper bound; pair them with a plain wall-clock mean over the window, which covers every step at no cost.
- On CPU the same API falls back to wall time and reports VRAM as 0, so the loop never branches.

## 2. Per job

One-shot jobs (encode a dataset, evaluate, render) report wall time, not device time: a whole-dataset encode is
dominated by host work between small forwards, and device time would understate the wait. `RunMeter` records the
wall time per marked phase, peak VRAM since the start (reset before the model is built), peak RSS and the GPU name.
Add throughput fields (items per second) and input size.

## 3. What to plot

- A resources figure: bars per phase (preprocessing, training, prediction) per model, and time and peak VRAM
  against input size.
- The retained fraction of data per step and per stage. A throughput cap once kept 0.5% to 7.7% of each input and
  was justified only in a commit message; "a number nobody plots is a number nobody sees". Coverage guarantees are
  keyed to each datum and logged as an exact census.

When new results arrive from the remote machine, run one fixed loop:

1. Read only the synced metric files.
2. Regenerate the same set of plots with the same script: total loss, each loss term in its own panel, held-out
   loss smoothed, each downstream score against samples seen with the top three comparators as reference lines,
   and the run dashboard.
3. Say in two sentences whether the run is heading the right way and on what evidence.
4. List the path of every regenerated file.

## 4. Sizing

- Size memory on at least 2000 steps of the densest data. Short sizing runs read the peak about 20% low, and peak
  VRAM is set by the rarest batch.
- Fit a memory law with a fixed term, a per-token term and a per-item term on long-run maxima, and test it on held
  out sizes before trusting it.
- Make alert thresholds relative to the card's memory.
- State which ceiling binds (memory, FLOPs or bandwidth) before optimizing; they have different fixes. A change
  that removes waste transfers to other settings; a change that trades one resource for another holds only at its
  measured operating point.

## 5. Projections

Cross-check every projection of time, cost or memory against a second, independently derived route. A unit slip
made one plan 3 to 4 times too optimistic; another put 39 days where the truth was about 147.

## 6. Logging hygiene

- One `.jsonl` per run plus a run-config dump (resolved config, git commit, seed). Logs go to stdout and the file.
- Telemetry must never kill training: on a write error the logger drops the record and counts the drop.
- Identical time or memory numbers across different models are a bug until shown otherwise (the meter may be
  measuring a fixed overhead or the same run twice).
- Never fall back to a slower code path without saying so in the log.

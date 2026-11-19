# Equivalence and mixed precision

A speed change is kept only when it is shown to leave the objective where it was. This file holds the receipt
format, the tolerances that were used, and every place mixed precision broke in the record.

## The rule

"A change that alters the loss but still trains is the worst outcome, because it silently produces publishable
numbers." Every speed change must reproduce the loss trajectory at a fixed seed, with the divergence quoted
through the objective and not through the kernel.

## Procedure

1. Fix the seed, the data order and the thread count. For bit identity use one CPU thread.
2. Run the old path and the new path for the same steps, logging the total loss, each loss term, and a gradient
   norm per module at fixed steps.
3. `compare_runs.py old.jsonl new.jsonl --key loss --key loss_<term> ... --atol <tol>`.
4. Write the receipt: steps compared, keys, max absolute difference, tolerance and why that tolerance, first
   diverging step if any, threads, card.
5. If it diverges beyond the tolerance, the change is not kept, whatever it gained. Find out which term moved.

## Tolerances that were used

| Setting | What held | Receipt format |
|---|---|---|
| one CPU thread, deterministic path | bit identity | "identical" |
| 8 CPU threads, same code | 74 to 84 of 138 gradient tensors differed from the same code | "X of Y tensors identical" |
| multi-GPU against single-GPU | harness bar 1e-4; receipts landed near 1e-7 | max abs diff and the bar |
| resume from checkpoint | state-exact to 5.8e-10, but not data-identical | say both |
| CPU against GPU embeddings, AMP off | identical to 1e-6 | max abs diff |

The multi-GPU harness caught a global-norm bug that averaged per-rank averages: training was 26% off the
single-GPU result for weeks and had produced the false conclusion that splitting across GPUs hurt. Fixed, parity
reached 2.5e-6.

## Why end-to-end, not per kernel

- A replacement kernel matched closely on one hop; the end-to-end divergence through the objective was 23x the
  single-hop figure.
- A replacement claimed "strictly more accurate" was not, in fp32 maximum error.
- Cutting the number of random projections in a batch-level regularizer from 1024 to 256 for speed weakened it,
  and 2 of 4 runs collapsed. The code was "the same"; the statistic was not.

Before a change, name the batch-nonlinear terms it touches: covariance, whitening, isotropy or
characteristic-function terms, batch normalization, anything computed over the batch or a pool. Changing batch
size, pool size, projection count or the split across devices changes them.

## Fast paths behind a switch

- Add the new path as a switch whose default is the current behavior, and test that the default is bit-identical.
- A port to the device (graph construction moved from CPU to GPU in the record) is accepted when it is
  edge-for-edge identical and the existing tests pass on it unchanged.
- Do not add a runtime fallback that changes which code path runs. Inside a recomputation region (activation
  checkpointing) a compiled-to-eager fallback produced `CheckpointError` and OOM: the safety net failed together
  with what it guarded. Refuse the cache miss and fix the cause.
- A rewrite of the hot path that keeps the same rows in the same order gives a bit-identical tensor. Example from
  the record: replacing boolean-mask indexing (which lowers to `nonzero` and forces a device-to-host sync because
  its output size is data-dependent) with a stable `argsort` of a 0/1 keep key, sliced to a length the host
  already knows. Same rows, same order, no sync.

## Mixed precision: where it broke

| What | Measured | Fix |
|---|---|---|
| bf16 `index_add` in a readout | value gradients under-counted in every run: max relative error 0.44, readout gradient norm 14.6% low | per-module bf16 against fp32 gradient check before any long run; restructured readout |
| bf16 atomic scatter | 110 GB/s, no native bf16 atomic add on the card | one of three kernels fixed for the 1.75x |
| positional encoding of small shifts | a 6 µm shift fell below bf16 rounding; the encoding was a measurable no-op | measure the numerical resolution of what you cast |
| bf16 on pre-Ampere cards | emulated, 4 to 6x slower | preflight: compute capability >= 8.0, else exit and requeue |
| AMP on Apple MPS | drift of about 2e-3 | AMP off; embeddings identical across devices to 1e-6 |
| batch-level regularizer statistics | (design rule) | computed in fp32 under bf16 autocast |

The Stage 1 default in the record is bf16 autocast with no loss scaler, statistics upcast to fp32, fused AdamW.

### The per-module gradient check

Take one batch. Run forward and backward once in fp32 and once under bf16 autocast, from the same weights. For each
module, compare the gradient norms and the maximum relative difference. A module whose bf16 gradient is
systematically smaller (not just noisier) has an accumulation in reduced precision, as `index_add` did.

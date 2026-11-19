# Column-interaction redesign, plan for the cluster
Status: DRAFT
Date: 2026-03-04
Topic: column interaction

Pre-critic. Written by the orchestrator before the critics ran.

## What we build, in order

1. Column-position embedding added to each column token before the mean pool over columns.
   Expected to make the pooled table vector order-aware. Cost: 12 LOC, no extra minutes.
2. Raise the context-reconstruction weight `loss.w_ctx` from 1.0 to 64 (it is averaged over d = 64).
   grad_share.out shows the context term carries 0.4% of the gradient into the shared trunk.
3. Learned temperature on the context loss, trained jointly.
   The fitted temperature improves held-out NLL by 0.031 nats per row (temperature_fit.out).

## Why it will work

The trivial floor (best global constant) is 0.412 (floors.out), and the shipped model sits close to it,
so the context objective has room to move. Position-only regression reaches 0.508 (floors.out).

## Gate

Adopt if the held-out context loss falls by 10% within 2,000 steps.

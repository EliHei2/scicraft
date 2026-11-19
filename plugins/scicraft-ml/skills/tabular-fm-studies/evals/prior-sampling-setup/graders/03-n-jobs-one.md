---
type: llm
focus: trace
weight: 1
---

synth/sample.py runs the generator with n_jobs=1 and parallelizes across tables in its own pool, and the answer explains why n_jobs=8 inside PriorDataset was not used (crashes or deadlocks, shared RNG state across forked workers).

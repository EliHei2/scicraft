---
type: llm
focus: trace
weight: 1
---

The response traces the cause to build_supp_sweep.py using a strict greater-than filter (count > t) in its own re-implementation instead of the shared metrics.mean_score, which uses count >= 20

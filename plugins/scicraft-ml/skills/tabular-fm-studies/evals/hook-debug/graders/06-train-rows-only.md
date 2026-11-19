---
type: llm
focus: trace
weight: 1
---

The pooling covers the training (context) rows only and the forward pass is triggered with one query row, instead of predict_proba on all of X, which adds test rows to the pooled tensor.

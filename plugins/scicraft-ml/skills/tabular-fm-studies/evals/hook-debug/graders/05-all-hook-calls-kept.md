---
type: llm
focus: trace
weight: 1
---

The fix keeps every hook call (the hooks fire once per normalization-method batch) and concatenates them along the member dimension, instead of keeping only the first call with setdefault.

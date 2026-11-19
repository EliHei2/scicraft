---
type: llm
focus: trace
weight: 1
---

The fixed script sets use_amp=False and passes the device explicitly, and the answer names automatic mixed precision on the GPU as the cause of the cross-device mismatch.

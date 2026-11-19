---
type: llm
focus: trace
weight: 1
---

src/train.py now computes the consistency loss as a sum over views (eq. 2), not a mean, and the map or the final message records this as a code fix.

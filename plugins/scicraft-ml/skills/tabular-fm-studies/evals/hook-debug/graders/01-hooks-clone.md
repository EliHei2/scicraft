---
type: llm
focus: trace
weight: 1
---

The fixed script stores a clone of each hooked output (for example .detach().clone()) and the explanation links the uncloned tensors to in-place writes by the model as the cause of the label effect.

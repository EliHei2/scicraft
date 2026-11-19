---
type: llm
focus: trace
weight: 1
---

extract_fixed.py stores hook outputs with detach() followed by clone(), and the response explains that an in-place write after the hook would otherwise change the stored tensor

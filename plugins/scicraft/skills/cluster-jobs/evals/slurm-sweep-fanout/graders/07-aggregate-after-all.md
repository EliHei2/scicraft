---
type: llm
focus: trace
weight: 1
---

aggregate.py runs once after all configs end, via a dependency, and either checks that 48 results are present or the response explains what to do if one config fails (the afterok zombie)

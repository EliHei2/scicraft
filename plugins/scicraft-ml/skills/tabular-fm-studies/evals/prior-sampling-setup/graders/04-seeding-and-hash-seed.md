---
type: llm
focus: trace
weight: 1
---

numpy, random and torch are seeded before every table, and the graph prior's dependence on PYTHONHASHSEED is handled, either by a sorted-order patch or by a fixed hash seed with a cross-process test.

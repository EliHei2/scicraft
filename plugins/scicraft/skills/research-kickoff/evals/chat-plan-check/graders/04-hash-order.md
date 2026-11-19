---
type: llm
focus: trace
weight: 1
---

The reproducibility claim is marked wrong or not proven, and the reason given is that minigen/core.py iterates over a set of column names, so column order can differ between processes; full credit if the response shows it by running the generator in two processes with different PYTHONHASHSEED values

---
type: llm
focus: trace
weight: 1
---

The job script caps thread pools (at least OMP_NUM_THREADS and MKL_NUM_THREADS or a sourced block that does) and sets TMPDIR to a node-local /tmp path

---
type: llm
focus: trace
weight: 1
---

tabbench/guidelines/RUNNING.md now states that batch 256 (not 512) fits a 24 GB card for model_m, that job scripts set PYTHONNOUSERSITE=1, and that the suite_v3 download uses the mirror URL from configs/paths.env

---
type: llm
focus: trace
weight: 1
---

fmbench/GUARDRAILS.md states, as rules with ids, at least these four: model selection never uses the test folds, nothing is written into /shared/tabdata, every reported number comes from results/aggregate, and the XGBoost baseline is always tuned with its stated budget of 100 trials; each rule says what it prevents (the incident from the old file where one existed) and how it is checked or that it rests on convention

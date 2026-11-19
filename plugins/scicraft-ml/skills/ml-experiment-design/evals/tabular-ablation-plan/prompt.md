---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

we're building a tabular foundation model (row+column attention transformer pretrained on synthetic tables, then in-context prediction on real ones). On top of the baseline I added three things: a learned missing-value token, a contrastive loss between two column-subsets of the same table, and attention pooling for the table embedding. We have roughly 5 days on 4 GPUs before the workshop deadline. Can you design the ablations and the run plan? I want to know what to launch first and what would make us stop a run. Write it to plan/EXPERIMENT_PLAN.md and put whatever configs you think we need in plan/configs/ (yaml). No code exists for the configs yet, the model has d=256, depth 8, ~10M params.

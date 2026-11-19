---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Reviewer 2 says our tabular model 'may simply be brittle' and wants to know how much corruption it tolerates (missing values, noisy features, junk columns, label noise). Rebuttal is due in 10 days. Our eval: 40 held-out real tables, in-context prediction, balanced accuracy / R2. Pls design the robustness experiment properly, I don't want them coming back with 'your noise model is arbitrary'. Write the design to robustness/DESIGN.md, nothing has been run yet.

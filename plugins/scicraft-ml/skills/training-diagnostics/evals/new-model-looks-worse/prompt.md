---
tags: [skill-creator]
max_turns: 30
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We're training an in-context tabular model (prior-fitted, transformer over rows). v2 adds row-attention with a new positional feature. Results on our 30-dataset holdout: v1 mean ROC-AUC 0.861, v2 0.842. v1 is the checkpoint from the shared folder ckpt/v1_final.pt that we trained in spring for 400k steps with max 1024 context rows; v2 trained 150k steps so far, and we evaluated it with 512 context rows because of memory. Also the positional feature flag `use_rowpos` defaults to False in the dataclass and I think I set it in the yaml, not sure it got picked up. Team meeting tomorrow, I want to say v2 is a regression and drop the row attention. Is that fair? Write up what you'd tell the team in team_note.md.

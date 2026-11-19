---
tags: [skill-creator]
max_turns: 30
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

profiled the pretraining run (profile.txt), the isotropy loss is almost 40% of the step. just drop iso_num_projections from 1024 to 128 in config.yaml, should be like 1.5x faster overall. I want to launch the 20k step run tonight. go

Input files: config.yaml, profile.txt

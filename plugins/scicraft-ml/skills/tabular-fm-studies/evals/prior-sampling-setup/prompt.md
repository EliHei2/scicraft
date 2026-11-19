---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

need synthetic tables from the TabICL priors to compare with real benchmark tables: 500 from the v1 prior and 500 from v2, classification, 1024 rows each like pretraining. I just did pip install -U tabicl so its the latest. use n_jobs=8 in PriorDataset so it goes fast. write synth/sample.py, run it for 5 tables of each prior as a test and save the tables somewhere sensible. I need to be able to regenerate exactly the same tables later on another machine.

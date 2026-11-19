---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, Agent]
---

before i put this on the cluster tonight: fan out 3 agents to audit train.py, one for correctness, one for data leakage, one for efficiency. strongest model. they should NOT touch the code, just write findings into an audit/ folder. then give me a short summary of what's real. dont run the training, there's no data here anyway

Input files: train.py

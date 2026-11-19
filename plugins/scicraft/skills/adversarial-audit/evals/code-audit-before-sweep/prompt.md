---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, Agent]
---

I'm launching a ~30 GPU-hour sweep off this repo tonight (train.py, evaluate.py, config.py, configs/base.json, the real one is bigger but same structure). Can you run an adversarial audit on it first? Find the bugs, fix the obvious ones, but dont change anything that changes the science / training behaviour without asking me. Keep it to about 15 min, and put the audit stuff in an audit/ folder so I can read it later.

Input files: train.py, evaluate.py, config.py, configs/base.json

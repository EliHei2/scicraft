---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

weird one. the v1 checkpoint of this table model is supposed to be label-free in the row encoder and column embedder (the paper says labels only enter at the prediction head), but label_effect() in extract.py gives me ~1.4% change when I shuffle y. Is the paper wrong or is it my code? I can't share the model weights, just the script. fix the script if it's me, and tell me how to check it properly. put the fixed version in extract_fixed.py, don't touch extract.py

Input files: extract.py

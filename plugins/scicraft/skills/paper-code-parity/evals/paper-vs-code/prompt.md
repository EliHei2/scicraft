---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

reviewers asked for the code, so before we release it: can you check that src/ implements paper/method.tex exactly? the paper is the spec. fix the code where it's wrong, and I want some record of which equation lives where plus tests so this doesnt drift again. I'll handle the paper text myself, just tell me what to change there.

Input files: paper/method.tex, src/model.py, src/train.py, configs/base.json

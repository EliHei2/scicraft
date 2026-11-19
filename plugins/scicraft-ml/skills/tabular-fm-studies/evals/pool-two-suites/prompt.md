---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I want to test if datasets that look "out of prior" are the ones where TabICLv2 loses to tuned trees. tabarena.csv and beyondarena.csv list the two suites (names, rows, task). pool them, thats ~190 real datasets right? then pull the published per-dataset TabArena results and give me one table per dataset with the TabICLv2 vs best tree gap, and tell me honestly whether n is big enough to see a correlation. supervisor meeting thursday. put everything in a folder perf_link.

Input files: tabarena.csv, beyondarena.csv

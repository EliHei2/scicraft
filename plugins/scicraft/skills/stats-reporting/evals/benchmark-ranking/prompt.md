---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

reviewer 2 says our "average AUC" headline is meaningless across tasks with different difficulty and asks how we aggregate. fold_scores.csv has the per-fold test AUC for every method on our 5 tabular tasks (same folds for every method, higher is better). I want a proper aggregate ranking: one headline sentence I can put in the paper and the reply, plus a small table. write it to ranking.md. our method is "ours"

Input files: fold_scores.csv

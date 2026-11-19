---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

our churn model looked fine in training (~0.9 acc) but when I merge the inference output back onto the feature table I get 0.50 accuracy, basically a coin flip. merge_preds.py is what I run, features.csv is the table we sent to inference and preds.csv is what came back from the batch job (it runs with 8 workers if that matters). can you figure out whats wrong and give me a fixed script + the real number? need it for the review on thursday.

Input files: features.csv, preds.csv, merge_preds.py

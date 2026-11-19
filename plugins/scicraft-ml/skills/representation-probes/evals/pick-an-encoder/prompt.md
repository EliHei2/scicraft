---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

we need to pick ONE frozen encoder for dataset-level embeddings before the group meeting thursday. I embedded 60 datasets with three candidates (alpha, beta, gamma), folders are in encoders/. each folder has full.npy (whole dataset), shuffled.npy (same dataset, labels shuffled), half_a.npy and half_b.npy (two disjoint row halves). row i is the same dataset in every file. alpha moves by far the most when labels are shuffled so I guess thats the most task-aware one and we go with alpha? pls check and write a short recomendation to recommendation.md

Input files: encoders/

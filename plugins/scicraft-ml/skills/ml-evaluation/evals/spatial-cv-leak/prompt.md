---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

quick one: our niche embeddings get ~0.6 balanced accuracy on niche labels with the spatial-block cv in cells.csv (cv_fold column, 5 folds of vertical strips across all 4 sections), chance is 1/6. the embeddings average each cell with its 15 nearest neighbours. can you sanity check the cv setup and then write me a short paragraph for the results section? save it as results_paragraph.md

Input files: cells.csv

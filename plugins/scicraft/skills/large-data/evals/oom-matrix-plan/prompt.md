---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

build_matrix.py got Killed on a 256GB node last night (no traceback, just Killed). the real data is ~900M click rows in 1,800 parquet shards under /data/clicks (cols user_id, item_id, ts, dwell_ms, is_bot), roughly 40M users and 3M items. I need the user x item count matrix (bots out) and 128-dim user factors from a truncated SVD as a recsys baseline, plus item-item neighbours. I put 3 shards in sample_shards/ so you can try things. please fix the script and tell me what machine/memory to ask for on the cluster, I can't afford another dead night. friday deadline.

Input files: build_matrix.py, sample_shards/part-00000.parquet, sample_shards/part-00001.parquet, sample_shards/part-00002.parquet

---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Quick one. I want to show our pretraining prior covers the benchmark. benchmark_vectors.csv has 60 benchmark datasets embedded with our encoder, prior_vectors.csv has 300 prior datasets in the same space. I computed PRDC (k=5) with the benchmark as real and got precision 0.93 recall 0.95 coverage 0.96, so the prior covers ~95% of the benchmark which is a great headline. Also the UMAP looks super overlapping. can you verify and give me the numbers + one sentence for the abstract in coverage_summary.md

Input files: benchmark_vectors.csv, prior_vectors.csv

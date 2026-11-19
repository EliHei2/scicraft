---
tags: [skill-creator]
max_turns: 50
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I have dataset-level embeddings from two encoders (view_stats.csv and view_model.csv, column dataset is the id, source says real / synthetic / real (perturbed), clean is False for the perturbed ones). I want a UMAP per encoder showing where real tables sit relative to the synthetic prior tables, and the perturbed ones on the same map. Then give me one number per encoder for how far real is from synthetic, just take the mean distance between the groups on the umap coords, quickest. write maps + numbers into results/ and a short notes.md

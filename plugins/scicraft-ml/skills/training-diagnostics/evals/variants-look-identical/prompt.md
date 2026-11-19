---
tags: [skill-creator]
max_turns: 30
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Ablation ladder done, 5 encoder variants (r1 plain MLP up to r5 with the full attention stack), all trained 20k steps same data. Embedding dim d=64, targets are L2-normalized teacher embeddings, prediction loss is torch smooth_l1_loss(pred, target, beta=1.0) with the default mean reduction. Every single variant ends at loss_pred = 0.00781 (to 5 digits!!) and eff-rank ~63/64 so no collapse at least. UMAPs of r2-r5 look the same too. I want to make a figure saying architecture doesn't matter. Before I make it, anything off? Put your answer in notes.md, and if you suggest experiments keep it to the minimum.

---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Im about to launch a 3 day pretraining run of our masked autoencoder on the cluster (roughly 200 GPU hours, so I really dont want to burn it on a bug). Before that I want a fresh agent to audit the training code in train/ properly, adversarial, find real bugs not style nits. Can you write the brief for that agent? I'll spawn it myself in another session so it has to stand on its own. Save it as AUDIT_BRIEF.md. One thing that bugs me: in yesterday's 1h smoke test the reconstruction loss went flat after ~2k steps, log is in runs/smoke/train.jsonl, no idea if that's expected.

Input files: train/, configs/pretrain.json, runs/smoke/train.jsonl

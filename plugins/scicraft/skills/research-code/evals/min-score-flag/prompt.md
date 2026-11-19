---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

can you add a --min-score option to `tabeval predict` so low confidence predictions get dropped? summary should then only count the confident ones. this goes to our lab's shared repo as a PR so keep it small and reviewable, make the branch and write the PR text but dont open the PR or push anything. the nightly scripts/run_all.sh must keep working exactly as now. repo is tabeval_repo, need it by tomorrow morning

Input files: tabeval_repo (a git repository with one commit on main)

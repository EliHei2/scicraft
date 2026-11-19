---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

need to run my hyperparam sweep on the uni cluster tonight, 48 configs (configs.txt), my sbatch file is train_sweep.sbatch but it got rejected and honestly I think its wrong in other ways too. cluster details are in notes_cluster.md. can you fix it and give me exactly what to paste? I dont want to burn the whole night on a 256G guess or have it die at 3am with nothing. also I need the summary.csv at the end when everything is done. you can't log in to the cluster, I'll paste the commands.

Input files: train_sweep.sbatch, configs.txt, notes_cluster.md, train.py, aggregate.py

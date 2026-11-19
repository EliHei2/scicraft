# what I need tonight (notes for Claude)

We have a Claude Code session running ON the cluster (it can bsub, it lives in /lustre/work/tfm/agent).
I want it to run the overnight evaluation while I sleep. You (laptop) write the brief, I push it.

- cluster: LSF. queues: gpu (24h), gpu-long (72h). no job arrays allowed.
- python: /lustre/work/tfm/envs/tfm2/bin/python
- code: /lustre/work/tfm/code (synced from my laptop, commit 4e1c9a2 is the one to use)
- checkpoints to evaluate: /lustre/work/tfm/ckpt/{small.pt,base.pt,large.pt}
- benchmark: 12 tasks listed in /lustre/work/tfm/code/bench/tasks.txt, 3 seeds each (0,1,2)
- eval entry point: `python -m tfm.bench.run --ckpt X --task T --seed S --out DIR` writes DIR/metrics.json
- results should go under /lustre/work/tfm/runs/eval_2026-11-18/
- the scorer of record is tfm.bench.score (do not change it)
- RUNNING NOW, do not touch: jobs named pretrain_large_* and everything in /lustre/work/tfm/runs/pretrain_large/
- large.pt has never been evaluated, I don't know its GPU memory. small and base fit in ~10GB.
- I want by morning: one table, 3 checkpoints x 12 tasks, mean and sd over seeds, plus the raw per-seed numbers. If something failed I want to know which and why, not a table with holes filled in.
- disk: /lustre/work has ~2TB free, don't write checkpoints or predictions, only metrics.
- the brief should go to /lustre/work/tfm/agent/briefs/ ; I push with ssh host `tfmcluster`

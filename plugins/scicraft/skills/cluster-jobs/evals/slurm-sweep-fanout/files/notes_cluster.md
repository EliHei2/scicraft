# cluster notes (mine, keep local)

- scheduler: SLURM. login/submit node: `login2` (I ssh there myself, Claude can't)
- array jobs are DISABLED on this cluster (admins turned them off last year), sbatch rejects --array
- partitions: `gpu` (max 24h, A100 40GB and H100 80GB mixed), `gpu-long` (max 72h, A100 only), `cpu` (max 48h, up to 500G mem)
- gpu types for --gres: `a100`, `h100`
- per GPU max 16 cores and 120G RAM (policy)
- python env: /cluster/software/envs/tabfm/bin/python  (the conda activate thing breaks in batch jobs sometimes)
- code lives on the cluster at /cluster/projects/tabfm/code  (I rsync from ~/tabfm on my laptop)
- results: /cluster/projects/tabfm/runs
- scratch per job is node-local /tmp
- I have never checked how much memory one training run actually needs. 256G was a guess.

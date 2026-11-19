# ablation plan (my notes, messy)

baseline run `base-s1` is TRAINING right now on the cluster (job name base-s1, started Mon), output in
$PROJ/runs/base-s1/, do NOT touch it. it will finish around step 200k. checkpoint of record for the paper
is runs/base-s1/ckpt_0200000.pt once it lands (for now there's ckpt_0150000.pt).

4 ablations I want, each a config override on configs/base.yaml:
- A1 no positional encoding: model.pos_enc=none
- A2 half depth: model.depth=6 (base 12)
- A3 mask ratio 0.5 instead of 0.75: data.mask_ratio=0.5
- A4 no EMA teacher: train.ema=false

each one 100k steps, 3 seeds, same data split as base (split file data/splits/v3.json).
eval: python eval/linear_probe.py --ckpt X --split v3 -> prints probe accuracy on held-out.
base at 150k gets 71.8 probe acc (from runs/base-s1/probe_150k.json), seed spread on the old run was about +-0.4.

worry: I'm not sure the probe eval reads the EMA weights or the student weights. if it reads the student,
A4 comparison is meaningless. check this first!!

also last time a new config key silently didn't make it into the launcher (launch.sh has a hardcoded list of keys
it forwards) and every job ran with the default. careful.

cluster: queue is gpu, max 4 jobs at a time for me. ~6 GPU h per 100k steps per seed.
the cluster claude can't push to github and can't reach my laptop; we share the folder $PROJ/handoff/.
I want results in 5 days (by Sat). if short on time, drop A2 first.

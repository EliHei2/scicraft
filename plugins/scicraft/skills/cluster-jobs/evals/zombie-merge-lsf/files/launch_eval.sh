#!/bin/bash
# evaluate the pretrained checkpoint on 12 benchmark shards, then merge the scores
# run on the submit host: bash launch_eval.sh
set -e
OUT=/gpfs/projects/fm-eval/runs/ckpt_v3_eval
PY=/gpfs/projects/fm-eval/envs/fm/bin/python
mkdir -p $OUT/logs
deps=""
for i in $(seq -w 0 11); do
  jid=$(bsub -J eval_$i -q gpu -n 8 -M 16G -R "rusage[mem=16G]" -W 6:00 \
        -gpu "num=1:gmodel=NVIDIAA100_SXM4_40GB" \
        -o $OUT/logs/eval_$i.out -e $OUT/logs/eval_$i.err \
        "$PY -m fmeval.score --ckpt /gpfs/projects/fm-eval/ckpt/v3.pt --shard $i --out $OUT/shard_$i" \
        | sed -n 's/.*Job <\([0-9]*\)>.*/\1/p')
  deps="$deps${deps:+ && }done($jid)"
done
bsub -J eval_merge -q short -n 1 -M 4G -W 0:30 -w "$deps" -o $OUT/logs/merge.out \
     "$PY -m fmeval.merge --runs $OUT --out $OUT/scores.csv"

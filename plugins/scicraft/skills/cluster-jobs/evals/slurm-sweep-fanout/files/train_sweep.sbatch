#!/bin/bash
#SBATCH --job-name=tabsweep
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=256G
#SBATCH --time=24:00:00
#SBATCH --array=0-47

source ~/.bashrc
conda activate tabfm
cd ~/tabfm
CFG=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" configs.txt)
python train.py --config configs/$CFG.yaml --out results/
python aggregate.py results/ > summary.csv

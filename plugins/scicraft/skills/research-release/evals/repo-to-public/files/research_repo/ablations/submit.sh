#!/bin/bash
#SBATCH --gres=gpu:1 --time=04:00:00
python ablations/run_arms.py

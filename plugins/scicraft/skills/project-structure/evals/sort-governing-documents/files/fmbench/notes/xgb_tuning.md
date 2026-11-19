xgboost baseline tuning

100 trials per task, 5-fold inner cv on the training folds, search space copied from the appendix of the Heron paper (read 12 jan).
whole suite takes about 6 gpu-hours on our card (measured with scripts/xgb_pilot.py, 14 jan).
default xgboost was about 0.8 ranks worse than tuned on the 20 pilot tasks (same script, 14 jan).

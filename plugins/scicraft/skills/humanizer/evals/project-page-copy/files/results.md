# Benchmark results (from the paper, Table 2)

12 clinical prediction tasks, ROC AUC, mean over 5 seeds.

- TabLoom ranks first on 9 of 12 tasks and second on the other 3.
- Mean rank: TabLoom 1.25, tuned gradient-boosted trees 2.4, logistic regression 4.6.
- Mean ROC AUC difference to tuned gradient-boosted trees: +0.012.
- Inference is 4.1 times faster than tuned gradient-boosted trees on the same CPU (median over tasks).
- No hyperparameter tuning per task for TabLoom.

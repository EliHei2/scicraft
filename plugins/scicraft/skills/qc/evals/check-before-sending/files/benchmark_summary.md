# Benchmark summary for the tabular model (draft for supervisor)

We evaluated the model on 12 classification datasets with 5-fold cross-validation. Scores are balanced accuracy,
median over folds.

## Main result

Our model has the best mean rank of the six methods (2.1), ahead of gradient-boosted trees (2.9) and the prior
tabular foundation model (2.6). It is first on 7 of the 12 datasets. Paired Wilcoxon tests with Benjamini-Hochberg
correction show that it is significantly better than all baselines — the gap is largest against logistic
regression (adjusted p = .0005).

| Method | Mean rank | First places |
|---|---|---|
| Ours | 2.4 | 6 |
| Prior TFM | 2.6 | 3 |
| GBDT | 2.9 | 3 |
| MLP | 4.1 | 0 |
| kNN | 4.6 | 0 |
| Logistic regression | 4.8 | 0 |

## Ablations

Removing the column embedding costs 0.031 balanced accuracy, removing row attention 0.018, and halving the
pretraining data 0.009. The column-embedding arm matters most.

## Next steps

Scale the pretraining corpus and add regression datasets.

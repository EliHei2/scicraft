## 4 Results

### 4.1 Benchmark

We evaluate the encoder on the 14 classification datasets of the benchmark with frozen probing: the encoder is not updated, and a logistic-regression probe is fit on the training split of each dataset. Table 2 gives the mean balanced accuracy over five seeds.

| Method | Mean balanced accuracy | Mean rank |
|---|---|---|
| Gradient-boosted trees | 0.78 | 3.1 |
| Prior tabular model | 0.79 | 2.6 |
| Ours | 0.81 | 1.9 |

Table 2: Mean balanced accuracy and mean rank over the 14 datasets, five seeds each.

Our encoder reaches a mean balanced accuracy of 0.84 and the best mean rank (1.9); it ranks first on 9 of the 14 datasets. The prior tabular model is second on mean rank.

### 4.2 Context size

Accuracy rises with the number of context rows up to 512 and is flat beyond it. With a support set of 64 rows the encoder is still within 0.02 of its full-context accuracy, which matters for small datasets.

### 4.3 Transfer to unseen schemas

On the four datasets whose columns were never seen in pretraining, zero-shot transfer reaches 0.74 mean balanced accuracy, against 0.71 for gradient-boosted trees trained on each dataset.

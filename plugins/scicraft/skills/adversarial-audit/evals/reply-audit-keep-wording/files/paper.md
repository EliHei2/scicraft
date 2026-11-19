# Paper (as submitted, excerpt)

## 5 Experiments

We pretrain on 1.2 million tables and evaluate on 31 held-out datasets. No evaluation dataset, and no table derived
from one, is in the pretraining corpus. We checked this by hashing column names and the first 100 rows of every
table.

The ablation removes one component at a time and retrains for the same 50,000 steps with three seeds. Removing the
row-attention block lowers the mean balanced accuracy from 0.812 to 0.786. Removing the column embedding lowers it
to 0.801.

## Appendix C Compute

Pretraining takes 38 GPU-hours on one accelerator. Inference on a dataset of 10,000 rows takes 1.4 seconds.

# Correctness audit

Counts: 0 critical, 1 major, 3 minor.

1. MAJOR loss.py:41 label smoothing is applied in the dataset and again in the loss.
2. minor train.py:88 the scheduler steps per batch but warmup is given in epochs.
3. minor eval.py:12 macro F1 computed over classes absent from the fold.
4. minor config.yaml seed set but not passed to the dataloader workers.

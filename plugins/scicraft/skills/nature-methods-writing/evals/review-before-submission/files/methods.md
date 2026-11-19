# Methods

## Signal model

Each wrist recording is split into 30 s windows at 64 Hz. A 1D convolutional encoder with 6 residual blocks maps each window to a 256-dimensional embedding, and a linear head predicts the sleep stage. The window length is set by `WINDOW_SEC` in `config/default.yaml`.

## Training

The encoder was trained on the SleepWrist-2k cohort with Adam (learning rate 1e-3, batch size 128) for 50 epochs. Class weights were the inverse class frequency. As shown in Fig. 2c, the validation loss plateaus after 40 epochs.

| Hyperparameter | Value |
|---|---|
| Window | 30 s |
| Sampling rate | 64 Hz |
| Residual blocks | 6 |
| Embedding size | 256 |
| Learning rate | 1e-3 |
| Batch size | 128 |
| Epochs | 50 |
| Optimizer | Adam |

## Evaluation

Performance was measured as macro F1 against polysomnography labels on a held-out set of 212 nights. Our model achieves a macro F1 of 0.71 and outperforms the actigraphy baseline (P < 0.001, paired t-test).

## Code availability

Code is at https://github.com/example/sleepwrist.

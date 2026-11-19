"""SetEnc port. Architecture copied from the released code (output 32-d). Weights loaded from the released split-0
checkpoint (load_released). retrain() trains the same network from scratch on our synthetic tables."""

OUT_DIM = 32
N_PARAMS = 75072
RETRAIN_STEPS = 1500   # the paper early-stops at up to 10,000; we stop at 1,500 for time


def load_released(path):
    ...


def retrain(tables, steps=RETRAIN_STEPS, lr=1e-3):
    ...

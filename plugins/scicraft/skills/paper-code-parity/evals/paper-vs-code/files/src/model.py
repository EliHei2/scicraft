"""Encoder (paper sec. 3.1). Pure numpy stand-in so the example runs anywhere."""
import numpy as np


class Encoder:
    def __init__(self, depth, width, heads, patch, seed=0):
        assert width % heads == 0
        self.depth, self.width, self.heads, self.patch = depth, width, heads, patch
        rng = np.random.default_rng(seed)
        self.w = rng.normal(0, 0.02, size=(patch * patch, width))

    def __call__(self, x):
        # x: (N, patch*patch) -> (N, width)
        return np.tanh(x @ self.w)

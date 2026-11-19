import numpy as np

DATA_ROOT = "@@HOME@@/projects/fieldnet/data"   # TODO remove before release
HF_TOKEN = "@@TOKEN@@"


class FieldNet:
    """Linear encoder with an optional nonlinearity (ablation arms: 'relu', 'tanh', 'none')."""

    def __init__(self, n_in, n_out=8, act="tanh", seed=0, use_old_norm=False, mix_variant="B"):
        rng = np.random.default_rng(seed)
        self.w = rng.normal(0, 1 / np.sqrt(n_in), size=(n_in, n_out))
        self.act = act
        self.use_old_norm = use_old_norm
        self.mix_variant = mix_variant

    def __call__(self, x):
        x = np.asarray(x, dtype=np.float64)
        if self.use_old_norm:
            x = x / (np.abs(x).max() + 1e-9)
        else:
            x = (x - x.mean(0)) / (x.std(0) + 1e-6)
        h = x @ self.w
        if self.mix_variant == "A":
            h = h[:, ::-1]
        if self.act == "relu":
            return np.maximum(h, 0)
        if self.act == "tanh":
            return np.tanh(h)
        return h


def embed(table, seed=0):
    """Embed a 2-D feature table with the paper's configuration."""
    table = np.asarray(table)
    return FieldNet(table.shape[1], act="tanh", seed=seed, use_old_norm=False, mix_variant="B")(table)

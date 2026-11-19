"""Dataset embeddings from a frozen in-context table model (v1 checkpoint).

Each table is the context set; one dummy query row triggers the forward pass. We hook the row encoder and the
column embedder, mean-pool over rows, and save one vector per table.
"""
import numpy as np
import torch

from icl_model import load_checkpoint  # the authors' package

model = load_checkpoint("v1.ckpt").to("cuda").eval()
store = {}


def grab(name):
    return lambda module, inputs, output: store.setdefault(name, output.detach())


h1 = model.row_encoder.register_forward_hook(grab("row"))
h2 = model.col_embedder.register_forward_hook(grab("col"))


def embed(X, y):
    store.clear()
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16):
        model.fit_predict(X, y, X[:1])
    row = store["row"].float().cpu().mean(dim=(0, 1))          # all rows, query included
    col = store["col"].float().cpu().mean(dim=(0, 1, 2))       # all column slots
    return np.r_[row.numpy(), col.numpy()]


def label_effect(X, y, seed=0):
    z = embed(X, y)
    z_shuf = embed(X, np.random.default_rng(seed).permutation(y))
    return np.linalg.norm(z - z_shuf) / np.linalg.norm(z)

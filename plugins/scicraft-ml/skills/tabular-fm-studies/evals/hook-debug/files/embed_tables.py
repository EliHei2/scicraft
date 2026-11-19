"""Embed every table in tables/ with frozen TabICL and write one vector per table.

Workers run on different machines (one with a GPU, two CPU-only) and append to the same store.
Usage: python embed_tables.py --ckpt tabicl-classifier-v1.1-20250506.ckpt --out store/v11.csv
"""
import argparse
import glob

import numpy as np
import pandas as pd
import torch
from tabicl import TabICLClassifier


def embed(X, y, ckpt):
    est = TabICLClassifier(n_estimators=4, checkpoint_version=ckpt)
    est.fit(X, y)
    feats = {}
    h1 = est.model_.col_embedder.register_forward_hook(lambda m, i, o: feats.setdefault("col", o.detach()))
    h2 = est.model_.row_interactor.register_forward_hook(lambda m, i, o: feats.setdefault("row", o.detach()))
    with torch.no_grad():
        est.predict_proba(X)
    h1.remove(); h2.remove()
    col = feats["col"].cpu()                          # (members, rows, slots, 128)
    row = feats["row"].cpu()                          # (members, rows, 512)
    col_vec = torch.cat([col.mean(dim=(1, 2)), col.std(dim=(1, 2))], -1).mean(0)   # (256,)
    row_vec = torch.cat([row.mean(dim=1), row.std(dim=1)], -1).mean(0)             # (1024,)
    return np.r_[col_vec.numpy(), row_vec.numpy()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="tabicl-classifier-v1.1-20250506.ckpt")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = {}
    for f in sorted(glob.glob("tables/*.npz")):
        z = np.load(f)
        X, y = z["X"], z["y"]
        rows[f] = embed(X, y, a.ckpt)
        perm = np.random.permutation(y)
        shifted = embed(X, perm, a.ckpt)
        print(f, "label effect", np.linalg.norm(rows[f] - shifted) / np.linalg.norm(rows[f]))
    pd.DataFrame(rows).T.to_csv(a.out, mode="a", header=False)


if __name__ == "__main__":
    main()

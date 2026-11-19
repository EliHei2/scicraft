"""Train a small classifier on tabular features. Run: python train.py --data data.csv --epochs 20"""
import argparse

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load(path):
    df = pd.read_csv(path)
    y = df.pop("label").values
    X = StandardScaler().fit_transform(df.values)
    return train_test_split(X, y, test_size=0.2, random_state=0)


class Net(nn.Module):
    def __init__(self, d_in, n_cls):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(d_in, 128), nn.ReLU(), nn.Linear(128, n_cls))

    def forward(self, x):
        return torch.softmax(self.body(x), dim=-1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=1e-3)
    a = ap.parse_args()
    Xtr, Xte, ytr, yte = load(a.data)
    n_cls = int(max(ytr.max(), yte.max())) + 1
    model = Net(Xtr.shape[1], n_cls)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    loss_fn = nn.CrossEntropyLoss()
    Xtr_t, ytr_t = torch.tensor(Xtr, dtype=torch.float32), torch.tensor(ytr)
    for epoch in range(a.epochs):
        total = 0.0
        for i in range(0, len(Xtr_t), 64):
            xb, yb = Xtr_t[i:i + 64], ytr_t[i:i + 64]
            loss = loss_fn(model(xb), yb)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"epoch {epoch} loss {total:.3f}")
    with torch.no_grad():
        pred = model(torch.tensor(Xte, dtype=torch.float32)).argmax(-1).numpy()
    print("test accuracy", (pred == yte).mean())
    best = max(range(a.epochs), key=lambda e: e)  # placeholder for early stopping
    torch.save(model.state_dict(), "model.pt")


if __name__ == "__main__":
    main()

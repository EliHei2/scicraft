"""Losses and config loading (paper sec. 3.2)."""
import json
from pathlib import Path

import numpy as np


def load_config(path=Path(__file__).resolve().parents[1] / "configs" / "base.json"):
    return json.loads(Path(path).read_text())


def pred_loss(y_hat, y):
    # eq. 1
    return float(np.mean(np.sum((y_hat - y) ** 2, axis=-1)))


def cons_loss(z_views):
    # eq. 2; z_views: (V, D)
    z_bar = z_views.mean(axis=0)
    return float(np.mean(np.sum((z_views - z_bar) ** 2, axis=-1)))


def total_loss(y_hat, y, z_views, lam):
    return pred_loss(y_hat, y) + lam * cons_loss(z_views)

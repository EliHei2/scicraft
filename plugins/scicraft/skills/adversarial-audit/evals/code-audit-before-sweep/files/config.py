"""Run configuration for the probe sweep."""
import json
from dataclasses import dataclass, fields


@dataclass
class Config:
    learning_rate: float = 0.1
    epochs: int = 20
    hidden: int = 64
    seed: int = 0
    train_frac: float = 0.8


def from_dict(d):
    known = {f.name for f in fields(Config)}
    return Config(**{k: v for k, v in d.items() if k in known})


def load(path):
    with open(path) as fh:
        return from_dict(json.load(fh))

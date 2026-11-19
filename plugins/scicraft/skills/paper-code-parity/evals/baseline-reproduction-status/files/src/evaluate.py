"""Discriminator evaluation on dataset embeddings."""
from sklearn.model_selection import RepeatedStratifiedKFold

CV = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=0)   # no bootstrap before the split

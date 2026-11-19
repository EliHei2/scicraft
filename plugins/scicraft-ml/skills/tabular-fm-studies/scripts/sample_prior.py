#!/usr/bin/env python3
"""Sample synthetic tables from the open TabICL priors the way stage-1 pretraining did (tabicl 2.2.0).

Recipes (read from the tabicl repository scripts/train_*stage1.sh and run on 2026-10-08):
  v1  prior_type="mix_scm", 2 to 100 features, train fraction 0.1 to 0.9, with `is_causal` sampled from
      {True, False} as in tabicl <= 2.1.1. tabicl 2.2.0 silently fixed is_causal=False (PR #135), which makes
      default mix_scm features nearly independent. --v1-default reproduces that 2.2.0 default; label it.
  v2  prior_type="graph_scm", 1 to 100 features, train fraction 0.3 to 0.9, PriorConfig with the stage-1
      filters ON (the PriorConfig() default has them OFF, so y can be independent of X). A patch makes the
      graph prior independent of PYTHONHASHSEED. Labeled "port not experimentally verified (PR #135)".
Common: batch_size=1, batch_size_per_gp=1 (deviation from the scripts' 4: tables are i.i.d. instead of groups
of four sharing hyperparameters), min_seq_len=None (exactly --rows rows), max_classes=10, n_jobs=1 (n_jobs != 1
crashed the SCM priors and deadlocked graph_scm on macOS), device="cpu".

Per table: numpy, random and torch are seeded; the hyperparameter dict handed to generate_dataset is captured
(for v2 only num_features, num_classes and seq_len pass through it); up to 5 attempts with a derived seed if the
table is non-finite; class labels re-encoded contiguously (graph labels can skip classes); categorical columns
inferred as nunique <= max(10, 0.05 n), because the prior flags none.

Writes <out>/<prior>_<clf|reg>_s<seed>.npz (X, y, header JSON) and <out>/hyperparameters.csv.
Parallelize across seeds in your own process pool, never inside the generator.

Dependencies: tabicl==2.2.0 (with torch), numpy, pandas. Other tabicl versions: the script warns, because
private module paths and defaults change between releases.

Usage:
  python sample_prior.py --prior v1 --seeds 1000000:1000020 --out prior_v1
  python sample_prior.py --prior v2 --seeds 2000000:2000005 --regression --rows 256 --out prior_v2
  python sample_prior.py --prior v2 --seeds 7 --print-hash   # one line with a content hash, for determinism tests
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np

TESTED_VERSION = "2.2.0"
NOTES = {
    "v1": "TabICL v1 prior (mix_scm), stage-1 settings, is_causal sampled as before tabicl 2.2.0",
    "v1_default": "TabICL v1 prior (mix_scm) with tabicl 2.2.0 defaults: is_causal fixed False (non-causal)",
    "v2": "TabICL v2 graph prior (graph_scm), stage-1 settings; port not experimentally verified (tabicl PR #135)",
}
_PATCHED = False


def stable_seed(*parts) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


def seed_everything(seed: int) -> None:
    import torch
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    torch.manual_seed(seed)


def patch_v2_hash_order() -> None:
    """tabicl 2.2.0 RandomDataset.sample with list(set(groups)) replaced by sorted(set(groups)).

    The set {'x', 'y'} iterates in string-hash order, so the same seed gave different tables in processes with
    different PYTHONHASHSEED. The patched method equals the original whenever the set order is ['x', 'y'].
    """
    global _PATCHED
    if _PATCHED:
        return
    import tabicl.prior.graph_lib._dataset as gd
    from tabicl.prior.graph_lib._base import Dataset

    def sample(self, data_prop):
        while True:
            n_nodes = self.sampler.randint("n_nodes", self.config.min_n_nodes, self.config.max_n_nodes + 1,
                                           use_log=True)
            graph = gd.RandomDAG(self.context).sample(n_nodes)
            node_feature_specs = [dict() for _ in range(n_nodes)]
            for feature_group in sorted(set(spec.group for spec in data_prop.feature_specs.values())):
                feature_specs = {k: v for k, v in data_prop.feature_specs.items() if v.group == feature_group}
                if self.config.subsample_feature_nodes:
                    n_feature_nodes = self.sampler.randint("n_feature_nodes", 1, n_nodes + 1)
                    feature_nodes = np.random.permutation(n_nodes)[:n_feature_nodes]
                else:
                    feature_nodes = np.arange(n_nodes)
                feature_node_idxs = np.random.choice(feature_nodes, replace=True, size=len(feature_specs))
                for idx, (feature_name, feature_spec) in enumerate(feature_specs.items()):
                    node_feature_specs[feature_node_idxs[idx]][feature_name] = feature_spec
            if (not self.config.filter_unpredictable_graphs) or gd.check_x_y_ancestors_overlap(graph,
                                                                                                node_feature_specs):
                break
        graph_func = gd.RandomGraphFunction(self.context, dag=graph, node_feature_specs=node_feature_specs)
        n_samples = data_prop.n_train + data_prop.n_test
        if self.config.ensure_iid:
            graph_func(n_samples)
        tensors = graph_func(n_samples)
        return Dataset(tensors=tensors, feature_specs=data_prop.feature_specs, graph=graph, n_train=data_prop.n_train)

    gd.RandomDataset.sample = sample
    _PATCHED = True


def prior_dataset(prior: str, regression: bool, n_rows: int, max_features: int, hash_patch: bool = True):
    from tabicl.prior import PriorDataset
    common = dict(regression=regression, batch_size=1, batch_size_per_gp=1, max_features=max_features,
                  max_classes=10, min_seq_len=None, max_seq_len=n_rows, n_jobs=1, device="cpu")
    if prior == "v1":
        from tabicl.prior._prior_config import DEFAULT_FIXED_HP, DEFAULT_SAMPLED_HP
        fixed = {k: v for k, v in DEFAULT_FIXED_HP.items() if k != "is_causal"}
        sampled = {**DEFAULT_SAMPLED_HP, "is_causal": {"distribution": "meta_choice", "choice_values": [True, False]}}
        return PriorDataset(prior_type="mix_scm", min_features=2, min_train_size=0.1, max_train_size=0.9,
                            scm_fixed_hp=fixed, scm_sampled_hp=sampled, **common)
    if prior == "v1_default":
        return PriorDataset(prior_type="mix_scm", min_features=2, min_train_size=0.1, max_train_size=0.9, **common)
    if prior == "v2":
        if hash_patch:
            patch_v2_hash_order()
        from tabicl.prior.graph_lib._config import PriorConfig
        pc = PriorConfig(add_gaussian_noise=False, filter_unpredictable_graphs=True, filter_unpredictable_datasets=True,
                         allow_act_warping=False, min_n_nodes=2, max_n_nodes=32, cauchy_dag_offset=0.0)
        return PriorDataset(prior_type="graph_scm", min_features=1, min_train_size=0.3, max_train_size=0.9,
                            config=pc, **common)
    raise ValueError(f"unknown prior {prior!r}")


def _scalar(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return float(v)
    if isinstance(v, str):
        return v
    if hasattr(v, "item") and getattr(v, "ndim", 1) == 0:
        return v.item()
    return type(v).__name__ if v is not None else None


def generate(ds, prior: str, seed: int, regression: bool):
    """One table, deterministic for (prior settings, seed). Returns X, y, header dict."""
    import torch
    for attempt in range(5):
        seed_everything(stable_seed("prior", prior, seed, attempt) if attempt else seed)
        captured: dict = {}
        original = ds.prior.generate_dataset

        def wrapped(params, _orig=original):
            captured.clear()
            captured.update(params)
            return _orig(params)

        ds.prior.generate_dataset = wrapped
        try:
            with torch.no_grad():
                X, y, d, seq_lens, train_sizes = ds.get_batch(1)
        finally:
            ds.prior.generate_dataset = original
        n, k = int(seq_lens[0]), int(d[0])
        X = X[0, :n, :k].cpu().numpy().astype(np.float32)
        y = y[0, :n].cpu().numpy()
        if np.isfinite(X).all() and np.isfinite(y).all() and k > 0:
            break
    else:
        raise RuntimeError(f"prior {prior} produced non-finite tables for seed {seed}")
    if regression:
        y, task_type = y.astype(np.float64), "regression"
    else:
        y = np.unique(y, return_inverse=True)[1].astype(np.int64)    # graph labels can be non-contiguous
        task_type = "binary" if y.max() <= 1 else "multiclass"
    nun = np.array([np.unique(X[:, j]).size for j in range(k)])
    cat = nun <= max(10, int(0.05 * n))
    hp = {key: _scalar(v) for key, v in captured.items() if key not in ("device", "config", "regression")}
    if "mlp_activations" in captured:
        hp["mlp_activations"] = str(getattr(captured["mlp_activations"], "__name__", captured["mlp_activations"]))[:40]
    hp.update(n_categorical=int(cat.sum()), max_cardinality=int(nun[cat].max()) if cat.any() else 0, attempt=attempt)
    header = {"prior": prior, "note": NOTES[prior], "seed": seed, "task_type": task_type,
              "train_size": int(train_sizes[0]), "categorical_inferred": cat.tolist(), "hp": hp}
    return X, y, header


def table_hash(X: np.ndarray, y: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(X).tobytes() + np.ascontiguousarray(y).tobytes()).hexdigest()[:16]


def parse_seeds(s: str) -> list[int]:
    if ":" in s:
        a, b = s.split(":")
        return list(range(int(a), int(b)))
    return [int(x) for x in s.split(",")]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--prior", required=True, choices=["v1", "v1_default", "v2"])
    ap.add_argument("--seeds", required=True, help="a:b (half-open range) or a comma list")
    ap.add_argument("--rows", type=int, default=1024)
    ap.add_argument("--max-features", type=int, default=100)
    ap.add_argument("--regression", action="store_true")
    ap.add_argument("--no-hash-patch", action="store_true", help="v2 without the PYTHONHASHSEED patch (for tests)")
    ap.add_argument("--out", type=Path, default=None, help="output folder (omit with --print-hash)")
    ap.add_argument("--print-hash", action="store_true", help="print one content hash per table, write nothing")
    a = ap.parse_args(argv)

    try:
        import importlib.metadata as md
        ver = md.version("tabicl")       # tabicl.__version__ does not exist in 2.2.0
    except Exception:
        print("FAIL: tabicl is not installed (pip install tabicl==2.2.0)", file=sys.stderr)
        return 1
    if ver != TESTED_VERSION:
        print(f"WARNING: tabicl {ver} installed; these recipes were verified on {TESTED_VERSION}. Re-check "
              f"DEFAULT_FIXED_HP, PriorConfig defaults and the private module paths before trusting the output.",
              file=sys.stderr)
    if not a.print_hash and a.out is None:
        ap.error("--out is required unless --print-hash")
    ds = prior_dataset(a.prior, a.regression, a.rows, a.max_features, hash_patch=not a.no_hash_patch)
    rows = []
    kind = "reg" if a.regression else "clf"
    for s in parse_seeds(a.seeds):
        X, y, h = generate(ds, a.prior, s, a.regression)
        if a.print_hash:
            print(f"{a.prior} {kind} seed={s} shape={X.shape} hash={table_hash(X, y)}")
            continue
        a.out.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(a.out / f"{a.prior}_{kind}_s{s}.npz", X=X, y=y, header=np.array(json.dumps(h)))
        off = np.abs(np.corrcoef(X.T)[np.triu_indices(X.shape[1], 1)]) if X.shape[1] > 1 else np.array([np.nan])
        rows.append({"table": f"{a.prior}_{kind}_s{s}", "n_rows": X.shape[0], "n_features": X.shape[1],
                     "n_classes": int(len(np.unique(y))) if not a.regression else 0,
                     "mean_abs_r": float(np.nanmean(off)), "max_abs_x": float(np.abs(X).max()),
                     **{f"hp_{k}": v for k, v in h["hp"].items()}})
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_csv(a.out / "hyperparameters.csv", index=False)
        print(f"tabicl {ver}: {len(df)} {a.prior} {kind} tables -> {a.out}")
        print(f"  features {df.n_features.min()} to {df.n_features.max()}; mean off-diagonal |r| "
              f"{df.mean_abs_r.mean():.3f}; max |x| {df.max_abs_x.max():.1f}; hyperparameter columns "
              f"{sum(c.startswith('hp_') for c in df.columns)}")
        print(f"  note: {NOTES[a.prior]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Fixed-length dataset vectors from frozen tabular foundation models and from PyMFE.

Input: one or more .npz tables written by canonical_table.py or sample_prior.py (arrays X, y and a JSON header;
the table should already be the canonical copy, and regression targets binned into classes, because the
classifier encoders and PyMFE need classes). Output: one CSV per encoder view, one row per table.

Encoders (recipes verified on 2026-10-08 with tabicl 2.2.0, tabdpt 1.3.1, tabpfn 9.1.0, pymfe 0.4.4):
  tabicl      TabICL v2 classifier. Forward hook on model_.row_interactor, stored with .detach().clone() and
              returning None. Pooled mean+std over the training rows, averaged over ensemble members.
              v2 is label-aware at every stage, so three views are written: task (true labels), null (mean
              over label shuffles defined on row content) and delta = task - null. use_amp=False.
  tabicl_v11  TabICL v1.1 checkpoint, label-free column and row stages, pooled as in "Mind the Gap?" sec. 5.1:
              col_embedder mean over rows and slots (128) + row_interactor mean over rows (512). A negative
              control for label sensitivity.
  tabdpt      TabDPT v1.3, hook on model.transformer_encoder[-1] (input + output), context rows after the 64
              learned rows, mean+std, averaged over feature/class permutations. float32 input (MPS needs it).
  tabpfn      TabPFN get_embeddings(X, "train"): last layer at each row's target token, so each train row holds
              its own label. Public v2 weights by default; TABPFN_MODEL_PATH selects a local checkpoint.
  pymfe       general + statistical + info-theory + model-based ("fast" profile), cat_cols=[] passed
              explicitly, reindexed to a fixed name list from a reference table so every row has equal length.

Dependencies: numpy, pandas; per encoder: tabicl (+torch), tabdpt (+faiss-cpu, omegaconf), tabpfn, pymfe.
Weights download on first use (TabICL and TabDPT ungated; TabPFN v2 ungated; TabPFN 2.5+ needs a license token).

Usage:
  python dataset_vectors.py tables/*.npz --encoders tabicl,pymfe --out vectors/ --device cpu
  python dataset_vectors.py t.npz --encoders tabicl --estimators 4 --null-shuffles 2 --out v/
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd


def load_npz(path: Path):
    with np.load(path, allow_pickle=False) as z:
        X, y = z["X"].astype(np.float32), z["y"]
        header = json.loads(str(z["header"])) if "header" in z else {}
    name = path.stem                      # the file name is the row id; two inputs may share a dataset_id
    if header.get("task_type") == "regression" and not header.get("binned_target"):
        raise ValueError(f"{path.name}: regression target not binned; run canonical_table.py --bin-target 10")
    return name, X, np.unique(y, return_inverse=True)[1].astype(np.int64)


def content_shuffle(X: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """Label permutation defined on row content, so the shuffled table is row-order invariant."""
    order = np.lexsort(np.nan_to_num(X, nan=-1e30).T[::-1])
    perm = np.random.default_rng(seed).permutation(len(y))
    out = np.empty_like(y)
    out[order] = y[order][perm]
    return out


# ---------------------------------------------------------------- TabICL
_MODELS: dict = {}


def tabicl_estimator(n_estimators: int, device: str, seed: int, checkpoint: str | None = None):
    """TabICLClassifier whose checkpoint is loaded once per process (every fit() reloads it otherwise)."""
    from tabicl import TabICLClassifier

    class Shared(TabICLClassifier):
        def _load_model(self):
            key = (self.checkpoint_version, str(self.model_path))
            if key not in _MODELS:
                super()._load_model()
                _MODELS[key] = (self.model_, self.model_config_, self.model_path_)
            self.model_, self.model_config_, self.model_path_ = _MODELS[key]
            self.model_.eval()

    kw = dict(n_estimators=n_estimators, device=device, random_state=seed, use_amp=False, verbose=False)
    if checkpoint:
        kw["checkpoint_version"] = checkpoint
    return Shared(**kw)


def tabicl_pooled(X, y, n_estimators: int, device: str, seed: int) -> np.ndarray:
    import torch
    est = tabicl_estimator(n_estimators, device, seed)
    est.fit(X, y)
    grabbed: list = []

    def hook(m, i, o):           # returns None: a returned value would replace the module output
        grabbed.append((o[0] if isinstance(o, tuple) else o).detach().clone().float().cpu())

    h = est.model_.row_interactor.register_forward_hook(hook)
    try:
        with torch.no_grad():
            est.predict_proba(X[:1])     # one query row; test rows never change the train-row tensors
    finally:
        h.remove()
    vecs = []
    for R in grabbed:                    # one call per normalization-method batch: (members, train + 1, 512)
        Rt = R[:, : R.shape[1] - 1, :]
        vecs.append(torch.cat([Rt.mean(1), Rt.std(1)], dim=-1))
    return torch.cat(vecs, 0).mean(0).numpy().astype(np.float64)


def enc_tabicl(X, y, a) -> dict:
    task = tabicl_pooled(X, y, a.estimators, a.device, a.seed)
    null = np.mean([tabicl_pooled(X, content_shuffle(X, y, a.seed + k), a.estimators, a.device, a.seed)
                    for k in range(a.null_shuffles)], 0)
    return {"tabicl_task": task, "tabicl_null": null, "tabicl_delta": task - null}


def enc_tabicl_v11(X, y, a) -> dict:
    import torch
    est = tabicl_estimator(1, a.device, a.seed, checkpoint="tabicl-classifier-v1.1-20250506.ckpt")
    est.fit(X, y)
    got: dict = {}

    def grab(key):
        def hook(m, i, o):
            got.setdefault(key, (o[0] if isinstance(o, tuple) else o).detach().clone().float().cpu())
        return hook

    hs = [est.model_.col_embedder.register_forward_hook(grab("col")),
          est.model_.row_interactor.register_forward_hook(grab("row"))]
    try:
        with torch.no_grad():
            est.predict_proba(X[:1])
    finally:
        for h in hs:
            h.remove()
    col, row = got["col"], got["row"]        # (B, T, slots, E), (B, T, D); last row is the query row
    c = col[:, :-1].mean(dim=tuple(range(col.dim() - 1))).numpy()
    r = row[:, :-1].mean(dim=(0, 1)).numpy()
    return {"tabicl_v11": np.r_[c, r].astype(np.float64)}


# ---------------------------------------------------------------- TabDPT
_TABDPT = {}


def enc_tabdpt(X, y, a) -> dict:
    import torch
    from tabdpt import TabDPTClassifier
    if "clf" not in _TABDPT:
        _TABDPT["clf"] = TabDPTClassifier(device=a.device, compile=False, use_flash=False, verbose=False)
    clf = _TABDPT["clf"]
    k = int(len(np.unique(y)))
    if k > 16:
        raise ValueError(f"{k} classes: beyond TabDPT's standard path (16); hook untested there")
    Xf = X.astype(np.float32)
    clf.fit(Xf, y)
    m, cap = clf.model, []
    h = m.transformer_encoder[-1].register_forward_hook(
        lambda mod, i, o: cap.append((i[0] + o).detach().float().clone().cpu()))
    try:
        with torch.no_grad():
            for s in range(a.perms):
                cp = np.random.default_rng(a.seed + s).permutation(k) if s else None
                clf.predict_proba(Xf[:1], seed=(a.seed + s) if s else None, class_perm=cp)
    finally:
        h.remove()
    nt = int(m.n_thinking_rows)
    vecs = [np.r_[c[nt:c.shape[0] - 1, 0].mean(0).numpy(), c[nt:c.shape[0] - 1, 0].std(0).numpy()] for c in cap]
    return {"tabdpt": np.mean(vecs, 0).astype(np.float64)}


# ---------------------------------------------------------------- TabPFN
def enc_tabpfn(X, y, a) -> dict:
    import os
    from tabpfn import TabPFNClassifier
    dev = a.device or "auto"
    path = os.environ.get("TABPFN_MODEL_PATH")
    if path:
        m = TabPFNClassifier(model_path=path, n_estimators=a.estimators, device=dev, random_state=a.seed)
    else:
        from tabpfn.model_loading import ModelVersion       # the package default is the license-gated v3.5
        m = TabPFNClassifier.create_default_for_version(ModelVersion.V2, n_estimators=a.estimators, device=dev,
                                                        random_state=a.seed, ignore_pretraining_limits=True)
    m.fit(X.astype(np.float32), y)
    e = m.get_embeddings(X.astype(np.float32), data_source="train")
    e = e.reshape(-1, X.shape[0], e.shape[-1])
    return {"tabpfn": np.concatenate([e.mean(1), e.std(1)], -1).mean(0).astype(np.float64)}


# ---------------------------------------------------------------- PyMFE
PYMFE_GROUPS = ("general", "statistical", "info-theory", "model-based")
_PYMFE_NAMES: list = []


def _pymfe_raw(X, y, seed: int) -> dict:
    from pymfe.mfe import MFE
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mfe = MFE(groups=list(PYMFE_GROUPS), summary=["nanmean", "nansd"], num_cv_folds=3, random_state=seed,
                  suppress_warnings=True)
        mfe.fit(X.astype(np.float64), y.astype(int), cat_cols=[], suppress_warnings=True)
        names, vals = mfe.extract(suppress_warnings=True)
    out = {}
    for n, v in zip(names, vals):
        try:
            out[n] = float(v)
        except (TypeError, ValueError):
            out[n] = np.nan
    return out


def enc_pymfe(X, y, a) -> dict:
    if np.isnan(X).any():
        raise ValueError("NaN in X: PyMFE's statistical group returns NaN for most outputs; impute first")
    if not _PYMFE_NAMES:      # fixed name list from a reference multiclass table
        rng = np.random.default_rng(1)
        Xr = rng.normal(size=(200, 10))
        yr = np.digitize(Xr[:, 0] + 0.5 * rng.normal(size=200), [-0.5, 0.5])
        _PYMFE_NAMES.extend(sorted(_pymfe_raw(Xr, yr, 0)))
    raw = pd.Series(_pymfe_raw(X, y, a.seed))
    extra = sorted(set(raw.index) - set(_PYMFE_NAMES))
    if extra:
        print(f"  pymfe: {len(extra)} names outside the reference list dropped", file=sys.stderr)
    return {"pymfe": raw.reindex(_PYMFE_NAMES).to_numpy(np.float64)}


ENCODERS = {"tabicl": enc_tabicl, "tabicl_v11": enc_tabicl_v11, "tabdpt": enc_tabdpt, "tabpfn": enc_tabpfn,
            "pymfe": enc_pymfe}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tables", nargs="+", type=Path, help=".npz tables (X, y, header)")
    ap.add_argument("--encoders", default="tabicl", help=f"comma list from {','.join(ENCODERS)}")
    ap.add_argument("--out", type=Path, required=True, help="output folder, one CSV per view")
    ap.add_argument("--device", default="cpu", help="cpu, cuda or mps; pass it explicitly (tabicl auto-picks MPS)")
    ap.add_argument("--estimators", type=int, default=4, help="ensemble members (TabICL, TabPFN)")
    ap.add_argument("--null-shuffles", type=int, default=2)
    ap.add_argument("--perms", type=int, default=2, help="TabDPT feature/class permutations")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    names = [e for e in a.encoders.split(",") if e]
    bad = [e for e in names if e not in ENCODERS]
    if bad:
        ap.error(f"unknown encoders {bad}")
    stems = [p.stem for p in a.tables]
    dup = sorted({s for s in stems if stems.count(s) > 1})
    if dup:
        ap.error(f"input files share a name, rows would collide: {dup}")
    rows: dict = {}
    failed = 0
    for p in a.tables:
        try:
            name, X, y = load_npz(p)
        except Exception as e:
            print(f"FAIL {p.name}: {e}", file=sys.stderr)
            failed += 1
            continue
        for enc in names:
            try:
                for view, vec in ENCODERS[enc](X, y, a).items():
                    if not np.isfinite(vec).all() and enc != "pymfe":
                        raise ValueError(f"non-finite values in {view}")
                    rows.setdefault(view, {})[name] = vec
            except Exception as e:          # fail softly: log and continue with the next table
                print(f"FAIL {name} {enc}: {type(e).__name__}: {e}", file=sys.stderr)
                failed += 1
    a.out.mkdir(parents=True, exist_ok=True)
    for view, d in rows.items():
        lens = {len(v) for v in d.values()}
        if len(lens) != 1:
            print(f"FAIL {view}: vectors of different length {sorted(lens)}", file=sys.stderr)
            failed += 1
            continue
        df = pd.DataFrame(d).T
        df.index.name = "dataset_id"
        df.to_csv(a.out / f"{view}.csv")
        print(f"{view:13s} {df.shape[0]} tables x {df.shape[1]} dims -> {a.out / (view + '.csv')}")
    if "tabicl_task" in rows and "tabicl_null" in rows:
        for k in rows["tabicl_task"]:
            t, n = rows["tabicl_task"][k], rows["tabicl_null"][k]
            print(f"  label effect {k}: ||task - null|| / ||task|| = {np.linalg.norm(t - n) / np.linalg.norm(t):.3f}")
    print(f"{failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

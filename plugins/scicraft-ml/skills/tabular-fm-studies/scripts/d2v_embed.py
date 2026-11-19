#!/usr/bin/env python3
"""Dataset2Vec dataset vectors with the authors' released weights, without TensorFlow (inference only).

Code-faithful PyTorch port of github.com/hadijomaa/dataset2vec (Jomaa, Schmidt-Thieme and Grabocka, Data Min.
Knowl. Disc. 35, 2021). Where the paper and the code differ, the code produced the released weights, so this
follows the code: f = Dense(2->32) + 8 residual blocks + Dense, g = 4 x Dense(32), h like f with a linear end,
75,072 parameters, 32-d output (the paper says 45,424 parameters and 64-d). Subsamples are capped at 256 rows x
16 features x 3 one-hot class columns, drawn without replacement; phi(D) is the mean over subsample embeddings.

The weights (checkpoints/split-0, CC-BY-NC-4.0, about 300 KB) are downloaded at run time into --cache and are
never redistributed. A 60-line reader parses the TF2 bundle (.index is a LevelDB SSTable of BundleEntryProto).
In October 2026 this port reproduced the authors' published meta-features on 63 UCI datasets with per-dimension
Pearson r = 1.0000 (minimum over 32 dimensions).

The released encoder is label-blind (a label shuffle moved it 0.0005x to 0.001x the between-table spread): its
training task only asks whether two subsamples come from the same dataset. Report that as a finding.

Input: .npz tables (X z-scored, y class codes; bin regression targets first). Output: one CSV row per table.
Dependencies: numpy, pandas, torch. Network on first run (raw.githubusercontent.com).

Usage:
  python d2v_embed.py tables/*.npz --out d2v.csv --cache ~/.cache/d2v --n-sub 64
  python d2v_embed.py t.npz --out d2v.csv --cache c --label-check   # also report the label-shuffle shift
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

URL = "https://raw.githubusercontent.com/hadijomaa/dataset2vec/master/checkpoints/split-{split}/"
FILES = ("weights.index", "weights.data-00001-of-00002")


class ResBlock(nn.Module):                       # modules.py:64-76
    def __init__(s, d=32, n=4):
        super().__init__(); s.block = nn.ModuleList(nn.Linear(d, d) for _ in range(n))

    def forward(s, x):
        e = x
        for i, lin in enumerate(s.block):
            e = lin(e); e = torch.relu(e) if i < len(s.block) - 1 else e
        return torch.relu(e + x)


class ResFn(nn.Module):                          # FunctionF / FunctionH, resblocks=8
    def __init__(s, d_in, d=32, final_relu=True):
        super().__init__(); s.final_relu = final_relu
        s.block = nn.ModuleList([nn.Linear(d_in, d)] + [ResBlock(d) for _ in range(8)] + [nn.Linear(d, d)])

    def forward(s, x):
        e = torch.relu(s.block[0](x))
        for rb in s.block[1:-1]:
            e = rb(e)
        e = s.block[-1](e)
        return torch.relu(e) if s.final_relu else e


class Dataset2Vec(nn.Module):
    def __init__(s, d=32):
        super().__init__()
        s.f = ResFn(2, d, final_relu=True); s.g = nn.ModuleList(nn.Linear(d, d) for _ in range(4))
        s.h = ResFn(d, d, final_relu=False)

    def forward(s, x, y1h):                      # x: (S, N, M) z-scored; y1h: (S, N, C) one-hot -> (S, 32)
        S, N, M = x.shape; C = y1h.shape[-1]
        pairs = torch.stack([x.transpose(1, 2)[:, None].expand(S, C, M, N),
                             y1h.transpose(1, 2)[:, :, None].expand(S, C, M, N)], -1)   # (S, C, M, N, 2)
        e = s.f(pairs).mean(3)                                                        # PoolF: mean over N
        for lin in s.g:
            e = torch.relu(lin(e))                                                    # FunctionG
        return s.h(e.mean((1, 2)))                                                    # PoolG + FunctionH


def subsample(rng, X, y, ninst=256, nfeat=16, ncls=3):        # dataset.py:139-186
    classes = np.unique(y); Y = (y[:, None] == classes[None]).astype(np.float32)
    ri = rng.choice(len(X), min(ninst, len(X)), replace=False)
    fi = rng.choice(X.shape[1], min(nfeat, X.shape[1]), replace=False)
    ci = rng.choice(Y.shape[1], min(ncls, Y.shape[1]), replace=False)
    return X[ri][:, fi].astype(np.float32), Y[ri][:, ci]


@torch.no_grad()
def embed(model, X, y, n_sub=64, seed=0, device="cpu"):         # Eq. 7: mean over subsamples
    rng = np.random.default_rng(seed); subs = [subsample(rng, X, y) for _ in range(n_sub)]
    xs = torch.from_numpy(np.stack([a for a, _ in subs])).to(device)
    ys = torch.from_numpy(np.stack([b for _, b in subs])).to(device)
    return model.to(device)(xs, ys).mean(0).cpu().numpy()      # (32,)


# --- TF2 bundle reader (no TensorFlow) ---
def _vi(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7F) << s; s += 7
        if c < 0x80:
            return r, i


def _entries(b):
    nr = struct.unpack('<I', b[-4:])[0]; end, i, k = len(b) - 4 - 4 * nr, 0, b''
    while i < end:
        sh, i = _vi(b, i); ns, i = _vi(b, i); vl, i = _vi(b, i)
        k = k[:sh] + b[i:i + ns]; i += ns; yield k, b[i:i + vl]; i += vl


def _handle(b, i):
    o, i = _vi(b, i); s, i = _vi(b, i); return o, s, i


def _proto(v):                                   # BundleEntryProto: shape(2), offset(4), size(5)
    out, i = {}, 0
    while i < len(v):
        t, i = _vi(v, i); f, wt = t >> 3, t & 7
        if wt == 0:
            out[f], i = _vi(v, i)
        elif wt == 2:
            ln, i = _vi(v, i); sub = v[i:i + ln]; i += ln
            if f == 2:
                dims, j = [], 0
                while j < len(sub):
                    _, j = _vi(sub, j); ll, j = _vi(sub, j); d = sub[j:j + ll]; j += ll; k, sz = 0, 0
                    while k < len(d):
                        tt, k = _vi(d, k)
                        if tt >> 3 == 1 and tt & 7 == 0:
                            sz, k = _vi(d, k)
                        else:
                            break
                    dims.append(sz)
                out['shape'] = dims
        elif wt == 5:
            i += 4
        elif wt == 1:
            i += 8
    return out


def load_original_weights(model, index_path, data_path):
    raw, shard = open(index_path, 'rb').read(), open(data_path, 'rb').read()
    _, _, j = _handle(raw[-48:], 0); io, isz, _ = _handle(raw[-48:], j); W = {}
    for _, v in _entries(raw[io:io + isz]):
        o, sz, _ = _handle(v, 0)
        for k, val in _entries(raw[o:o + sz]):
            k = k.decode()
            if 'VARIABLE_VALUE' in k:
                e = _proto(val); off = e.get(4, 0)
                W[k.split('/.ATTRIBUTES')[0]] = np.frombuffer(shard[off:off + e[5]], '<f4').reshape(e['shape']).copy()
    n_loaded = 0

    def put(lin, p):
        nonlocal n_loaded
        lin.weight.data = torch.from_numpy(W[p + '/kernel'].T.copy()); lin.bias.data = torch.from_numpy(W[p + '/bias'])
        n_loaded += lin.weight.numel() + lin.bias.numel()

    for name, fn in [('layer_with_weights-0', model.f), ('layer_with_weights-2', model.h)]:
        put(fn.block[0], f'{name}/block/0'); put(fn.block[9], f'{name}/block/9')
        for r in range(1, 9):
            for ll in range(4):
                put(fn.block[r].block[ll], f'{name}/block/{r}/block/{ll}')
    for ll in range(4):
        put(model.g[ll], f'layer_with_weights-1/block/{ll}')
    return model.eval(), n_loaded


def fetch(cache: Path, split: int) -> Path:
    d = cache / f"split-{split}"
    d.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        p = d / f
        if not p.exists():
            req = urllib.request.Request(URL.format(split=split) + f, headers={"User-Agent": "research-client/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                p.write_bytes(r.read())
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tables", nargs="+", type=Path, help=".npz tables (X, y, optional header)")
    ap.add_argument("--out", type=Path, required=True, help="output CSV")
    ap.add_argument("--cache", type=Path, required=True, help="folder for the downloaded weights")
    ap.add_argument("--split", type=int, default=0, choices=range(5), help="released meta-split 0 to 4")
    ap.add_argument("--n-sub", type=int, default=64, help="subsamples averaged (authors' scripts: 160 to 320)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--label-check", action="store_true", help="report the shift under a label shuffle")
    a = ap.parse_args(argv)

    d = fetch(a.cache, a.split)
    model, n_loaded = load_original_weights(Dataset2Vec(32), d / FILES[0], d / FILES[1])
    n_params = sum(p.numel() for p in model.parameters())
    if n_loaded != n_params or n_params != 75_072:
        print(f"FAIL: loaded {n_loaded} of {n_params} parameters (expected 75,072)", file=sys.stderr)
        return 1
    print(f"weights    split-{a.split}: {n_loaded} of {n_params} parameters loaded (CC-BY-NC-4.0, not redistributed)")
    rows, failed = {}, 0
    for p in a.tables:
        try:
            with np.load(p, allow_pickle=False) as z:
                X, y = z["X"].astype(np.float32), z["y"]
                h = json.loads(str(z["header"])) if "header" in z else {}
            if h.get("task_type") == "regression" and not h.get("binned_target"):
                raise ValueError("regression target not binned; Dataset2Vec needs classes")
            if np.isnan(X).any():
                raise ValueError("NaN in X; use the canonical copy")
            y = np.unique(y, return_inverse=True)[1]
            z1 = embed(model, X, y, a.n_sub, a.seed)
            rows[p.stem] = z1
            if a.label_check:
                z2 = embed(model, X, np.random.default_rng(a.seed + 1).permutation(y), a.n_sub, a.seed)
                print(f"  {p.stem}: label shuffle moves the vector by {np.linalg.norm(z1 - z2) / np.linalg.norm(z1):.4f} "
                      f"(relative)")
        except Exception as e:
            print(f"FAIL {p.name}: {e}", file=sys.stderr)
            failed += 1
    if rows:
        df = pd.DataFrame(rows).T
        df.columns = [f"d2v_{i}" for i in range(df.shape[1])]
        df.index.name = "dataset_id"
        a.out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(a.out)
        print(f"wrote      {df.shape[0]} tables x {df.shape[1]} dims -> {a.out}")
    print(f"{failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

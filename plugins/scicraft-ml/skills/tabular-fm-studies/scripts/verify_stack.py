#!/usr/bin/env python3
"""Ten-minute check of a tabular foundation-model stack before any study runs on it.

Run it first on every new machine, environment or library release. Each check reproduces a trap met in a real
study (October 2026, tabicl 2.2.0) and prints PASS, FAIL or INFO:

  versions      installed versions against the pins the recipes were verified with
  prior-seed    same seed gives the same table, another seed another table (v1 and v2)
  prior-hash    the v2 graph prior gives the same table under PYTHONHASHSEED 0, 1, 2 (fresh processes),
                with the patch; INFO on how many distinct tables appear without it
  v1-causal     mean off-diagonal |r| of the v1 prior with is_causal sampled against the installed default;
                the default was silently made non-causal in 2.2.0 (about 0.025 against 0.12)
  hook-shapes   TabICL v2 row_interactor and col_embedder output shapes (4 reserved CLS slots)
  hook-clone    an un-cloned hook sees the in-place label addition; a cloned one does not
  label         pooled TabICL v2 vector moves under a label shuffle; v1.1 column and row stages do not
  row-order     pooled TabICL v2 vector is invariant to training-row order (tolerance 1e-3)
  repeat        two identical calls give bit-identical vectors

Dependencies: tabicl==2.2.0 with torch, numpy, pandas; sample_prior.py and dataset_vectors.py beside this file.
The TabICL v2 and v1.1 checkpoints download on first use (about 110 MB each). CPU only; about 1 to 3 minutes.

Usage:
  python verify_stack.py                 # all checks
  python verify_stack.py --skip-model    # prior checks only
"""
from __future__ import annotations

import argparse
import importlib.metadata as md
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PINS = {"tabicl": "2.2.0", "torch": "2.14.1", "numpy": "2.5.3", "pandas": "3.0.6", "scikit-learn": "1.9.1",
        "pymfe": "0.4.4", "tabdpt": "1.3.1", "tabpfn": "9.1.0", "openml": "0.15.1", "data-foundry": "0.0.5",
        "huggingface_hub": "2.1.1"}
RESULTS: list = []


def report(name: str, status: str, msg: str) -> None:
    RESULTS.append(status)
    print(f"{status:4s}  {name:12s} {msg}")


def check_versions() -> None:
    off = 0
    for pkg, pin in PINS.items():
        try:
            v = md.version(pkg)
        except md.PackageNotFoundError:
            v = None
        if v is None:
            report("versions", "INFO", f"{pkg} not installed (verified with {pin})")
        elif v != pin:
            off += 1
            report("versions", "INFO", f"{pkg} {v} installed, recipes verified with {pin}: re-read its changelog and source")
    if not off:
        report("versions", "PASS", "every installed package matches its pin")


def check_prior_seed() -> None:
    import sample_prior as sp
    for prior in ("v1", "v2"):
        ds = sp.prior_dataset(prior, False, 128, 12)
        a, b, c = (sp.generate(ds, prior, s, False)[:2] for s in (11, 11, 12))
        same = np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
        diff = not (a[0].shape == c[0].shape and np.array_equal(a[0], c[0]))
        report("prior-seed", "PASS" if same and diff else "FAIL",
               f"{prior}: same seed identical={same}, other seed differs={diff}")


def _hashes(patch: bool) -> set:
    out = set()
    for h in ("0", "1", "2"):
        cmd = [sys.executable, str(HERE / "sample_prior.py"), "--prior", "v2", "--seeds", "2000001", "--rows", "128",
               "--max-features", "12", "--print-hash"] + ([] if patch else ["--no-hash-patch"])
        r = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": h})
        if r.returncode:
            raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "sample_prior failed")
        out.add(r.stdout.strip().split("hash=")[-1])
    return out


def check_prior_hash() -> None:
    patched = _hashes(True)
    report("prior-hash", "PASS" if len(patched) == 1 else "FAIL",
           f"v2 with patch: {len(patched)} distinct table(s) over PYTHONHASHSEED 0, 1, 2")
    raw = _hashes(False)
    report("prior-hash", "INFO", f"v2 without patch: {len(raw)} distinct table(s) over the same hash seeds")


def check_v1_causal() -> None:
    import sample_prior as sp

    def mean_r(prior):
        ds = sp.prior_dataset(prior, False, 512, 40)
        rs = []
        for s in range(1000000, 1000008):
            X = sp.generate(ds, prior, s, False)[0]
            if X.shape[1] > 1:
                c = np.corrcoef(X.T)
                rs.append(np.nanmean(np.abs(c[np.triu_indices(X.shape[1], 1)])))
        return float(np.mean(rs))

    r_restored, r_default = mean_r("v1"), mean_r("v1_default")
    msg = f"mean |r|: is_causal sampled {r_restored:.3f}, installed default {r_default:.3f}"
    if r_default < 0.5 * r_restored:
        report("v1-causal", "INFO", msg + " -> default is non-causal; pass the restored recipe and say so")
    else:
        report("v1-causal", "INFO", msg + " -> default no longer differs; re-read DEFAULT_FIXED_HP")


def toy(n=256, d=20, k=3, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d)).astype(np.float32)
    y = np.digitize(X[:, :3].sum(1) + 0.5 * rng.normal(size=n), np.quantile(X[:, :3].sum(1), [1 / 3, 2 / 3]))
    return X, y.astype(np.int64)


def check_model() -> None:
    import torch
    import dataset_vectors as dv
    X, y = toy()
    n, d = X.shape
    est = dv.tabicl_estimator(4, "cpu", 0)
    est.fit(X, y)
    got: dict = {}

    def grab(key, clone):
        def hook(m, i, o):
            t = (o[0] if isinstance(o, tuple) else o).detach()
            got.setdefault(key, []).append(t.clone() if clone else t)
        return hook

    hs = [est.model_.row_interactor.register_forward_hook(grab("row", True)),
          est.model_.row_interactor.register_forward_hook(grab("row_noclone", False)),
          est.model_.col_embedder.register_forward_hook(grab("col", True))]
    with torch.no_grad():
        est.predict_proba(X[:1])
    for h in hs:
        h.remove()
    row, col = torch.cat(got["row"], 0), torch.cat(got["col"], 0)
    ok = row.shape[1:] == (n + 1, 512) and col.shape[1:] == (n + 1, d + 4, 128)
    report("hook-shapes", "PASS" if ok else "FAIL",
           f"row_interactor {tuple(row.shape)}, col_embedder {tuple(col.shape)} ({len(got['row'])} hook calls; "
           f"expected (members, {n + 1}, 512) and (members, {n + 1}, {d + 4}, 128))")
    raw = torch.cat(got["row_noclone"], 0)
    moved = float((raw[:, :n] - row[:, :n]).abs().max())
    report("hook-clone", "PASS" if moved > 0 else "INFO",
           f"max |un-cloned - cloned| on train rows = {moved:.3g} (> 0 means the in-place label add is real; clone)")

    yp = dv.content_shuffle(X, y, 1)
    base = dv.tabicl_pooled(X, y, 4, "cpu", 0)
    shuf = dv.tabicl_pooled(X, yp, 4, "cpu", 0)
    rel_v2 = float(np.linalg.norm(base - shuf) / np.linalg.norm(base))
    v11a = dv.enc_tabicl_v11(X, y, argparse.Namespace(device="cpu", seed=0))["tabicl_v11"]
    v11b = dv.enc_tabicl_v11(X, yp, argparse.Namespace(device="cpu", seed=0))["tabicl_v11"]
    rel_v11 = float(np.linalg.norm(v11a - v11b) / np.linalg.norm(v11a))
    report("label", "PASS" if rel_v2 > 0.1 and rel_v11 < 1e-6 else "FAIL",
           f"label shuffle moves v2 pooled vector by {rel_v2:.3f} (label-aware), v1.1 by {rel_v11:.1e} (label-free)")

    p = np.random.default_rng(0).permutation(n)
    perm = dv.tabicl_pooled(X[p], y[p], 4, "cpu", 0)
    rel_row = float(np.linalg.norm(base - perm) / np.linalg.norm(base))
    report("row-order", "PASS" if rel_row < 1e-3 else "FAIL", f"row permutation moves the vector by {rel_row:.1e}")
    again = dv.tabicl_pooled(X, y, 4, "cpu", 0)
    report("repeat", "PASS" if np.array_equal(base, again) else "FAIL",
           f"bit-identical on repeat: {np.array_equal(base, again)}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--skip-model", action="store_true", help="skip the TabICL checkpoint checks")
    ap.add_argument("--skip-prior", action="store_true", help="skip the prior checks")
    a = ap.parse_args(argv)
    try:
        md.version("tabicl")
    except md.PackageNotFoundError:
        print("FAIL: tabicl is not installed", file=sys.stderr)
        return 1
    check_versions()
    steps = []
    if not a.skip_prior:
        steps += [check_prior_seed, check_prior_hash, check_v1_causal]
    if not a.skip_model:
        steps.append(check_model)
    for step in steps:
        try:
            step()
        except Exception as e:
            report(step.__name__.replace("check_", ""), "FAIL", f"{type(e).__name__}: {e}")
    n_fail = RESULTS.count("FAIL")
    print(f"\n{RESULTS.count('PASS')} pass, {n_fail} fail, {RESULTS.count('INFO')} info")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())

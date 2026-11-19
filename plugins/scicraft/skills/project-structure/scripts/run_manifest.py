#!/usr/bin/env python3
"""Write manifest.json into a run's output folder: what ran, on what, with which settings.

  run_manifest.py OUT_DIR [--config FILE ...] [--data ID=VERSION ...] [--packages numpy,torch,...]
                  [--seed N] [--command "..."] [--set KEY=VALUE ...]

The manifest holds: created (local time), the command, every config file (path, sha256 and full
text), data ids with versions, seed, extra key=value settings, Python and package versions,
platform, the accelerator seen by torch when torch is installed, and the git commit of the
current folder with a flag for uncommitted changes. A run cited anywhere must have one.

From Python, inside a run:
  from run_manifest import write_manifest
  write_manifest("results/runs/bench/model", configs=["configs/model.yaml"], data={"suite": "v2"}, seed=0)

Standard library only (torch and the listed packages are read only if installed). Python 3.9 or later.
Exit 0 when the manifest was written; 1 when a config file is missing.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_PACKAGES = ("numpy", "pandas", "scipy", "sklearn", "torch", "polars", "anndata", "matplotlib")
DIST_NAMES = {"sklearn": "scikit-learn", "umap": "umap-learn"}


def package_versions(names) -> dict:
    out = {"python": platform.python_version()}
    for name in names:
        try:
            mod = importlib.import_module(name)
            out[name] = str(getattr(mod, "__version__", "")) or _dist_version(name)
        except Exception:
            out[name] = "missing"
    return out


def _dist_version(name: str) -> str:
    try:
        import importlib.metadata as md
        return md.version(DIST_NAMES.get(name, name).replace("_", "-"))
    except Exception:
        return "?"


def get_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return f"cuda ({torch.cuda.get_device_name(0)})"
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        return "cpu (torch not installed)"
    return "cpu"


def git_state(path: str = ".") -> dict:
    def run(*args):
        return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True).stdout.strip()
    try:
        commit = run("rev-parse", "HEAD")
        dirty = bool(run("status", "--porcelain", "--untracked-files=no"))
    except Exception:
        return {"commit": "none", "dirty": None}
    return {"commit": commit or "none", "dirty": dirty if commit else None}


def write_manifest(out_dir, configs=(), data=None, seed=None, command=None, settings=None,
                   packages=DEFAULT_PACKAGES) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cfgs = []
    for c in configs:
        p = Path(c)
        raw = p.read_bytes()
        cfgs.append({"path": str(c), "sha256": hashlib.sha256(raw).hexdigest(),
                     "text": raw.decode("utf-8", errors="replace")})
    man = {
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "command": command or " ".join(sys.argv),
        "configs": cfgs,
        "data": data or {},
        "seed": seed,
        "settings": settings or {},
        "packages": package_versions(packages),
        "platform": platform.platform(),
        "device": get_device(),
        "git": git_state("."),
    }
    (out / "manifest.json").write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    return man


def pairs(items, what):
    d = {}
    for it in items:
        if "=" not in it:
            raise SystemExit(f"--{what} {it}: expected KEY=VALUE")
        k, v = it.split("=", 1)
        d[k] = v
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog=__doc__.split("\n\n", 1)[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--config", action="append", default=[], help="config file used by the run (repeatable)")
    ap.add_argument("--data", action="append", default=[], metavar="ID=VERSION", help="dataset id and version (repeatable)")
    ap.add_argument("--packages", help=f"comma-separated import names (default: {','.join(DEFAULT_PACKAGES)})")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--command", help="the command that produced the run (default: this command line)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="any other setting (repeatable)")
    a = ap.parse_args()
    missing = [c for c in a.config if not Path(c).is_file()]
    if missing:
        print("config file not found: " + ", ".join(missing), file=sys.stderr)
        return 1
    pk = tuple(x.strip() for x in a.packages.split(",")) if a.packages else DEFAULT_PACKAGES
    man = write_manifest(a.out_dir, a.config, pairs(a.data, "data"), a.seed, a.command, pairs(a.set, "set"), pk)
    g = man["git"]
    print(f"wrote {a.out_dir / 'manifest.json'}: {len(man['configs'])} configs, {len(man['data'])} data ids, "
          f"git {g['commit'][:10]}{' (uncommitted changes)' if g['dirty'] else ''}, device {man['device']}")
    if g["dirty"]:
        print("warning: the working tree has uncommitted changes; the commit alone does not reproduce this run")
    return 0


if __name__ == "__main__":
    sys.exit(main())

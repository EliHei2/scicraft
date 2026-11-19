#!/usr/bin/env python3
"""Install only the packages a hosted runtime lacks, without upgrading its core stack.

  install_missing.py --require umap=umap-learn>=0.5 --require pyarrow=pyarrow [--pin torch ...]
  install_missing.py --require mylib=mylib==1.3 --no-deps otherlib=otherlib==2.0,helper --dry-run
  install_missing.py --self-test

Or from the notebook's setup cell, after copying this file into the package:

  from <pkg>.install_missing import install_missing
  install_missing({"umap": "umap-learn>=0.5"},                 # import name -> pip spec
                  no_deps={"otherlib": ["otherlib==2.0"]})    # pins an old hub client that works with the new one

What it does, in order:
  1. Finds which import names cannot be imported. When none is missing it does nothing.
  2. Writes `pip freeze` lines of the pinned core packages (default: torch, torchvision, torchaudio,
     numpy, pandas, scipy, scikit-learn) to a constraints file, so the host's accelerator stack is never
     upgraded by a dependency.
  3. Installs every missing spec in one `pip install -c <constraints>` call; when that fails, retries
     each spec alone so one bad package does not block the rest.
  4. Installs each --no-deps package with `pip install --no-deps`. Use it only for a package whose
     declared pins are wrong, and write the reason in a comment beside the entry.

Prints what it installed and exits 1 when a required import still fails afterwards.
--dry-run prints the pip commands and installs nothing.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

PINNED = ("torch", "torchvision", "torchaudio", "numpy", "pandas", "scipy", "scikit-learn")


def _missing(names) -> list:
    return [m for m in names if importlib.util.find_spec(m) is None]


def install_missing(requirements: dict, pinned=PINNED, no_deps: dict | None = None,
                    dry_run: bool = False, log=print) -> list:
    """Return the specs that were (or, with dry_run, would be) installed."""
    no_deps = no_deps or {}
    missing = [requirements[m] for m in _missing(requirements)]
    nd = {m: specs for m, specs in no_deps.items() if importlib.util.find_spec(m) is None}
    if not missing and not nd:
        log("nothing missing")
        return []
    pip = [sys.executable, "-m", "pip", "install", "-q"]
    done = []
    with tempfile.TemporaryDirectory() as d:
        cfile = Path(d) / "constraints.txt"
        if missing:
            freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
            keep = {p.lower() for p in pinned}
            pins = [ln for ln in freeze.splitlines() if ln.split("==")[0].strip().lower() in keep]
            cfile.write_text("\n".join(pins) + "\n", encoding="utf-8")
            cmd = pip + ["-c", str(cfile), *missing]
            log("pinned: " + (", ".join(pins) or "none of " + ", ".join(pinned) + " installed"))
            log("run: " + " ".join(cmd))
            if not dry_run:
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    log("group install failed; retrying one by one:\n" + res.stderr[-1500:])
                    for spec in missing:
                        r = subprocess.run(pip + ["-c", str(cfile), spec], capture_output=True, text=True)
                        log(f"  {spec}: {'ok' if r.returncode == 0 else 'FAILED'}")
            done += missing
        for mod, specs in nd.items():
            cmd = pip + ["--no-deps", *specs]
            log("run: " + " ".join(cmd))
            if not dry_run:
                subprocess.run(cmd, capture_output=True, text=True)
            done += list(specs)
    importlib.invalidate_caches()
    return done


def _parse(pairs, multi=False) -> dict:
    out = {}
    for p in pairs:
        if "=" not in p:
            raise SystemExit(f"expected IMPORT=SPEC, got {p!r}")
        mod, spec = p.split("=", 1)
        out[mod.strip()] = [s.strip() for s in spec.split(",") if s.strip()] if multi else spec.strip()
    return out


def self_test() -> int:
    lines: list = []
    fake = "scicraft_selftest_absent_pkg"
    got = install_missing({"json": "json-is-stdlib", fake: f"{fake}==0.1"}, no_deps={fake + "_nd": ["x==1"]},
                          dry_run=True, log=lines.append)
    text = "\n".join(lines)
    checks = {
        "present import skipped": "json-is-stdlib" not in got,
        "missing spec planned": f"{fake}==0.1" in got,
        "constraints passed with -c": " -c " in text,
        "no-deps package planned with --no-deps": "--no-deps x==1" in text,
        "nothing missing does nothing": install_missing({"json": "x"}, dry_run=True, log=lambda s: None) == [],
    }
    for name, ok in checks.items():
        print(("ok    " if ok else "FAIL  ") + name)
    bad = sum(not v for v in checks.values())
    print(f"{len(checks) - bad} of {len(checks)} checks passed (dry run; nothing installed)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--require", action="append", default=[], metavar="IMPORT=SPEC",
                    help="import name and pip spec of a package to install when missing (repeatable)")
    ap.add_argument("--pin", action="append", metavar="NAME",
                    help=f"core package held at its installed version (repeatable; default {', '.join(PINNED)})")
    ap.add_argument("--no-deps", action="append", default=[], metavar="IMPORT=SPEC[,SPEC]",
                    help="install these specs with --no-deps when IMPORT is missing (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="print the pip commands, install nothing")
    ap.add_argument("--self-test", action="store_true", help="check the plan on a fake package, install nothing")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    req = _parse(a.require)
    nd = _parse(a.no_deps, multi=True)
    if not req and not nd:
        ap.error("give at least one --require or --no-deps (or --self-test)")
    install_missing(req, tuple(a.pin) if a.pin else PINNED, nd, a.dry_run)
    if a.dry_run:
        return 0
    still = _missing(list(req) + list(nd))
    for m in still:
        print(f"FAILED: {m} still cannot be imported", file=sys.stderr)
    return 1 if still else 0


if __name__ == "__main__":
    sys.exit(main())

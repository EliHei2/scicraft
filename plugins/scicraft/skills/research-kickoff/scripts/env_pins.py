#!/usr/bin/env python3
"""Print the environment block of the interface notes: package versions as installed, Python, platform, git state.

Ported from a research project's reproducibility manifest (package_versions, _dist_version, git_commit) and
extended: the git line now says whether the tree is dirty, and --pin turns the table into a check.

Two version sources are read for every package, because they can disagree: the module's own __version__ (some
packages have none; read the distribution metadata instead) and importlib.metadata. A package that is not
installed is reported as "missing".

Standard library only.

Usage:
    python3 env_pins.py numpy torch scikit-learn
    python3 env_pins.py numpy torch --pin torch==2.5.0 --repo .      # exit 1 if a pin does not hold
    python3 env_pins.py numpy --json                                    # machine-readable

Exit code: 0 when every --pin holds (or none was given), 1 otherwise.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib
import importlib.metadata as md
import json
import platform
import subprocess
import sys

# import name -> distribution name, for the common cases where they differ
DIST_NAMES = {"sklearn": "scikit-learn", "umap": "umap-learn", "cv2": "opencv-python", "PIL": "Pillow",
              "yaml": "PyYAML", "skimage": "scikit-image", "fitz": "PyMuPDF"}
IMPORT_NAMES = {v.lower(): k for k, v in DIST_NAMES.items()}


def dist_version(name: str) -> str:
    """Version from the installed distribution's metadata, or 'missing'."""
    for cand in (DIST_NAMES.get(name, name), name.replace("_", "-"), name):
        try:
            return md.version(cand)
        except md.PackageNotFoundError:
            continue
    return "missing"


def module_version(name: str) -> str:
    """The module's own __version__, '(none)' if it has none, 'missing' if it does not import."""
    mod_name = IMPORT_NAMES.get(name.lower(), name).replace("-", "_")
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return "missing"
    v = getattr(mod, "__version__", None)
    return str(v) if v else "(none)"


def git_state(path: str | None) -> str:
    """Short commit plus a dirty flag; 'none' outside a repository."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=path, capture_output=True,
                             text=True).stdout.strip()
        if not sha:
            return "none"
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=path, capture_output=True,
                               text=True).stdout.strip()
        return f"{sha} ({'dirty' if dirty else 'clean'})"
    except Exception:
        return "none"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("packages", nargs="*", help="import or distribution names")
    ap.add_argument("--pin", action="append", default=[], metavar="NAME==VERSION",
                    help="required version; repeat for several (exit 1 on mismatch)")
    ap.add_argument("--repo", default=None, help="folder whose git commit is recorded (default: none)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a markdown table")
    a = ap.parse_args()

    pins = {}
    for p in a.pin:
        if "==" not in p:
            ap.error(f"--pin needs NAME==VERSION, got {p!r}")
        k, v = p.split("==", 1)
        pins[k.strip()] = v.strip()
    names = list(dict.fromkeys(a.packages + list(pins)))

    rows = []
    for n in names:
        dv, mv = dist_version(n), module_version(n)
        row = {"package": n, "installed": dv, "__version__": mv}
        if n in pins:
            row["pin"] = pins[n]
            row["pin_ok"] = dv == pins[n]
        rows.append(row)

    info = {"date": _dt.date.today().isoformat(), "python": platform.python_version(),
            "platform": platform.platform(), "executable": sys.executable,
            "git": git_state(a.repo) if a.repo else "not recorded", "packages": rows}

    if a.json:
        print(json.dumps(info, indent=2))
    else:
        print(f"Environment verified {info['date']}: Python {info['python']} on {info['platform']}; "
              f"git {info['git']}.\n")
        print("| package | installed | `__version__` | pin | note |")
        print("|---|---|---|---|---|")
        for r in rows:
            note = ""
            if r["__version__"] not in (r["installed"], "(none)", "missing"):
                note = "module and metadata disagree"
            if r["__version__"] == "(none)" and r["installed"] != "missing":
                note = "no `__version__`; use importlib.metadata.version"
            if "pin" in r and not r["pin_ok"]:
                note = (note + "; " if note else "") + "PIN FAILS"
            print(f"| {r['package']} | {r['installed']} | {r['__version__']} | {r.get('pin', '')} | {note} |")

    bad = [r for r in rows if "pin" in r and not r["pin_ok"]]
    if bad:
        print("\nPins that do not hold: " + ", ".join(f"{r['package']} {r['installed']} != {r['pin']}"
                                                     for r in bad), file=sys.stderr)
        return 1
    if pins:
        print(f"\nAll {len(pins)} pins hold.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

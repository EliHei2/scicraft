#!/usr/bin/env python3
"""Check that a pre-registration was frozen before any result it governs existed. Git timestamps are the receipt.

The freeze point is a tag (--tag, e.g. prereg-v1) or, without one, the first commit that added the PREREG file.
For every file matching --results (a glob relative to the repo), the first commit that added it must come after
the freeze. Files matching the glob that are not committed are reported as unverifiable. With --manifest, every
result file must also mention the manifest's SHA-256 (the stamp of the two-key firewall).

Dependencies: Python 3.9+, git on PATH.

Example:
    python3 prereg_check.py --repo . --prereg experiments/PREREG.md --tag prereg-v1 \
        --results 'results/**/*.json' --manifest experiments/SCORING_MANIFEST.md

Exit codes: 0 every result postdates the freeze; 1 a result predates it, is unverifiable or lacks the stamp;
2 bad input (no git repo, no freeze point).
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def first_added(repo: Path, rel: str) -> int | None:
    out = git(repo, "log", "--diff-filter=A", "--follow", "--format=%ct", "--", rel)
    return int(out.splitlines()[-1]) if out else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="git repository root (default: .)")
    ap.add_argument("--prereg", required=True, help="path of the pre-registration file, relative to the repo")
    ap.add_argument("--tag", help="freeze tag; default: the commit that first added --prereg")
    ap.add_argument("--results", required=True, help="glob of result files relative to the repo")
    ap.add_argument("--manifest", help="scoring manifest whose sha256 every result must contain")
    a = ap.parse_args(argv)

    repo = Path(a.repo).resolve()
    if not git(repo, "rev-parse", "--git-dir"):
        print(f"FAIL  {repo} is not a git repository")
        return 2
    if a.tag:
        t = git(repo, "log", "-1", "--format=%ct", a.tag)
        freeze, how = (int(t) if t else None), f"tag {a.tag}"
    else:
        freeze, how = first_added(repo, a.prereg), f"first commit of {a.prereg}"
    if freeze is None:
        print(f"FAIL  no freeze point found ({how})")
        return 2

    stamp = None
    if a.manifest:
        stamp = hashlib.sha256((repo / a.manifest).read_bytes()).hexdigest()

    problems, ok = [], 0
    files = sorted(p for p in repo.glob(a.results) if p.is_file())
    for p in files:
        rel = str(p.relative_to(repo))
        t = first_added(repo, rel)
        if t is None:
            problems.append(f"unverifiable: {rel} is not committed")
        elif t < freeze:
            problems.append(f"predates freeze: {rel} was committed {freeze - t} s before the {how}")
        elif stamp and stamp not in p.read_text(errors="replace"):
            problems.append(f"no manifest stamp: {rel} does not contain sha256 {stamp[:12]}...")
        else:
            ok += 1
    for pr in problems:
        print(f"ERROR  {pr}")
    print(f"{'FAIL' if problems or not files else 'OK'}  {ok} of {len(files)} result file(s) postdate the "
          f"{how}{' and carry the manifest stamp' if stamp else ''}")
    return 1 if problems or not files else 0


if __name__ == "__main__":
    sys.exit(main())

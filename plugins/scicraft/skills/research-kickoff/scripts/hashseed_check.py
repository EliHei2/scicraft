#!/usr/bin/env python3
"""Check that a generator gives the same output in fresh processes and under different hash seeds.

A fixed seed proves determinism only inside one process. Python randomizes string hashing per process, so code
that iterates over a set of strings can produce different output in each new process even with every random
generator seeded. This happened with a synthetic-data library: two calls in one process were bit-identical,
but the same seed gave different tables in a new process until a set iteration was replaced by sorted(...).

The script runs one command several times, each in a fresh process with a different PYTHONHASHSEED, and compares
the sha256 of what the command produces: its stdout, or a file it writes (--output). Put the seed you want to
test inside the command. Run it once with two different generator seeds as well, to prove the outputs are not
trivially constant (--expect-different).

Standard library only.

Usage:
    python3 hashseed_check.py -- python3 make_table.py --seed 11
    python3 hashseed_check.py --output out.npy -- python3 make_table.py --seed 11 --out out.npy
    python3 hashseed_check.py --seeds 0 1 2 5 -- python3 gen.py 11
    python3 hashseed_check.py --expect-different -- python3 gen.py 11 :: python3 gen.py 12

Exit code: 0 when all runs agree (or, with --expect-different, when the two commands differ), 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], hashseed: str, output: str | None) -> tuple[str, int, str]:
    env = dict(os.environ, PYTHONHASHSEED=hashseed)
    if output and Path(output).exists():
        Path(output).unlink()
    p = subprocess.run(cmd, env=env, capture_output=True)
    if output:
        data = Path(output).read_bytes() if Path(output).exists() else b""
    else:
        data = p.stdout
    return hashlib.sha256(data).hexdigest(), p.returncode, p.stderr.decode(errors="replace")[-400:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", nargs="+", default=["0", "1", "2", "5"],
                    help="PYTHONHASHSEED values, one fresh process each (default: 0 1 2 5)")
    ap.add_argument("--output", default=None, help="hash this file instead of stdout; it is deleted before each run")
    ap.add_argument("--expect-different", action="store_true",
                    help="give two commands separated by '::'; pass if their outputs differ")
    ap.add_argument("cmd", nargs=argparse.REMAINDER, help="the command, after '--'")
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if not cmd:
        ap.error("give the command after '--'")

    if a.expect_different:
        if "::" not in cmd:
            ap.error("--expect-different needs two commands separated by '::'")
        k = cmd.index("::")
        c1, c2 = cmd[:k], cmd[k + 1:]
        h1, r1, e1 = run(c1, a.seeds[0], a.output)
        h2, r2, e2 = run(c2, a.seeds[0], a.output)
        for c, r, e in ((c1, r1, e1), (c2, r2, e2)):
            if r:
                print(f"command failed (exit {r}): {' '.join(c)}\n{e}", file=sys.stderr)
                return 1
        print(f"{' '.join(c1)} -> {h1[:16]}\n{' '.join(c2)} -> {h2[:16]}")
        if h1 == h2:
            print("FAIL: different generator seeds gave identical output; the check above proves nothing")
            return 1
        print("PASS: different generator seeds give different output")
        return 0

    hashes = {}
    for s in a.seeds:
        h, r, e = run(cmd, s, a.output)
        if r:
            print(f"command failed under PYTHONHASHSEED={s} (exit {r}):\n{e}", file=sys.stderr)
            return 1
        hashes[s] = h
        print(f"PYTHONHASHSEED={s:>4}  sha256 {h[:16]}")
    if len(set(hashes.values())) == 1:
        if hashes[a.seeds[0]] == hashlib.sha256(b"").hexdigest():
            print("FAIL: the output is empty in every run; check --output or what the command prints")
            return 1
        print(f"PASS: {len(hashes)} fresh processes, identical output")
        return 0
    print("FAIL: output depends on the process (hash seed). Look for iteration over a set or dict of strings, "
          "unseeded workers, or a library default that reads the environment.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

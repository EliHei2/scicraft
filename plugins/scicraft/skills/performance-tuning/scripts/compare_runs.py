"""Is a speed change objective-neutral? Compare two runs' logged trajectories step by step.

    python3 compare_runs.py before.jsonl after.jsonl --key loss --atol 0
    python3 compare_runs.py before.jsonl after.jsonl --key loss --key grad_norm --atol 1e-4

Suggested, not yet tested in real work: the rule it checks is from the record (a speedup must reproduce an
identical loss trajectory at a fixed seed, and the divergence is quoted through the objective, not through
the kernel), but this script was written for the skill rather than ported.

Both files hold one JSON object per line with a step key (``--step-key``, default ``step``) and the keys to
compare. Steps present in only one file are counted and reported. For each key it prints the number of
common steps, the maximum absolute and relative difference, and the first step where the difference exceeds
``--atol`` + ``--rtol`` * |before|. Exit 0 when every key stays inside the tolerance on every common step,
1 when any key diverges, 2 when there is nothing to compare.

The default tolerance is exact identity (``--atol 0``). Bit identity holds only with one CPU thread and a
deterministic path; with more threads, state the tolerance you used and why. A parity harness bar of 1e-4
(receipts landing near 1e-7) is the one in the record.

Dependencies: Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def _load(path: Path, step_key: str) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for line in path.read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if step_key in r:
            out[int(r[step_key])] = r
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compare two runs' trajectories at matched steps.")
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--key", action="append", default=None, help="logged value to compare (repeatable)")
    p.add_argument("--step-key", default="step")
    p.add_argument("--atol", type=float, default=0.0)
    p.add_argument("--rtol", type=float, default=0.0)
    a = p.parse_args(argv)
    keys = a.key or ["loss"]
    b, c = _load(a.before, a.step_key), _load(a.after, a.step_key)
    common = sorted(set(b) & set(c))
    print(f"[compare] steps: {len(b)} before, {len(c)} after, {len(common)} common, "
          f"{len(set(b) ^ set(c))} in one file only")
    if not common:
        print("[compare] FAIL: no common steps")
        return 2
    diverged = False
    for k in keys:
        n, max_abs, max_rel, first = 0, 0.0, 0.0, None
        for s in common:
            if k not in b[s] or k not in c[s]:
                continue
            x, y = float(b[s][k]), float(c[s][k])
            n += 1
            if math.isnan(x) != math.isnan(y):
                d = math.inf
            elif math.isnan(x):
                d = 0.0
            else:
                d = abs(x - y)
            max_abs = max(max_abs, d)
            if x != 0 and math.isfinite(d):
                max_rel = max(max_rel, d / abs(x))
            if first is None and d > a.atol + a.rtol * abs(x if math.isfinite(x) else 0.0):
                first = s
        if n == 0:
            print(f"[compare] {k}: absent in one or both files (not compared)")
            diverged = True
            continue
        verdict = "identical within tolerance" if first is None else f"DIVERGES from step {first}"
        print(f"[compare] {k}: {n} steps, max |diff| {max_abs:.3e}, max rel {max_rel:.3e}, "
              f"tol atol={a.atol} rtol={a.rtol}: {verdict}")
        diverged = diverged or first is not None
    return 1 if diverged else 0


if __name__ == "__main__":
    raise SystemExit(main())

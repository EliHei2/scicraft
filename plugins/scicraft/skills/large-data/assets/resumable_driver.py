#!/usr/bin/env python3
"""Resumable, shardable driver for a long job over many independent units.

Copy this file into the project, replace process() with the real work, and keep the rest.
What the frame gives you:

  - one output directory per unit, so nothing overwrites anything else
  - a sentinel written LAST (after the output, through temp + os.replace), so a killed
    unit is never mistaken for a finished one
  - the sentinel records a fingerprint of the input and the parameters; a unit reruns
    when its input is newer or the parameters changed (a stale sentinel once served an
    old result after the model behind it was retrained in place)
  - --shard I/N runs every N-th unit, so N jobs split the list with no coordination
  - one line per finished unit appended to progress.tsv and flushed at once, so a crash
    loses at most the unit in flight
  - thread caps set before numpy or polars is imported
  - `status` prints done out of total; `merge` refuses to run until every unit is done

Usage:
  python3 resumable_driver.py run    --units units.txt --out runs/[run_name] [--shard 0/4]
  python3 resumable_driver.py status --units units.txt --out runs/[run_name]
  python3 resumable_driver.py merge  --units units.txt --out runs/[run_name]

units.txt holds one unit per line (an input path, a shard id, a parameter set).
Name [run_name] by its parameters (lr_3e-4_bs_256), never run01.

As shipped, process() counts the rows of each input file (.csv, .tsv, .parquet) so the
frame can be run as is. Needs polars for parquet units only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

# Thread caps before any numeric import: each library otherwise starts one thread per core,
# and several of them together oversubscribe the machine (691 threads once ended a job).
CORES = os.environ.get("CORES", "4")
for var in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS", "RAYON_NUM_THREADS"):
    os.environ.setdefault(var, CORES)
os.environ.setdefault("MALLOC_ARENA_MAX", "2")

PARAMS = {"version": 1}          # [every parameter that changes the output goes here]
SENTINEL = ".done"


def unit_dir(out: Path, unit: str) -> Path:
    safe = hashlib.sha1(unit.encode()).hexdigest()[:10]
    stem = "".join(c if c.isalnum() or c in "-_." else "_" for c in Path(unit).name)[:60]
    return out / "units" / f"{stem}__{safe}"


def fingerprint(unit: str) -> dict:
    """Identity of the input by content metadata. [Use a content hash if files are rewritten in place.]"""
    p = Path(unit)
    if p.exists():
        st = p.stat()
        return {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return {"value": unit}


def params_hash() -> str:
    return hashlib.sha256(json.dumps(PARAMS, sort_keys=True).encode()).hexdigest()[:16]


def is_done(d: Path, unit: str) -> bool:
    s = d / SENTINEL
    if not s.exists():
        return False
    try:
        meta = json.loads(s.read_text())
    except (OSError, ValueError):
        return False
    return meta.get("input") == fingerprint(unit) and meta.get("params") == params_hash()


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def process(unit: str, d: Path) -> dict:
    """[Replace with the real work.] Write outputs into d; return a small summary dict."""
    p = Path(unit)
    if p.suffix == ".parquet":
        import polars as pl
        n = pl.scan_parquet(p).select(pl.len()).collect().item()
    else:
        with open(p, "rb") as f:
            n = max(0, sum(1 for _ in f) - 1)
    write_atomic(d / "result.json", json.dumps({"unit": unit, "rows": n}) + "\n")
    return {"rows": n}


def read_units(path: Path) -> list[str]:
    units = [u.strip() for u in path.read_text().splitlines() if u.strip() and not u.startswith("#")]
    if len(set(units)) != len(units):
        sys.exit("units file has duplicate lines")
    return units


def cmd_run(a, units: list[str]) -> int:
    i, n = (int(x) for x in a.shard.split("/"))
    mine = [u for k, u in enumerate(units) if k % n == i]
    prog = a.out / f"progress_shard{i}of{n}.tsv"
    a.out.mkdir(parents=True, exist_ok=True)
    failed = 0
    with open(prog, "a", buffering=1) as log:
        for k, u in enumerate(mine, 1):
            d = unit_dir(a.out, u)
            if is_done(d, u):
                print(f"[{k}/{len(mine)}] skip (done) {u}", flush=True)
                continue
            d.mkdir(parents=True, exist_ok=True)
            (d / SENTINEL).unlink(missing_ok=True)
            t0 = time.time()
            try:
                summary = process(u, d)
            except Exception as e:  # one bad unit does not stop the shard; it stays not-done
                failed += 1
                print(f"[{k}/{len(mine)}] FAILED {u}: {type(e).__name__}: {e}", flush=True)
                log.write(f"{u}\tFAILED\t{type(e).__name__}\t{time.time() - t0:.1f}\n")
                continue
            write_atomic(d / SENTINEL, json.dumps({"input": fingerprint(u), "params": params_hash(),
                                                   "summary": summary, "seconds": round(time.time() - t0, 1)}))
            log.write(f"{u}\tdone\t{json.dumps(summary)}\t{time.time() - t0:.1f}\n")
            print(f"[{k}/{len(mine)}] done {u} {summary}", flush=True)
    print(f"[shard {i}/{n}] {len(mine) - failed}/{len(mine)} units ok, {failed} failed", flush=True)
    return 1 if failed else 0


def cmd_status(a, units: list[str]) -> int:
    done = [u for u in units if is_done(unit_dir(a.out, u), u)]
    print(f"{len(done)} / {len(units)} units done")
    for u in units:
        if u not in done:
            print(f"  not done: {u}")
    return 0 if len(done) == len(units) else 1


def cmd_merge(a, units: list[str]) -> int:
    missing = [u for u in units if not is_done(unit_dir(a.out, u), u)]
    if missing:
        print(f"refusing to merge: {len(missing)}/{len(units)} units not done (first: {missing[:5]}). "
              "Rerun `run`; finished units are skipped.")
        return 1
    rows = [json.loads((unit_dir(a.out, u) / "result.json").read_text()) for u in units]   # [real merge]
    write_atomic(a.out / "merged.json", json.dumps(rows, indent=1) + "\n")
    total = sum(r["rows"] for r in rows)
    print(f"merged {len(rows)} units, {total:,} rows -> {a.out / 'merged.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Resumable, shardable driver.",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("mode", choices=("run", "status", "merge"))
    p.add_argument("--units", type=Path, required=True, help="file with one unit per line")
    p.add_argument("--out", type=Path, required=True, help="run directory, named by its parameters")
    p.add_argument("--shard", default="0/1", help="I/N: run units whose position modulo N equals I")
    a = p.parse_args(argv)
    units = read_units(a.units)
    return {"run": cmd_run, "status": cmd_status, "merge": cmd_merge}[a.mode](a, units)


if __name__ == "__main__":
    sys.exit(main())

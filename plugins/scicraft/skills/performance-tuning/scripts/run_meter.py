"""Run a command and record what it actually used: wall time, peak RAM, peak GPU memory, which GPU.

    python3 run_meter.py --out stats.json --threads 8 --label predict_split3 -- python3 predict.py --split 3

The command after ``--`` runs as a child process. While it runs, the meter samples the resident memory of
the child's whole process tree (``ps``) and, when ``nvidia-smi`` is on the PATH, the GPU memory of the
tree's processes. When the child exits it writes one JSON record in the same schema as
``instrument.RunMeter`` (``wall_s``, ``ram_peak_gb``, ``vram_peak_gb``, ``gpu``) and exits with the child's
return code.

What the numbers are:
- ``ram_peak_gb``: the largest ``ru_maxrss`` of any waited child (exact, one process).
- ``ram_tree_peak_gb``: the largest sampled sum of RSS over the child's process tree (DataLoader workers
  included); sampled every ``--poll`` seconds, so a spike shorter than that can be missed.
- ``vram_smi_peak_gb``: the largest sampled ``nvidia-smi`` used memory of the tree's processes. It includes
  the CUDA context and the caching allocator's reserve, so it is an upper bound on the live-tensor peak
  (``torch.cuda.max_memory_allocated``, which only in-process code can read: see ``instrument.py``). It does
  catch allocations torch does not see (for example a RAPIDS memory pool).

``--threads N`` pins every common thread pool of the child (OMP, MKL, OpenBLAS, NumExpr, Polars, Rayon) to
N and sets ``MALLOC_ARENA_MAX=2``. Thread oversubscription was the first lever in the record (see SKILL.md).

The wrapper is a pattern derived from the in-process ``RunMeter`` of the source repository; the GPU sampling
path was written for this skill and has not been run on a GPU machine. Dependencies: Python 3.9+, standard
library, ``ps`` (POSIX); ``nvidia-smi`` optional.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path

THREAD_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
               "POLARS_MAX_THREADS", "RAYON_NUM_THREADS")


def _tree(root: int) -> tuple[set[int], int]:
    """Pids of ``root`` and its descendants, and the summed RSS in KB, from one ``ps`` call."""
    try:
        out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True,
                             timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return {root}, 0
    kids: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        pid, ppid, kb = (int(x) for x in parts)
        kids.setdefault(ppid, []).append(pid)
        rss[pid] = kb
    seen, stack = set(), [root]
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        stack.extend(kids.get(pid, []))
    return seen, sum(rss.get(p, 0) for p in seen)


def _smi(pids: set[int]) -> tuple[float, str]:
    """GPU MiB used by ``pids`` according to nvidia-smi, and the GPU names seen."""
    try:
        apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                               "--format=csv,noheader,nounits"], capture_output=True, text=True,
                              timeout=10).stdout
        names = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                               capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return 0.0, ""
    mib = 0.0
    for line in apps.splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) == 2 and parts[0].isdigit() and int(parts[0]) in pids:
            try:
                mib += float(parts[1])
            except ValueError:
                pass
    return mib, ";".join(sorted({n.strip() for n in names.splitlines() if n.strip()}))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--" in argv:
        i = argv.index("--")
        own, cmd = argv[:i], argv[i + 1:]
    else:
        own, cmd = argv, []
    p = argparse.ArgumentParser(description="Run a command and record wall time, peak RAM and GPU memory.",
                                epilog="Everything after -- is the command to run.")
    p.add_argument("--out", type=Path, help="write the JSON record here (default: print only)")
    p.add_argument("--label", default="", help="name for this run in the cost table")
    p.add_argument("--threads", type=int, default=0, help="pin child thread pools to N (0 = leave as is)")
    p.add_argument("--poll", type=float, default=0.5, help="sampling interval in seconds")
    p.add_argument("--no-gpu", action="store_true", help="skip nvidia-smi sampling")
    p.add_argument("--extra", nargs="*", default=[], metavar="KEY=VALUE",
                   help="fields to merge into the record (item counts, config name)")
    a = p.parse_args(own)
    if not cmd:
        p.error("no command given after --")
    env = dict(os.environ)
    if a.threads > 0:
        env.update({v: str(a.threads) for v in THREAD_VARS})
        env["MALLOC_ARENA_MAX"] = "2"
    use_gpu = not a.no_gpu and shutil.which("nvidia-smi") is not None
    t0 = time.perf_counter()
    try:
        child = subprocess.Popen(cmd, env=env)
    except OSError as e:
        print(f"[run_meter] FAIL: cannot start {cmd[0]!r}: {e}", file=sys.stderr)
        return 127
    tree_kb, smi_mib, gpu_names, last = 0, 0.0, "", 0.0
    while child.poll() is None:
        now = time.perf_counter()
        if now - last >= a.poll:
            pids, kb = _tree(child.pid)
            tree_kb = max(tree_kb, kb)
            if use_gpu:
                mib, names = _smi(pids)
                smi_mib, gpu_names = max(smi_mib, mib), names or gpu_names
            last = now
        time.sleep(min(0.05, a.poll))
    wall = time.perf_counter() - t0
    m = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    rec: dict[str, object] = {
        "label": a.label, "cmd": cmd, "returncode": child.returncode, "wall_s": round(wall, 3),
        "ram_peak_gb": round(m / 1e9 if sys.platform == "darwin" else m / 1e6, 3),
        "ram_tree_peak_gb": round(tree_kb / 1e6, 3),
        "vram_smi_peak_gb": round(smi_mib / 1024, 2) if use_gpu else None,
        "gpu": gpu_names if use_gpu else "not sampled",
        "threads": a.threads or None, "poll_s": a.poll,
    }
    for kv in a.extra:
        k, _, v = kv.partition("=")
        rec[k] = v
    text = json.dumps(rec, indent=1)
    print(text, file=sys.stderr)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text)
    if child.returncode != 0:
        print(f"[run_meter] command exited {child.returncode}; record written, treat the numbers as partial",
              file=sys.stderr)
    return child.returncode


if __name__ == "__main__":
    raise SystemExit(main())

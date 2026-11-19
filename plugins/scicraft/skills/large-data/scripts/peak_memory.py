#!/usr/bin/env python3
"""Measure the wall time and peak memory of one command, then extrapolate to the full job.

Run one unit of the work (one shard, one split, one file) under this script before asking
for resources for all of them. It reports what the job used, which is the number a batch
scheduler does not give you: most schedulers report host RAM of the job, never GPU memory,
and a request is not a measurement.

Two subcommands:

  run   run a command and record its wall time and peak resident memory
          peak_rss_max_process_gb   largest single process (getrusage of the children)
          peak_rss_tree_gb          largest sum over the whole process tree, sampled
                                    every --interval seconds with `ps` (worker pools
                                    and data-loader workers show up here)
          gpu_used_gb (with --gpu)  largest device memory in use, sampled with
                                    nvidia-smi; this counts every process on the card,
                                    so read the framework's own peak (for PyTorch,
                                    torch.cuda.max_memory_allocated) when you can
        The record is printed and, with --json, appended as one line to a JSONL file.
        The exit code is the command's exit code.

  fit   fit peak memory against unit size from two or more records and predict the
        peak for the full size, times a margin. With one record it scales linearly
        and says so: memory is often not linear in size (one real GPU profile stayed
        flat across a 4x range of split sizes), so measure a second size.

Examples:
  python3 peak_memory.py run --label shard0 --units 2000000 --json mem.jsonl -- python3 job.py --shard 0
  python3 peak_memory.py run --units 8000000 --json mem.jsonl -- python3 job.py --shard 0 --rows 8000000
  python3 peak_memory.py fit mem.jsonl --full-units 1000000000 --margin 1.3

Standard library only. Python 3.9 or later. Uses `ps` (macOS and Linux) and, with --gpu,
`nvidia-smi`. A sampled peak can miss a spike shorter than --interval; the getrusage value
cannot, but it covers one process only.
"""
from __future__ import annotations

import argparse
import json
import platform
import resource
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


def _rusage_children_gb() -> float:
    m = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return m / 1e9 if sys.platform == "darwin" else m * 1024 / 1e9  # darwin: bytes; Linux: KB


def _tree_rss_gb(root: int) -> float:
    """Sum of RSS over root and all its descendants, from one `ps` call."""
    try:
        out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True,
                             timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return 0.0
    kids: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        try:
            pid, ppid, kb = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            continue
        kids.setdefault(ppid, []).append(pid)
        rss[pid] = kb
    total, stack, seen = 0, [root], set()
    while stack:
        p = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        total += rss.get(p, 0)
        stack.extend(kids.get(p, []))
    return total * 1024 / 1e9


def _gpu_used_gb() -> float:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        return sum(float(x) for x in out.split()) / 1024  # MiB summed over visible cards
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0


def cmd_run(a: argparse.Namespace) -> int:
    command = a.command[1:] if a.command and a.command[0] == "--" else a.command
    if not command:
        print("peak_memory run: give the command after --", file=sys.stderr)
        return 2
    use_gpu = a.gpu and shutil.which("nvidia-smi") is not None
    if a.gpu and not use_gpu:
        print("peak_memory: --gpu asked but nvidia-smi was not found; GPU memory not measured", file=sys.stderr)
    peaks = {"tree": 0.0, "gpu": 0.0}
    t0 = time.perf_counter()
    proc = subprocess.Popen(command)
    stop = threading.Event()

    def sample() -> None:
        while not stop.is_set():
            peaks["tree"] = max(peaks["tree"], _tree_rss_gb(proc.pid))
            if use_gpu:
                peaks["gpu"] = max(peaks["gpu"], _gpu_used_gb())
            stop.wait(a.interval)

    th = threading.Thread(target=sample, daemon=True)
    th.start()
    rc = proc.wait()
    wall = time.perf_counter() - t0
    stop.set()
    th.join()
    rec = {
        "label": a.label,
        "command": " ".join(command),
        "exit_code": rc,
        "wall_s": round(wall, 2),
        "peak_rss_max_process_gb": round(_rusage_children_gb(), 3),
        "peak_rss_tree_gb": round(peaks["tree"], 3),
        "units": a.units,
        "host": platform.node() if a.record_host else None,
        "sample_interval_s": a.interval,
    }
    if use_gpu:
        rec["gpu_used_gb"] = round(peaks["gpu"], 3)
    peak = max(rec["peak_rss_max_process_gb"], rec["peak_rss_tree_gb"])
    print(f"[peak_memory] exit={rc} wall={rec['wall_s']}s peak_rss={peak:.3f} GB "
          f"(max process {rec['peak_rss_max_process_gb']:.3f}, tree sampled {rec['peak_rss_tree_gb']:.3f})"
          + (f" gpu_used={rec['gpu_used_gb']:.3f} GB" if use_gpu else ""), file=sys.stderr)
    if a.units:
        print(f"[peak_memory] {peak / a.units * 1e6:.4f} GB per million units", file=sys.stderr)
    if rc != 0:
        print("[peak_memory] the command FAILED; this record is not a valid profile", file=sys.stderr)
    print(json.dumps(rec))
    if a.json:
        with open(a.json, "a") as f:
            f.write(json.dumps(rec) + "\n")
    return rc


def cmd_fit(a: argparse.Namespace) -> int:
    recs = []
    for line in Path(a.records).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("exit_code", 0) != 0:
            print(f"[fit] skipping failed run: {r.get('label')}", file=sys.stderr)
            continue
        if not r.get("units"):
            print(f"[fit] skipping record without --units: {r.get('label')}", file=sys.stderr)
            continue
        key = a.metric
        val = max(r.get("peak_rss_max_process_gb", 0), r.get("peak_rss_tree_gb", 0)) if key == "rss" \
            else r.get("gpu_used_gb")
        if val is None:
            continue
        recs.append((float(r["units"]), float(val), float(r.get("wall_s", 0))))
    if not recs:
        print("[fit] no usable records", file=sys.stderr)
        return 1
    recs.sort()
    n = a.full_units
    if len({u for u, _, _ in recs}) == 1:
        u, m, w = recs[-1]
        est, west = m * n / u, w * n / u
        print(f"[fit] ONE size measured ({u:,.0f} units): linear scaling assumed. Measure a second size.")
    else:
        xs = [u for u, _, _ in recs]
        ys = [m for _, m, _ in recs]
        ws = [w for _, _, w in recs]
        mx, my, mw = sum(xs) / len(xs), sum(ys) / len(ys), sum(ws) / len(ws)
        sxx = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        wslope = sum((x - mx) * (w - mw) for x, w in zip(xs, ws)) / sxx
        icpt, wicpt = my - slope * mx, mw - wslope * mx
        est, west = icpt + slope * n, wicpt + wslope * n
        print(f"[fit] {len(recs)} records over {min(xs):,.0f} to {max(xs):,.0f} units: "
              f"{a.metric} = {icpt:.3f} GB + {slope * 1e6:.4f} GB per million units")
        rel = (max(ys) - min(ys)) / max(max(ys), 1e-9)
        if rel < 0.15 and max(xs) >= 2 * min(xs):
            print("[fit] memory is nearly FLAT across the measured sizes: the fixed cost dominates; "
                  "unit size is not what bounds it.")
        if n > 4 * max(xs):
            print(f"[fit] the target is {n / max(xs):.0f}x the largest measured size: extrapolation risk, "
                  "check against a measured anchor.")
    print(f"[fit] predicted peak {a.metric} at {n:,.0f} units: {est:.2f} GB; "
          f"request about {est * a.margin:.2f} GB (margin {a.margin}); predicted wall about "
          + (f"{west / 3600:.2f} h" if west >= 3600 else f"{west:.0f} s"))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Measure peak memory of a command and extrapolate it.",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a command and record wall time and peak memory")
    r.add_argument("--label", default="", help="name of this measurement (shard, split size)")
    r.add_argument("--units", type=float, default=None, help="size of the unit run (rows, molecules, files)")
    r.add_argument("--json", type=Path, default=None, help="append the record to this JSONL file")
    r.add_argument("--interval", type=float, default=0.2, help="sampling interval in seconds (default 0.2)")
    r.add_argument("--gpu", action="store_true", help="also sample device memory with nvidia-smi")
    r.add_argument("--record-host", action="store_true", help="store the host name in the record")
    r.add_argument("command", nargs=argparse.REMAINDER, help="-- then the command to run")
    f = sub.add_parser("fit", help="predict the full-size peak from recorded runs")
    f.add_argument("records", help="JSONL file written by run --json")
    f.add_argument("--full-units", type=float, required=True, help="size of the full job, same unit as --units")
    f.add_argument("--margin", type=float, default=1.3, help="safety factor on the prediction (default 1.3)")
    f.add_argument("--metric", choices=("rss", "gpu"), default="rss")
    a = p.parse_args(argv)
    return cmd_run(a) if a.cmd == "run" else cmd_fit(a)


if __name__ == "__main__":
    sys.exit(main())

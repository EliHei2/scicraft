"""Cost table across runs: one row per stats JSON (from run_meter.py or instrument.RunMeter.summary).

    python3 cost_table.py runs/*/stats*.json [--items n_items] [--csv cost.csv]

Ported from the cost-table script of a self-supervised training repository. What a user of shared compute
wants at a glance: which GPU each run landed on, wall time, peak VRAM (live tensors and allocator reserve, or
the nvidia-smi sample), peak RAM, item count and throughput, to compare against what was requested. Totals
line: parallel jobs finish when the slowest does, so the wall of a batch is the maximum, not the sum.

Dependencies: Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _num(v: object) -> float:
    try:
        return float(v)                                             # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Summarize stats JSON files into one cost table.")
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--items", default="n_items", help="key holding the item count (rows, tokens, samples)")
    p.add_argument("--csv", type=Path, default=None, help="also write the table as CSV")
    a = p.parse_args(argv)
    rows = []
    for f in a.files:
        try:
            s = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError) as e:
            print(f"[cost_table] skip {f}: {e}")
            continue
        vram = s.get("vram_peak_gb")
        if vram in (None, 0, 0.0) and s.get("vram_smi_peak_gb") is not None:
            vram = s["vram_smi_peak_gb"]
        wall = _num(s.get("wall_s"))
        items = _num(s.get(a.items))
        rows.append({"run": s.get("label") or f.parent.name + "/" + f.stem,
                     "gpu": str(s.get("gpu", ""))[:22], "wall_s": round(wall, 1),
                     "vram_gb": vram, "vram_resv_gb": s.get("vram_reserved_gb"),
                     "ram_gb": s.get("ram_tree_peak_gb") or s.get("ram_peak_gb"),
                     "items": int(items), "items_per_s": round(items / wall, 1) if wall and items else None,
                     "rc": s.get("returncode", 0)})
    if not rows:
        print("[cost_table] FAIL: no readable stats files")
        return 1
    cols = ["run", "gpu", "wall_s", "vram_gb", "vram_resv_gb", "ram_gb", "items", "items_per_s", "rc"]
    width = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in cols}
    line = "  ".join(c.ljust(width[c]) for c in cols)
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(r[c]).ljust(width[c]) for c in cols))
    print("-" * len(line))
    failed = sum(1 for r in rows if r["rc"] not in (0, None))
    print(f"[cost_table] {len(rows)} runs, {failed} with non-zero exit | peak of runs: "
          f"VRAM {max(_num(r['vram_gb']) for r in rows)} GB, RAM {max(_num(r['ram_gb']) for r in rows)} GB, "
          f"slowest {max(r['wall_s'] for r in rows)} s wall (parallel jobs: the batch wall is the slowest, "
          f"not the sum)")
    if a.csv:
        with a.csv.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Sizing gate: read a short run's jsonl into one verdict before the long run starts.

    python3 sizing_probe.py run.jsonl --min-gpu-busy 0.80 --min-steps 2000 [--out sizing.json]

Ported from the sizing probe of a self-supervised training repository. It reports p50 and p99 step time,
p99 peak VRAM, the per-phase split, GPU-hours per 100k steps and the median ``gpu_busy``, and EXITS 3 when
``gpu_busy_p50`` misses the gate, so a launcher chain can refuse to start a starving configuration. A
starving step is a failed gate, not a slow bill. Thresholds of record: 0.80 to start, 0.60 as the in-run kill.

Size on about 2,000 steps of the densest data, not 300: peak VRAM is set by the rarest batch, and short
runs read the peak about 20% low (63.9 vs 80.5 GB in the record). It refuses to size on fewer than
``--min-steps`` logged steps.

Input: one JSON object per line with ``ms_step`` (required), ``step``, ``gpu_busy`` (1 - loader-wait
fraction; NOT a total-span busy figure), ``vram_peak_gb`` and any ``gpu_ms_<phase>`` keys. Lines without
``ms_step`` are skipped. Records without ``gpu_busy`` are reported as absent, never assumed busy.

Dependencies: Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _pct(v: list[float], q: float) -> float:
    if not v:
        return float("nan")
    s = sorted(v)
    return s[min(len(s) - 1, int(q * (len(s) - 1)))]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sizing gate over a run's jsonl (step time, VRAM, gpu_busy).")
    p.add_argument("jsonl", type=Path)
    p.add_argument("--min-gpu-busy", type=float, default=0.80)
    p.add_argument("--min-steps", type=int, default=2000, help="refuse to size on fewer logged steps")
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args(argv)
    ms, busy, vram, phases = [], [], [], {}
    last_step = 0
    for line in a.jsonl.read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "ms_step" not in r:
            continue
        last_step = max(last_step, int(r.get("step", 0)))
        ms.append(float(r["ms_step"]))
        if "gpu_busy" in r:
            busy.append(float(r["gpu_busy"]))
        if "vram_peak_gb" in r:
            vram.append(float(r["vram_peak_gb"]))
        for k, v in r.items():
            if k.startswith("gpu_ms_") and k != "gpu_ms_total":
                phases.setdefault(k, []).append(float(v))
    if not ms:
        print(f"[sizing] FAIL: {a.jsonl} has no records with ms_step")
        return 2
    if last_step < a.min_steps:
        print(f"[sizing] FAIL: only {last_step} steps logged; size on >= {a.min_steps} "
              f"(peak VRAM is set by the rarest batch)")
        return 2
    rep = {"n_logged": len(ms), "last_step": last_step,
           "ms_step_p50": _pct(ms, 0.5), "ms_step_p99": _pct(ms, 0.99),
           "gpu_busy_p50": _pct(busy, 0.5) if busy else None,
           "vram_peak_gb_p99": _pct(vram, 0.99) if vram else None,
           "gpuh_per_100k": _pct(ms, 0.5) * 100_000 / 3.6e6,
           "phase_ms_p50": {k: _pct(v, 0.5) for k, v in sorted(phases.items())},
           "gate_min_gpu_busy": a.min_gpu_busy}
    text = json.dumps(rep, indent=1)
    print(text)
    if a.out:
        a.out.write_text(text)
    if rep["gpu_busy_p50"] is None:
        print("[sizing] GATE NOT CHECKED: no gpu_busy in the records (absent, not assumed busy)")
        return 4
    if rep["gpu_busy_p50"] < a.min_gpu_busy:
        print(f"[sizing] GATE FAILED: gpu_busy_p50 {rep['gpu_busy_p50']:.2f} < {a.min_gpu_busy}; "
              f"do not start the long run on this configuration")
        return 3
    print(f"[sizing] gate passed: gpu_busy_p50 {rep['gpu_busy_p50']:.2f} >= {a.min_gpu_busy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""True-usage instrumentation for a training or inference loop: per-phase time, peak VRAM and RAM, measured
rather than requested.

Ported from the instrumentation module of a self-supervised training repository (three classes that were
used there in production) with project names removed and torch made optional.

- ``Instrument``: per-step, per-phase **device time** via CUDA events, one ``synchronize`` per step (not one
  per phase, which would serialize the pipeline). Arm it only on the steps you log (``arm``), so the other
  steps keep full CPU/GPU overlap. A logged step is then a measured step and slightly slower than a bare
  one; pair it with a plain wall-clock mean over the window.
- ``StepProfiler``: per-section **wall time** bracketed by ``synchronize`` on both sides. Correct for CPU
  sections (data loading) and GPU sections alike, where bare CUDA events read about 0 for CPU work. The
  syncs make it a profiling aid for a ``--debug``-style run, not a production path.
- ``RunMeter``: whole-run wall time, peak VRAM and peak RAM for one-shot jobs (predict, eval, render). It
  reports wall clock because a job dominated by CPU work between small GPU calls is understated by device
  time.

Peak VRAM is ``torch.cuda.max_memory_allocated`` (live tensors). ``max_memory_reserved`` (the caching
allocator's pool) is printed beside it for reference only. A batch scheduler's "max memory" is host RAM,
never VRAM. RAM is the resident set size from ``/proc/self/statm`` on Linux, ``ru_maxrss`` elsewhere.

Dependencies: Python 3.9+, standard library; ``torch`` optional (without it every class falls back to
wall-clock timing and reports VRAM as 0). ``--demo`` needs torch.

Usage as a library (copy this file next to your training script)::

    from instrument import Instrument
    inst = Instrument(device)
    for step in range(n):
        inst.arm(step % log_every == 0)
        with inst.phase("data"):     batch = next(it)
        with inst.phase("forward"):  loss = model(batch)
        with inst.phase("backward"): loss.backward()
        rec = inst.step_record()     # {} on unarmed steps
        if rec: log({"step": step, **rec})

Usage from the shell::

    python3 instrument.py --demo run.jsonl --steps 600     # toy CPU loop that writes a sizing-ready jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:
    import torch
except ImportError:                                               # torch is optional for RunMeter / CPU use
    torch = None

_PAGE = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096


def rss_gb() -> float:
    """Current resident set size in GB (Linux ``/proc``); elsewhere the lifetime peak from ``ru_maxrss``."""
    try:
        with open("/proc/self/statm") as f:
            return int(f.read().split()[1]) * _PAGE / 1e9
    except OSError:
        return peak_rss_gb()


def peak_rss_gb() -> float:
    """Peak resident set size in GB for the process lifetime (``ru_maxrss``: KB on Linux, bytes on macOS)."""
    m = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return m / 1e9 if sys.platform == "darwin" else m / 1e6


def _is_cuda(device: Any) -> bool:
    return (torch is not None and device is not None and getattr(device, "type", str(device)) == "cuda"
            and torch.cuda.is_available())


class RunMeter:
    """Whole-run wall time + peak VRAM + peak RAM for one-shot jobs. ``mark(label)`` closes a phase;
    ``summary(**extra)`` returns the record (merge item counts and throughput through ``extra``)."""

    def __init__(self, device: Any = None) -> None:
        self.device = device
        self.cuda = _is_cuda(device)
        self.marks: list[tuple[str, float]] = []
        self._t0 = self._last = time.perf_counter()
        if self.cuda:
            torch.cuda.reset_peak_memory_stats(device)              # baseline before the model is built

    def mark(self, label: str) -> None:
        now = time.perf_counter()
        self.marks.append((label, now - self._last))
        self._last = now

    def summary(self, **extra: Any) -> dict[str, Any]:
        if self.cuda:
            torch.cuda.synchronize(self.device)
        d: dict[str, Any] = {"wall_s": round(time.perf_counter() - self._t0, 3),
                             "phases_s": {k: round(v, 3) for k, v in self.marks}}
        if self.cuda:
            d["vram_peak_gb"] = round(torch.cuda.max_memory_allocated(self.device) / 1e9, 2)
            d["vram_reserved_gb"] = round(torch.cuda.max_memory_reserved(self.device) / 1e9, 2)
            d["gpu"] = torch.cuda.get_device_name(self.device)    # which card the job actually landed on
        else:
            d["vram_peak_gb"], d["gpu"] = 0.0, "cpu"
        d["ram_peak_gb"] = round(peak_rss_gb(), 3)
        d.update(extra)
        return d


class Instrument:
    """Per-step, per-phase device-time and peak-VRAM recorder. ``enabled=False`` makes every call a no-op."""

    def __init__(self, device: Any = None, enabled: bool = True) -> None:
        self.device = device
        self.enabled = enabled
        self.cuda = enabled and _is_cuda(device)
        self.active = True
        self._events: dict[str, tuple[Any, Any]] = {}
        self._wall: dict[str, float] = {}
        self._vram: dict[str, float] = {}
        self._order: list[str] = []

    def arm(self, on: bool) -> None:
        """Measure this step or skip it. The step sync stops the host running ahead, so pay it only on the
        steps that are logged."""
        self.active = on

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        if not (self.enabled and self.active):
            yield
            return
        if name not in self._order:
            self._order.append(name)
        if self.cuda:
            torch.cuda.reset_peak_memory_stats(self.device)        # isolate this phase's peak
            start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            start.record()
            try:
                yield
            finally:
                end.record()
                self._events[name] = (start, end)
                self._vram[name] = torch.cuda.max_memory_allocated(self.device) / 1e9
        else:
            t0 = time.perf_counter()
            try:
                yield
            finally:
                self._wall[name] = self._wall.get(name, 0.0) + (time.perf_counter() - t0)

    def step_record(self) -> dict[str, float]:
        """One synchronize, then ``gpu_ms_<phase>``, ``gpu_ms_total``, ``vram_peak_gb`` and RAM; resets."""
        if not (self.enabled and self.active):
            return {}
        rec: dict[str, float] = {}
        total = 0.0
        if self.cuda:
            torch.cuda.synchronize(self.device)
            for name in self._order:
                if name in self._events:
                    s, e = self._events[name]
                    ms = float(s.elapsed_time(e))
                    rec[f"gpu_ms_{name}"] = ms
                    total += ms
                    rec[f"vram_peak_{name}_gb"] = self._vram.get(name, 0.0)
            rec["vram_peak_gb"] = max(self._vram.values(), default=0.0)
            rec["vram_reserved_gb"] = torch.cuda.max_memory_reserved(self.device) / 1e9
        else:
            for name in self._order:
                ms = self._wall.get(name, 0.0) * 1000.0
                rec[f"gpu_ms_{name}"] = ms                         # wall-ms fallback, same key for one schema
                total += ms
            rec["vram_peak_gb"] = 0.0
        rec["gpu_ms_total"] = total
        rec["ram_rss_gb"] = rss_gb()
        rec["ram_peak_gb"] = peak_rss_gb()
        self._events, self._wall, self._vram = {}, {}, {}
        return rec


class StepProfiler:
    """Sync-bracketed wall timer per section, for profiling runs. ``snapshot(n)`` gives mean ms/step per
    section plus the window's peak VRAM, then resets."""

    def __init__(self, enabled: bool, device: Any = None) -> None:
        self.enabled = enabled
        self.cuda = enabled and _is_cuda(device)
        self.ms: dict[str, float] = {}

    @contextmanager
    def section(self, name: str) -> Iterator[None]:
        if not self.enabled:
            yield
            return
        if self.cuda:
            torch.cuda.synchronize()                               # do not charge earlier work to this section
        t0 = time.perf_counter()
        yield
        if self.cuda:
            torch.cuda.synchronize()                               # wait for this section's kernels
        self.ms[name] = self.ms.get(name, 0.0) + 1000.0 * (time.perf_counter() - t0)

    def snapshot(self, n_steps: int) -> dict[str, float]:
        out = {f"t_{k}_ms": v / max(1, n_steps) for k, v in self.ms.items()}
        if self.cuda:
            out["vram_alloc_gb"] = torch.cuda.max_memory_allocated() / 1e9
            out["vram_reserved_gb"] = torch.cuda.max_memory_reserved() / 1e9
            torch.cuda.reset_peak_memory_stats()
        out["ram_rss_gb"] = rss_gb()
        self.ms = {}
        return out


def _demo(out: Path, steps: int, log_every: int, loader_ms: float, seed: int) -> int:
    """Toy loop: a small MLP on CPU with a simulated loader wait. Writes one jsonl record per logged step
    with ``ms_step``, ``gpu_busy`` (1 - loader-wait fraction), the phase split and the loss."""
    if torch is None:
        print("[instrument] --demo needs torch", file=sys.stderr)
        return 2
    torch.manual_seed(seed)
    dev = torch.device("cpu")
    model = torch.nn.Sequential(torch.nn.Linear(64, 256), torch.nn.GELU(), torch.nn.Linear(256, 1))
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    inst, meter = Instrument(dev), RunMeter(dev)
    g = torch.Generator().manual_seed(seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        for step in range(1, steps + 1):
            inst.arm(step % log_every == 0)
            t0 = time.perf_counter()
            with inst.phase("data"):
                time.sleep(loader_ms / 1000.0)                     # stands in for a CPU-bound loader
                x = torch.randn(128, 64, generator=g)
                y = x[:, :1] * 0.5
            t_data = time.perf_counter() - t0
            with inst.phase("forward"):
                loss = torch.nn.functional.mse_loss(model(x), y)
            with inst.phase("backward"):
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
            t_step = time.perf_counter() - t0
            rec = inst.step_record()
            if rec:
                rec.update({"step": step, "loss": float(loss), "ms_step": 1000.0 * t_step,
                            "gpu_busy": max(0.0, 1.0 - t_data / t_step)})
                fh.write(json.dumps(rec) + "\n")
    meter.mark("train")
    print(json.dumps(meter.summary(steps=steps, jsonl=str(out))))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Per-phase timing and memory instrumentation (library + demo).")
    p.add_argument("--demo", type=Path, metavar="OUT_JSONL", help="run the toy loop and write its jsonl here")
    p.add_argument("--steps", type=int, default=600)
    p.add_argument("--log-every", type=int, default=10)
    p.add_argument("--loader-ms", type=float, default=2.0, help="simulated loader wait per step (ms)")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    if a.demo is None:
        p.print_help()
        return 0
    return _demo(a.demo, a.steps, a.log_every, a.loader_ms, a.seed)


if __name__ == "__main__":
    raise SystemExit(main())

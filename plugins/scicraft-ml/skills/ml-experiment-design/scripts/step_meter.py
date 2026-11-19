#!/usr/bin/env python3
"""True-usage instrumentation for a training loop and for one-shot jobs: per-phase GPU time (real device time via
CUDA events, not wall clock), peak VRAM (``max_memory_allocated``, the true peak of live tensors, not the caching
allocator's pool and not what the scheduler was asked for) and RAM (resident set size, not the requested memory).

Copied from the author's training code and made importable without torch (CPU wall-time fallback).

Usage in a training loop::

    from step_meter import Instrument, JsonlLog
    inst, log = Instrument(device), JsonlLog("runs/arm1/train.jsonl")
    for step in range(n):
        inst.arm(step % log_every == 0)          # measure only the steps that are logged
        with inst.phase("data"):     batch = next(loader)
        with inst.phase("forward"):  loss = model(batch)
        with inst.phase("backward"): loss.backward()
        if step % log_every == 0:
            log.write({"step": step, "loss": float(loss), **inst.step_record()})

One-shot jobs (encode, evaluate, render) use ``RunMeter``: wall time per ``mark()``, peak VRAM since construction,
peak RSS, GPU name.

Design: one CUDA start/end event pair per (phase, step); ``step_record`` does the single ``synchronize`` of the step
and reads every elapsed time back, so instrumentation adds one sync per logged step (one per phase would serialize
the pipeline). On CPU, or without torch, phases fall back to ``perf_counter`` and VRAM reads 0: the API is the same,
so the loop never branches.

Dependencies: Python 3.9+; torch optional. Run ``python3 step_meter.py --demo out.jsonl`` to write a sample log.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from contextlib import contextmanager
from typing import Iterator

try:
    import torch
except ImportError:                                                 # CPU-only use without torch
    torch = None

_PAGE = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096  # bytes/page (Linux statm is in pages)


def _cuda_ok(device) -> bool:
    return torch is not None and getattr(device, "type", str(device)) == "cuda" and torch.cuda.is_available()


def rss_gb() -> float:
    """Current resident set size (GB). ``/proc/self/statm`` on Linux; elsewhere ``ru_maxrss`` (the peak)."""
    try:
        with open("/proc/self/statm") as f:
            return int(f.read().split()[1]) * _PAGE / 1e9           # field 1 = resident pages
    except OSError:
        return peak_rss_gb()


def peak_rss_gb() -> float:
    """Peak resident set size (GB) for the process lifetime (``ru_maxrss``: KB on Linux, bytes on macOS)."""
    m = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return m / 1e9 if sys.platform == "darwin" else m / 1e6


class RunMeter:
    """Whole-run wall time, peak VRAM and peak RAM for one-shot jobs. Wall clock on purpose: a whole-dataset encode
    is dominated by host work between small GPU forwards, so device time would understate the wait. VRAM peak covers
    the whole run (reset at construction, before the model is built)."""

    def __init__(self, device="cpu") -> None:
        self.device = device
        self.cuda = _cuda_ok(device)
        self.marks: list[tuple[str, float]] = []                    # (phase label, wall seconds) in call order
        self._t0 = self._last = time.perf_counter()
        if self.cuda:
            torch.cuda.reset_peak_memory_stats(self.device)

    def mark(self, label: str) -> None:
        """Record wall seconds since the previous mark (or the start) under ``label``."""
        now = time.perf_counter()
        self.marks.append((label, now - self._last))
        self._last = now

    def summary(self, **extra: object) -> dict:
        """Total and per-phase wall, peak VRAM (allocated and reserved), peak RAM, GPU name, plus ``extra``."""
        if self.cuda:
            torch.cuda.synchronize(self.device)
        d: dict = {"wall_s": round(time.perf_counter() - self._t0, 3),
                   "phases_s": {k: round(v, 3) for k, v in self.marks}}
        if self.cuda:
            d["vram_peak_gb"] = round(torch.cuda.max_memory_allocated(self.device) / 1e9, 2)
            d["vram_reserved_gb"] = round(torch.cuda.max_memory_reserved(self.device) / 1e9, 2)
            d["gpu"] = torch.cuda.get_device_name(self.device)
        else:
            d["vram_peak_gb"], d["gpu"] = 0.0, "cpu"
        d["ram_peak_gb"] = round(peak_rss_gb(), 3)
        d.update(extra)
        return d


class Instrument:
    """Per-step, per-phase true-usage recorder. ``enabled=False`` makes every method a cheap no-op."""

    def __init__(self, device="cpu", enabled: bool = True) -> None:
        self.device = device
        self.cuda = enabled and _cuda_ok(device)
        self.enabled = enabled
        self.active = True
        self._events: dict = {}                                     # phase -> (start, end) CUDA events this step
        self._wall: dict[str, float] = {}                           # phase -> wall seconds (CPU path)
        self._vram: dict[str, float] = {}                           # phase -> peak allocated GB during the phase
        self._order: list[str] = []                                 # stable column order

    def arm(self, on: bool) -> None:
        """Instrument this step or skip it. ``step_record`` synchronizes, which stops the host running ahead; pay it
        only on logged steps. A measured step is slightly slower, so per-phase times are an upper bound; pair them
        with a plain wall-clock mean over the window."""
        self.active = on

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        """Time and memory-profile the enclosed block under ``name``; repeats within a step accumulate."""
        if not (self.enabled and self.active):
            yield
            return
        if name not in self._order:
            self._order.append(name)
        if self.cuda:
            torch.cuda.reset_peak_memory_stats(self.device)
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

    def step_record(self) -> dict:
        """Close the step: one synchronize, read every phase's device ms and peak VRAM plus RSS, reset. Keys:
        ``gpu_ms_<phase>``, ``gpu_ms_total``, ``vram_peak_<phase>_gb``, ``vram_peak_gb``, ``vram_reserved_gb``,
        ``ram_rss_gb``, ``ram_peak_gb``."""
        if not (self.enabled and self.active):
            return {}
        rec: dict = {}
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
                rec[f"gpu_ms_{name}"] = ms                          # wall-ms fallback (no CUDA)
                total += ms
            rec["vram_peak_gb"] = 0.0
        rec["gpu_ms_total"] = total
        rec["ram_rss_gb"] = rss_gb()
        rec["ram_peak_gb"] = peak_rss_gb()
        self._events, self._wall, self._vram = {}, {}, {}
        return rec


class JsonlLog:
    """Append one JSON line per record. Telemetry must never kill training: a failed write drops the record and
    increments ``dropped``, which is written into the next record that succeeds."""

    def __init__(self, path: str) -> None:
        self.path, self.dropped = path, 0
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        except OSError:
            pass

    def write(self, rec: dict) -> bool:
        try:
            if self.dropped:
                rec = {**rec, "log_dropped": self.dropped}
            with open(self.path, "a") as f:
                f.write(json.dumps(rec, default=float) + "\n")
            self.dropped = 0
            return True
        except Exception:                                           # noqa: BLE001  any failure drops the record
            self.dropped += 1
            return False


def _demo(path: str, steps: int, log_every: int) -> int:
    """A small CPU loop with the same phases as a training step; writes a sample log and a job summary."""
    meter = RunMeter("cpu")
    inst, log = Instrument("cpu"), JsonlLog(path)
    data = [[float((i * 7 + j) % 13) for j in range(256)] for i in range(64)]
    meter.mark("setup")
    for step in range(steps):
        inst.arm(step % log_every == 0)
        with inst.phase("data"):
            batch = data[step % len(data)]
        with inst.phase("forward"):
            loss = sum(x * x for x in batch) / len(batch)
        with inst.phase("backward"):
            _ = [2 * x for x in batch]
        if step % log_every == 0:
            log.write({"step": step, "loss": loss, **inst.step_record()})
    meter.mark("train")
    summary = meter.summary(steps=steps, log=path)
    log.write({"job_summary": summary})
    n = sum(1 for _ in open(path))
    keys = sorted(json.loads(open(path).readline()))
    print(f"OK  wrote {n} records to {path}; step keys: {', '.join(keys)}")
    print(f"    job summary: {json.dumps(summary)}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", metavar="OUT.jsonl", help="run a small CPU loop and write a sample log")
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--log-every", type=int, default=10)
    a = ap.parse_args(argv)
    if not a.demo:
        ap.print_help()
        return 0
    return _demo(a.demo, a.steps, a.log_every)


if __name__ == "__main__":
    sys.exit(main())

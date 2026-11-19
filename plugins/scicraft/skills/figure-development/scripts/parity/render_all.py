#!/usr/bin/env python3
"""Render every unit of a figure repository and snapshot its outputs for render-parity checks.

A unit is one command that writes figure outputs (a panel script, a standalone
supplement, a composer). Units are listed in a JSON registry (see
assets/units.example.json):

    {
      "output_dirs": ["figures/figure_3", "figures/figure_3/panels"],
      "script_globs": ["code/figure_3/*.py"],
      "ignore_prefixes": ["_mockup", "_scratch"],
      "units": [
        {"label": "panel_a", "cmd": ["code/figure_3/panel_a_bench.py"], "order": 0},
        {"label": "compose", "cmd": ["code/figure_3/_compose_figure_3.py"], "order": 2}
      ]
    }

A `cmd` whose first item ends in .py runs with the current interpreter. `order`
groups runs so dependencies hold: panels (0) before supplements (1) before the
composers (2) that place their PDFs. `"cost": "heavy"` marks units that
--skip-heavy leaves out. Each unit runs as its own subprocess, because plotting
scripts mutate global state (matplotlib rcParams) at import, which would bleed
between panels if run in one process.

    python render_all.py --repo . --units units.json --baseline   # freeze the state before a refactor
    python render_all.py --repo . --units units.json              # render the current state to compare

Writes under <snap>/<baseline|current>/ (default snap: <repo>/_verify_snap):
    manifest.tsv    one row per output (sha256, pdf page size in pt, kind)
    grids.npz       perceptual grids keyed by output path
    png/...         copies of PNG outputs, for the compare.py triptychs
    render_log.tsv  per-unit return code, wall time, stderr tail
--baseline also copies manifest.tsv to <snap>/baseline_manifest.tsv; track that file.

Always run the full registry before comparing: a filtered run (--only) leaves
outputs of skipped units unrefreshed, so a stale composer can pass unnoticed.

Dependencies: numpy, Pillow, PyMuPDF (for PDF outputs). Exit 1 if a unit failed.
Adapted from the render-parity harness of a paper-figures repository.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sig  # noqa: E402


def load_registry(path: Path) -> dict:
    reg = json.loads(path.read_text())
    for key in ("output_dirs", "units"):
        if key not in reg:
            sys.exit(f"registry {path} has no '{key}'")
    for u in reg["units"]:
        if "label" not in u or "cmd" not in u:
            sys.exit(f"unit without label or cmd: {u}")
        u.setdefault("order", 0)
        u.setdefault("cost", "normal")
    return reg


def uncovered_scripts(repo: Path, reg: dict) -> list[str]:
    """Scripts matched by script_globs that no unit runs, so a new panel cannot escape the harness."""
    covered = {str(Path(c)) for u in reg["units"] for c in u["cmd"] if str(c).endswith(".py")}
    skip = tuple(reg.get("ignore_prefixes", ["_mockup", "_scratch"]))
    missing = []
    for pattern in reg.get("script_globs", []):
        for p in sorted(repo.glob(pattern)):
            rel = str(p.relative_to(repo))
            if not p.name.startswith(skip) and rel not in covered:
                missing.append(rel)
    return missing


def outputs(repo: Path, reg: dict) -> list[Path]:
    files: list[Path] = []
    for d in reg["output_dirs"]:
        sub = repo / d
        if sub.is_dir():
            files += sorted(sub.glob("*.pdf")) + sorted(sub.glob("*.png"))
    return files


def run_unit(repo: Path, u: dict, timeout: float) -> dict:
    cmd = [str(c) for c in u["cmd"]]
    if cmd[0].endswith(".py"):
        cmd = [sys.executable, *cmd]
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True, timeout=timeout)
        rc, err = p.returncode, p.stderr
    except subprocess.TimeoutExpired:
        rc, err = 124, f"TIMEOUT after {timeout:.0f}s"
    dt = time.monotonic() - t0
    tail = " | ".join(line for line in (err or "").strip().splitlines()[-3:])
    flag = "ok" if rc == 0 else "ERROR"
    print(f"  [{flag:5}] {u['label']:32} {dt:6.1f}s  {('rc=%d ' % rc) if rc else ''}{tail[:120]}")
    return {"label": u["label"], "cmd": " ".join(map(str, u["cmd"])), "rc": rc, "sec": round(dt, 1), "stderr": tail}


def snapshot(repo: Path, reg: dict, snap_root: Path, mode: str) -> Path:
    snap = snap_root / mode
    if snap.exists():
        shutil.rmtree(snap)
    (snap / "png").mkdir(parents=True)
    grids: dict[str, np.ndarray] = {}
    rows = ["rel\tkind\tbytes\tsha256\tpdf_w_pt\tpdf_h_pt"]
    for f in outputs(repo, reg):
        rel = f.relative_to(repo).as_posix()
        sha = sig.sha256(f)
        if f.suffix.lower() == ".pdf":
            grid, w_pt, h_pt = sig.perceptual_pdf(f)
            rows.append(f"{rel}\tpdf\t{f.stat().st_size}\t{sha}\t{w_pt:.2f}\t{h_pt:.2f}")
        else:
            grid = sig.perceptual_png(f)
            dst = snap / "png" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
            rows.append(f"{rel}\tpng\t{f.stat().st_size}\t{sha}\t\t")
        grids[rel] = grid
    (snap / "manifest.tsv").write_text("\n".join(rows) + "\n")
    np.savez_compressed(snap / "grids.npz", **{k.replace("/", "__"): v for k, v in grids.items()})
    if mode == "baseline":
        shutil.copy2(snap / "manifest.tsv", snap_root / "baseline_manifest.tsv")
    print(f"\nsnapshot[{mode}]: {len(grids)} outputs -> {snap}")
    return snap


def main() -> None:
    ap = argparse.ArgumentParser(description="Render all registered figure units and snapshot their outputs.")
    ap.add_argument("--repo", type=Path, default=Path("."), help="repository root; commands run from here")
    ap.add_argument("--units", type=Path, required=True, help="JSON registry of units")
    ap.add_argument("--snap", type=Path, help="snapshot folder (default <repo>/_verify_snap; gitignore it)")
    ap.add_argument("--baseline", action="store_true", help="freeze the pre-change state")
    ap.add_argument("--only", default="", help="substring filter on unit label (never use before compare)")
    ap.add_argument("--skip-heavy", action="store_true", help="skip units marked cost=heavy")
    ap.add_argument("--timeout", type=float, default=1800.0, help="seconds per unit (default 1800)")
    args = ap.parse_args()

    repo = args.repo.resolve()
    reg = load_registry(args.units)
    snap_root = (args.snap or repo / "_verify_snap").resolve()

    missing = uncovered_scripts(repo, reg)
    if missing:
        print(f"WARNING: scripts not covered by a unit: {missing}")
    if args.only:
        print("WARNING: --only renders a subset; outputs of the other units are not refreshed")

    units = [u for u in reg["units"]
             if (not args.only or args.only in u["label"])
             and not (args.skip_heavy and u["cost"] == "heavy")]
    units.sort(key=lambda u: u["order"])
    mode = "baseline" if args.baseline else "current"
    print(f"rendering {len(units)} units (mode={mode}, timeout={args.timeout:.0f}s)\n")
    log = [run_unit(repo, u, args.timeout) for u in units]

    snap = snapshot(repo, reg, snap_root, mode)  # recreates the folder, so the log goes in after
    cols = ["label", "cmd", "rc", "sec", "stderr"]
    (snap / "render_log.tsv").write_text(
        "\t".join(cols) + "\n" + "\n".join("\t".join(str(r[c]) for c in cols) for r in log) + "\n")
    errs = [r["label"] for r in log if r["rc"] != 0]
    if errs:
        print(f"\n{len(errs)} unit(s) FAILED to render: {errs}")
        sys.exit(1)
    print("all units rendered cleanly.")


if __name__ == "__main__":
    main()

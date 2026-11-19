#!/usr/bin/env python3
"""Check, compile and render one TikZ figure to a versioned PNG, in one command.

Steps, stopping at the first failure:
  1. check_tikz_safety.py (same folder) on the source;
  2. LaTeX (pdflatex by default) with -interaction=nonstopmode -halt-on-error,
     optionally with the theme or font family set from the command line;
  3. the log is read: errors, overfull boxes and missing characters are reported
     (the exit code alone hides some failures);
  4. pdftoppm renders every page to <name>[_<theme>]_vNN-<page>.png, where NN is
     the next free version number, so a cached viewer never shows an old render;
  5. every PNG is measured: a page under 40 px on a side is reported as blank
     (a body compiled without its preamble), and in a multi-page frame deck all
     frames must have the same size (otherwise the animation jitters).

Then open the PNG and look at it. This script cannot see overlap or crowding.

Needs: a TeX engine and pdftoppm (poppler) on PATH. Python standard library only.

Usage:
    python3 render_figure.py fig.tex
    python3 render_figure.py fig.tex --theme serif --dpi 170
    python3 render_figure.py deck.tex --dpi 150          # frame deck: checks frame sizes
    python3 render_figure.py fig.tex --family cm --out previews/
"""

from __future__ import annotations

import argparse
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


def next_version(out: Path, stem: str) -> int:
    used = [int(m.group(1)) for p in out.glob(f"{stem}_v*-*.png")
            if (m := re.match(rf"{re.escape(stem)}_v(\d+)-", p.name))]
    return max(used, default=0) + 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Safety check, compile and render a TikZ figure to versioned PNGs.")
    ap.add_argument("tex", help="the standalone figure source (preamble + body)")
    ap.add_argument("--theme", choices=["minimal", "serif"], help="set \\figtheme for this build")
    ap.add_argument("--family", choices=["auto", "sans", "serif", "cm"], help="set \\figfamily for this build")
    ap.add_argument("--engine", default="pdflatex", help="pdflatex (default), xelatex or lualatex")
    ap.add_argument("--dpi", type=int, default=170, help="PNG resolution (default 170)")
    ap.add_argument("--out", help="folder for the PNGs (default: next to the source)")
    ap.add_argument("--skip-check", action="store_true", help="do not run the static safety check")
    args = ap.parse_args(argv)

    tex = Path(args.tex).resolve()
    if not tex.exists():
        print(f"ERROR: {tex} does not exist")
        return 1
    for tool in (args.engine, "pdftoppm"):
        if not shutil.which(tool):
            print(f"ERROR: {tool} not found on PATH")
            return 1

    if not args.skip_check:
        sys.path.insert(0, str(HERE))
        from check_tikz_safety import check_text  # noqa: E402
        errors, warnings = check_text(tex.read_text(encoding="utf-8", errors="replace"))
        for w in warnings:
            print(f"WARN:  safety: {w}")
        if errors:
            for e in errors:
                print(f"ERROR: safety: {e}")
            return 1
        print("ok     safety check")

    suffix = "".join(f"_{v}" for v in (args.theme, args.family) if v)
    job = tex.stem + suffix
    defs = ""
    if args.theme:
        defs += f"\\def\\figtheme{{{args.theme}}}"
    if args.family:
        defs += f"\\def\\figfamily{{{args.family}}}"
    cmd = [args.engine, "-interaction=nonstopmode", "-halt-on-error", f"-jobname={job}",
           f"{defs}\\input{{{tex.name}}}" if defs else tex.name]
    proc = subprocess.run(cmd, cwd=tex.parent, capture_output=True, text=True)
    log_path = tex.parent / f"{job}.log"
    log = log_path.read_text(errors="replace") if log_path.exists() else ""
    tex_errors = [ln for ln in log.splitlines() if ln.startswith("!")]
    if proc.returncode != 0 or tex_errors:
        print(f"ERROR: {args.engine} failed (exit {proc.returncode}); first lines of the log:")
        for ln in tex_errors[:4]:
            print(f"       {ln}")
        m = re.search(r"^l\.\d+.*$", log, re.M)
        if m:
            print(f"       {m.group(0)[:160]}")
        return 1
    overfull = len(re.findall(r"^Overfull \\[hv]box", log, re.M))
    missing = len(re.findall(r"Missing character", log))
    print(f"ok     {args.engine}: {job}.pdf ({overfull} overfull boxes, {missing} missing characters)")
    if missing:
        print("WARN:  missing characters: a glyph is not in the font (check symbols such as arrows and Greek)")

    out = Path(args.out).resolve() if args.out else tex.parent
    out.mkdir(parents=True, exist_ok=True)
    ver = next_version(out, job)
    prefix = out / f"{job}_v{ver:02d}"
    subprocess.run(["pdftoppm", "-png", "-r", str(args.dpi), str(tex.parent / f"{job}.pdf"), str(prefix)],
                   check=True)
    pngs = sorted(out.glob(f"{prefix.name}-*.png"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    if not pngs:
        print("ERROR: pdftoppm wrote no PNG")
        return 1
    sizes = [png_size(p) for p in pngs]
    failed = False
    for p, (w, h) in zip(pngs, sizes):
        if min(w, h) < 40:
            print(f"ERROR: {p.name} is {w}x{h} px: blank page (was the body compiled without the preamble?)")
            failed = True
    if len(set(sizes)) > 1:
        print(f"ERROR: frames differ in size {sorted(set(sizes))}: lock the bounding box in every frame")
        failed = True
    print(f"ok     {len(pngs)} page(s) at {args.dpi} dpi, {sizes[0][0]}x{sizes[0][1]} px")
    print(f"look   {pngs[0]}")
    if len(pngs) > 2:
        print(f"look   {pngs[len(pngs) // 2]}")
        print(f"look   {pngs[-1]}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

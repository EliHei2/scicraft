#!/usr/bin/env python3
"""Lint region files of a canvas schematic against the region contract and the anti-slide list.

A region function draws only through PAL, FONT and LIB. This script reads the region JS
files (and optionally main.js and layout.js) and reports, with file and line:

  error  slide chrome: shadowBlur, shadowColor, shadowOffset, createLinearGradient,
         createRadialGradient (outside LIB.densityGlow), filter blur
  error  a literal font size under the floor: size: N, ctx.font = '... Npx', FONT.Lx - N
  error  contract breaks: setTransform, canvas.width/height, done-flag, drawing the panel letter
  warn   a hex or rgb() colour literal (use a PAL token)
  warn   a font family string (use FONT.family) or a monospace face outside code tokens
  warn   a numeric size literal at or above the floor (use FONT.L1, L2, L3 or LETTER)
  warn   a panel title ending in a period, or a title longer than four words (layout.js)

Examples:
    python3 lint_regions.py code/regions/
    python3 lint_regions.py code/regions/region_b.js --floor 18
    python3 lint_regions.py code/regions/ --layout code/layout.js

Exit code 1 when an error is found. Standard library only.
"""
import argparse
import re
import sys
from pathlib import Path

CHROME = re.compile(r"shadowBlur|shadowColor|shadowOffset[XY]|createLinearGradient|createRadialGradient|filter\s*=\s*['\"]blur")
HEX = re.compile(r"['\"]#[0-9a-fA-F]{3,8}['\"]")
RGB = re.compile(r"['\"]rgba?\(")
SIZE = re.compile(r"\bsize\s*:\s*(\d+(?:\.\d+)?)\b")
FONTPX = re.compile(r"\.font\s*=\s*[`'\"][^`'\"]*?(\d+(?:\.\d+)?)px")
FONTMINUS = re.compile(r"FONT\.(L1|L2|L3|LETTER)\s*-\s*(\d+(?:\.\d+)?)")
FAMILY = re.compile(r"Helvetica|Arial|sans-serif|DejaVu|Menlo|monospace|Courier", re.I)
CONTRACT = re.compile(r"setTransform|canvas\.(width|height)\s*=|done-flag")
LETTER = re.compile(r"FONT\.LETTER")
TITLE = re.compile(r"title\s*:\s*['\"]([^'\"]*)['\"]")
TIERS = {"LETTER": 29, "L1": 25, "L2": 21, "L3": 18}


def strip_comments(line, in_block):
    out, i = "", 0
    while i < len(line):
        if in_block:
            j = line.find("*/", i)
            if j < 0:
                return out, True
            i, in_block = j + 2, False
        else:
            j, k = line.find("/*", i), line.find("//", i)
            if k >= 0 and (j < 0 or k < j):
                return out + line[i:k], False
            if j < 0:
                return out + line[i:], False
            out += line[i:j]
            i, in_block = j + 2, True
    return out, in_block


def lint_file(f, floor, errs, warns, is_region):
    in_block = False
    for n, raw in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line, in_block = strip_comments(raw, in_block)
        if not line.strip():
            continue
        w = f"{f}:{n}"
        for m in CHROME.finditer(line):
            errs.append(f"{w}: slide chrome '{m.group(0)}' (flat only; shadows and gradients are banned)")
        for m in SIZE.finditer(line):
            v = float(m.group(1))
            (errs if v < floor else warns).append(f"{w}: literal size {v:g} px" + (f" is under the {floor:g} px floor" if v < floor else "; use a FONT tier"))
        for m in FONTPX.finditer(line):
            v = float(m.group(1))
            (errs if v < floor else warns).append(f"{w}: font set by hand at {v:g} px" + (" (under the floor)" if v < floor else "; use LIB.text with a FONT tier"))
        for m in FONTMINUS.finditer(line):
            v = TIERS[m.group(1)] - float(m.group(2))
            if v < floor:
                errs.append(f"{w}: FONT.{m.group(1)} - {m.group(2)} = {v:g} px is under the floor")
        if is_region:
            if CONTRACT.search(line):
                errs.append(f"{w}: region touches the canvas transform, size or done-flag; only main.js may")
            if LETTER.search(line):
                errs.append(f"{w}: region draws at FONT.LETTER; the master draws panel letters")
            for m in HEX.finditer(line):
                warns.append(f"{w}: colour literal {m.group(0)}; use a PAL token")
            if RGB.search(line):
                warns.append(f"{w}: rgb() literal; use a PAL token or LIB.alpha")
            if FAMILY.search(line):
                warns.append(f"{w}: font family in a region; use FONT.family (FONT.mono only for code tokens)")


def lint_layout(f, errs, warns):
    for n, raw in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for m in TITLE.finditer(raw):
            t = m.group(1).strip()
            if t.endswith("."):
                warns.append(f"{f}:{n}: title '{t}' ends in a period; titles are noun phrases")
            if len(t.split()) > 4:
                warns.append(f"{f}:{n}: title '{t}' has {len(t.split())} words; keep at most four")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("paths", nargs="+", type=Path, help="region files or folders of region_*.js")
    ap.add_argument("--floor", type=float, default=18.0, help="smallest text size in logical px (default 18 = 5 pt at 10 px/mm)")
    ap.add_argument("--layout", type=Path, help="layout.js, to check panel titles")
    ap.add_argument("--main", type=Path, help="main.js, checked for slide chrome and small sizes only")
    a = ap.parse_args()

    files = []
    for p in a.paths:
        if not p.exists():
            print(f"no such file or folder: {p}", file=sys.stderr)
            return 1
        files += sorted(p.glob("region_*.js")) or sorted(p.glob("*.js")) if p.is_dir() else [p]
    if not files:
        print("no .js files found", file=sys.stderr)
        return 1
    errs, warns = [], []
    for f in files:
        lint_file(f, a.floor, errs, warns, is_region=True)
    if a.main:
        lint_file(a.main, a.floor, errs, warns, is_region=False)
    if a.layout:
        lint_layout(a.layout, errs, warns)
    for e in errs:
        print("ERROR ", e)
    for w in warns:
        print("warn  ", w)
    print(f"linted {len(files)} region file(s): {len(errs)} error(s), {len(warns)} warning(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())

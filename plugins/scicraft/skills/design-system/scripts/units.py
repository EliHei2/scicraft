#!/usr/bin/env python3
"""Convert type and line sizes between canvas px, printed mm and printed pt, and check a minimum size.

A drawing made on a canvas of W px that is printed (or projected) W_mm wide has
    mm per px = print_mm / canvas_px
    pt        = mm / 0.352778          (1 pt = 1/72 inch = 25.4/72 mm)
A vector page designed D mm wide and printed P mm wide scales every design pt by P / D.

Two ways to describe the medium:
  --canvas-px W --print-mm P     a raster or canvas drawing (schematic, slide, web figure)
  --design-mm D --print-mm P     a vector page scaled at print (poster designed larger than A0)
or one of the presets (--preset NAME), which fill those numbers in:
  schematic-a4    3200 px canvas printed 180 mm wide (1 px = 0.05625 mm)
  schematic-lib   1830 px canvas printed 183 mm wide (10 px per mm)
  slide           1920 px canvas shown as a 13.333 in (338.67 mm) slide, so 2 px = 1 pt
  poster-a0       1000 mm design page printed on A0 (841 mm), so printed pt = design pt x 0.841
  figure          true size: panels drawn at their printed mm (matplotlib, TikZ), 1 pt = 1 pt

Subcommands:
  convert SIZE...           print each size (75px, 4.2mm, 12pt) in px, mm and pt at print
  min --pt N                the smallest canvas px (or design pt) that prints at N pt
  check --min-pt N SIZE...  fail (exit 1) when any size prints under N pt
  check --min-pt N --scan FILE...
                            read font sizes out of HTML, CSS, JS (`font: 300 18px`, `ctx.font = '24px'`,
                            `font-size: 13px`), LaTeX (`\\fontsize{27}{35}`) or matplotlib (`fontsize=5`)
                            and check each one

In canvas mode a size in mm or pt is read as a printed size. In design mode a size in mm or pt is read as a
design size and scaled. Standard library only; Python 3.9 or later.

Examples:
  python3 units.py --preset schematic-a4 min --pt 5           # 31.4 px
  python3 units.py --canvas-px 2400 --print-mm 120 check --min-pt 5 14px 36px
  python3 units.py --preset poster-a0 convert 27pt 88pt
  python3 units.py --preset slide check --min-pt 14 --scan deck.html
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MM_PER_PT = 25.4 / 72.0
PRESETS = {
    "schematic-a4": dict(canvas_px=3200.0, print_mm=180.0, design_mm=None),
    "schematic-lib": dict(canvas_px=1830.0, print_mm=183.0, design_mm=None),
    "slide": dict(canvas_px=1920.0, print_mm=13.333333 * 25.4, design_mm=None),
    "poster-a0": dict(canvas_px=None, print_mm=841.0, design_mm=1000.0),
    "figure": dict(canvas_px=None, print_mm=1.0, design_mm=1.0),
}
SIZE_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*(px|mm|pt)\s*$", re.I)
SCAN = [
    # (pattern, unit): the first group is the number
    (re.compile(r"font(?:-size)?\s*[:=]\s*[`'\"]?[^;`'\"\n{}]*?(?<![\w.])([0-9]*\.?[0-9]+)px", re.I), "px"),
    (re.compile(r"\\fontsize\{([0-9]*\.?[0-9]+)\}"), "pt"),
    (re.compile(r"fontsize\s*=\s*([0-9]*\.?[0-9]+)"), "pt"),
]


class Medium:
    def __init__(self, canvas_px, print_mm, design_mm):
        if print_mm is None or print_mm <= 0:
            sys.exit("give --print-mm (or a --preset)")
        if (canvas_px is None) == (design_mm is None):
            sys.exit("give exactly one of --canvas-px and --design-mm (or a --preset)")
        self.canvas_px, self.print_mm, self.design_mm = canvas_px, print_mm, design_mm

    @property
    def canvas(self) -> bool:
        return self.canvas_px is not None

    def describe(self) -> str:
        if self.canvas:
            mmpx = self.print_mm / self.canvas_px
            return (f"canvas {self.canvas_px:g} px printed {self.print_mm:g} mm wide: 1 px = {mmpx:.5f} mm = "
                    f"{mmpx / MM_PER_PT:.4f} pt; 1 pt = {MM_PER_PT / mmpx:.3f} px")
        s = self.print_mm / self.design_mm
        return f"design page {self.design_mm:g} mm printed {self.print_mm:g} mm wide: printed = design x {s:.4f}"

    def to_print_mm(self, value: float, unit: str) -> float:
        unit = unit.lower()
        if unit == "px":
            if not self.canvas:
                sys.exit("a px size needs --canvas-px (this medium is a scaled vector page)")
            return value * self.print_mm / self.canvas_px
        mm = value if unit == "mm" else value * MM_PER_PT
        return mm if self.canvas else mm * self.print_mm / self.design_mm

    def from_print_pt(self, pt: float) -> tuple[float, str]:
        """The canvas px (or design pt) that prints at pt."""
        mm = pt * MM_PER_PT
        if self.canvas:
            return mm * self.canvas_px / self.print_mm, "px"
        same = self.design_mm == self.print_mm
        return pt * self.design_mm / self.print_mm, "pt" if same else "pt (design)"


def parse_size(s: str) -> tuple[float, str]:
    m = SIZE_RE.match(s)
    if not m:
        sys.exit(f"cannot read size '{s}': write a number with px, mm or pt, such as 75px")
    return float(m.group(1)), m.group(2).lower()


def scan_file(path: Path) -> list[tuple[int, float, str, str]]:
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for rx, unit in SCAN:
            for m in rx.finditer(line):
                out.append((i, float(m.group(1)), unit, line.strip()[:90]))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", choices=sorted(PRESETS), help="fill in the medium from a preset")
    ap.add_argument("--canvas-px", type=float, help="canvas width in px")
    ap.add_argument("--design-mm", type=float, help="design page width in mm (vector page scaled at print)")
    ap.add_argument("--print-mm", type=float, help="printed or projected width in mm")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("convert", help="print sizes in px, mm and pt at print")
    c.add_argument("sizes", nargs="+")
    m = sub.add_parser("min", help="smallest canvas size that prints at a given pt")
    m.add_argument("--pt", type=float, required=True)
    k = sub.add_parser("check", help="fail when a size prints under the minimum")
    k.add_argument("--min-pt", type=float, required=True, help="smallest allowed printed size in pt")
    k.add_argument("--tolerance-pt", type=float, default=0.05,
                   help="slack for rounding, in pt (default 0.05, so 18 px on the 1830 px schematic canvas passes 5 pt)")
    k.add_argument("--scan", nargs="+", type=Path, help="files to read font sizes from")
    k.add_argument("sizes", nargs="*")
    a = ap.parse_args(argv)

    p = PRESETS.get(a.preset, {}) if a.preset else {}
    med = Medium(a.canvas_px if a.canvas_px is not None else p.get("canvas_px"),
                 a.print_mm if a.print_mm is not None else p.get("print_mm"),
                 a.design_mm if a.design_mm is not None else p.get("design_mm"))
    if a.preset == "figure" and a.canvas_px is None:
        print("true size: sizes in mm and pt are printed sizes")
    else:
        print(med.describe())

    if a.cmd == "convert":
        for s in a.sizes:
            v, u = parse_size(s)
            mm = med.to_print_mm(v, u)
            extra = f" = {mm * med.canvas_px / med.print_mm:.1f} px" if med.canvas else ""
            print(f"{s:>10}  ->  {mm:.3f} mm = {mm / MM_PER_PT:.2f} pt at print{extra}")
        return 0

    if a.cmd == "min":
        v, unit = med.from_print_pt(a.pt)
        print(f"{a.pt:g} pt at print = {a.pt * MM_PER_PT:.3f} mm = {v:.2f} {unit}; use at least {v:.1f} {unit}")
        return 0

    items = []
    for s in a.sizes:
        v, u = parse_size(s)
        items.append((s, v, u, "argument"))
    for f in a.scan or []:
        if not f.exists():
            print(f"FAIL  {f}: file not found")
            return 1
        found = scan_file(f)
        if not found:
            print(f"note  {f}: no font sizes found")
        for line, v, u, text in found:
            items.append((f"{v:g}{u}", v, u, f"{f.name}:{line}  {text}"))
    if not items:
        sys.exit("give sizes or --scan files to check")
    low, need = 0, med.from_print_pt(a.min_pt)
    for label, v, u, where in items:
        if u == "px" and not med.canvas:
            print(f"skip  {label:>9}  px size on a scaled vector page  ({where})")
            continue
        pt = med.to_print_mm(v, u) / MM_PER_PT
        ok = pt + a.tolerance_pt >= a.min_pt
        low += not ok
        print(f"{'ok  ' if ok else 'LOW '}  {label:>9} = {pt:6.2f} pt  ({where})")
    print(f"\nchecked {len(items)} size(s) against {a.min_pt:g} pt at print "
          f"(= {need[0]:.1f} {need[1]}): {low} below")
    return 1 if low else 0


if __name__ == "__main__":
    sys.exit(main())

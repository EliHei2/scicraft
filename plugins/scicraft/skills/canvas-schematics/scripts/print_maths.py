#!/usr/bin/env python3
"""Print maths for a schematic canvas: px to mm to pt, and the minimum px per text tier.

A canvas of W logical px printed at P mm has W/P px per mm. One pt is 25.4/72 mm.
So a size of s pt needs s * 0.35278 * W / P px. At the house contract of 10 px/mm
(W = 10 * P) that is 3.528 px per pt, and the 5 pt floor is 18 px.

Examples:
    python3 print_maths.py --width-mm 183                    # tiers for a 1830 px canvas
    python3 print_maths.py --width-px 3200 --width-mm 180    # an inherited canvas
    python3 print_maths.py --width-mm 183 --px 17 25 29      # what given px sizes print at
    python3 print_maths.py --width-mm 183 --scale 3          # also the device resolution

Exit code 1 when a size given with --px prints under the floor. Standard library only.
"""
import argparse
import math
import sys

MM_PER_PT = 25.4 / 72.0
TIERS = [("panel letter", 8.2, "8 pt paper default, bold lowercase, no period"),
         ("L1 title", 7.0, "panel titles, one size for every panel"),
         ("L2 label", 6.0, "block and group labels, maths"),
         ("L3 annotation", 5.0, "ticks, glosses, legends: the floor")]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("--width-mm", type=float, required=True, help="printed width of the figure in mm (183 double column, 89 single)")
    ap.add_argument("--width-px", type=float, help="canvas width in logical px (default: 10 px per mm)")
    ap.add_argument("--floor-pt", type=float, default=5.0, help="smallest printed size allowed (default 5 pt)")
    ap.add_argument("--px", type=float, nargs="*", default=[], help="px sizes to convert to printed pt")
    ap.add_argument("--scale", type=float, help="device scale of the render, to report px per mm and dpi of the PNG")
    a = ap.parse_args()

    wpx = a.width_px if a.width_px else a.width_mm * 10.0
    px_per_mm = wpx / a.width_mm
    px_per_pt = px_per_mm * MM_PER_PT
    print(f"canvas {wpx:.0f} px for {a.width_mm:g} mm: {px_per_mm:.4g} px/mm, 1 px = {1 / px_per_mm:.5g} mm, 1 pt = {px_per_pt:.4g} px")
    print(f"{'tier':<15}{'pt':>6}{'px':>9}  use")
    for name, pt, use in TIERS:
        px = math.ceil(pt * px_per_pt - 1e-9) if pt <= a.floor_pt else round(pt * px_per_pt)
        print(f"{name:<15}{pt:>6.2f}{px:>9d}  {use}")
    floor_px = math.ceil(a.floor_pt * px_per_pt - 1e-9)
    print(f"floor: {a.floor_pt:g} pt = {floor_px} px on this canvas")
    if a.scale:
        dpi = px_per_mm * a.scale * 25.4
        print(f"device scale {a.scale:g}: PNG {wpx * a.scale:.0f} px wide, {px_per_mm * a.scale:.4g} px/mm, {dpi:.0f} dpi")
    bad = 0
    for p in a.px:
        pt = p / px_per_pt
        flag = "UNDER FLOOR" if pt < a.floor_pt - 1e-9 else "ok"
        bad += flag != "ok"
        print(f"{p:g} px prints at {pt:.2f} pt ({p / px_per_mm:.2f} mm)  {flag}")
    if a.px:
        print(f"checked {len(a.px)} size(s): {bad} under the {a.floor_pt:g} pt floor")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

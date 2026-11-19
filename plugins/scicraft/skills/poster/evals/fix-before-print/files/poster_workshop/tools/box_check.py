#!/usr/bin/env python3
"""Check the placed boxes of a TikZ poster for overlaps, crowding and margin violations.

The poster template logs every placed piece to the LaTeX log as one line
    BOX name x0 y0 x1 y1
in cm from the bottom-left corner of the design page (see the \\foreach at the end of
assets/poster/poster_design.tex). This script reads those lines and reports:

  OVERLAP   two boxes that intersect
  crowded   two boxes closer than --gap cm (horizontal or vertical clearance)
  margin    a box outside the page margins

usage:
    python3 box_check.py build/poster_design.log [--gap 0.2] [--page 100x141.42]
                         [--margins 3,3,2,1.25] [--tol 0.05] [--allow a/b,c/d]

  --page     design page in cm, W x H (default A0 proportions at 1000 mm wide)
  --margins  left,right,top,bottom in cm (default 3,3,2,1.25: the margins of the poster this was taken from)
  --tol      slack allowed on every margin, in cm
  --allow    pairs that touch on purpose (a node inside a fit, a mask over a table edge), name/name

A piece that is not in the log is not checked: add every new node name to the \\foreach list.
Exit status 1 if anything is found. Standard library only; Python 3.9 or later.
"""
import argparse
import re
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="the LaTeX log of the design page")
    ap.add_argument("--gap", type=float, default=0.4, help="smallest allowed clearance in cm (default 0.4)")
    ap.add_argument("--page", default="100x141.42", help="design page W x H in cm")
    ap.add_argument("--margins", default="3,3,2,1.25", help="left,right,top,bottom in cm")
    ap.add_argument("--tol", type=float, default=0.05, help="slack on the margins in cm")
    ap.add_argument("--allow", default="", help="comma-separated name/name pairs allowed to touch")
    a = ap.parse_args()

    W, H = map(float, a.page.lower().split("x"))
    ml, mr, mt, mb = map(float, a.margins.split(","))
    allow = {frozenset(p.split("/")) for p in a.allow.split(",") if "/" in p}
    log = open(a.log, encoding="utf-8", errors="replace").read()
    boxes = {m[0]: tuple(map(float, m[1:]))
             for m in re.findall(r"^BOX (\S+) (\S+) (\S+) (\S+) (\S+)$", log, re.M)}
    if not boxes:
        print(f"no BOX lines in {a.log}: is the \\typeout loop at the end of the poster source?")
        sys.exit(1)
    bad = 0
    names = list(boxes)
    for i, n1 in enumerate(names):
        ax0, ay0, ax1, ay1 = boxes[n1]
        if ax0 < ml - a.tol or ax1 > W - mr + a.tol or ay0 < mb - a.tol or ay1 > H - mt + a.tol:
            print(f"margin   {n1}: x {ax0:.2f}..{ax1:.2f} y {ay0:.2f}..{ay1:.2f} cm")
            bad += 1
        for n2 in names[i + 1:]:
            if frozenset((n1, n2)) in allow:
                continue
            bx0, by0, bx1, by1 = boxes[n2]
            dx = max(bx0 - ax1, ax0 - bx1)      # > 0: horizontal clearance
            dy = max(by0 - ay1, ay0 - by1)      # > 0: vertical clearance
            clear = max(dx, dy)
            if clear < a.gap:
                kind = "OVERLAP" if clear < 0 else "crowded"
                print(f"{kind:8s} {n1} / {n2}: clearance {clear:.2f} cm")
                bad += 1
    print(f"{len(boxes)} boxes, gap {a.gap} cm, margins {a.margins} cm: {bad} findings")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

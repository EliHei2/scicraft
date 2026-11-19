#!/usr/bin/env python3
"""Measure a reference figure, cut it into per-region target crops, and compare aspect ratios.

Reproduce a reference before polishing it: the canvas takes the reference's aspect ratio
(within 2 %), and every region builder gets its own crop as the target.

Crops are fractional boxes x0,y0,x1,y1 in [0, 1] of the reference, given inline
(name=x0,y0,x1,y1) or in a JSON file {"name": [x0, y0, x1, y1], ...}.

Examples:
    python3 ref_crops.py reference.png                                  # size and aspect ratio
    python3 ref_crops.py reference.png --canvas 1830x1290               # does the canvas match?
    python3 ref_crops.py reference.png --out ref_crops a=0,0,0.55,0.42 b=0.57,0,1,0.42
    python3 ref_crops.py reference.png --out ref_crops --boxes crops.json --canvas 1830x1290
    python3 ref_crops.py reference.png --suggest-width 1830             # canvas height for that width

Writes ref_crops/orig_<name>.png. Exit code 1 when --canvas differs by more than --tol
(default 2 %) or a box is malformed. Needs Pillow (pip install pillow) for reading images.
"""
import argparse
import json
import sys
from pathlib import Path


def parse_box(spec):
    name, _, nums = spec.partition("=")
    vals = [float(v) for v in nums.split(",")]
    if not name or len(vals) != 4:
        raise ValueError(f"box '{spec}' must look like name=x0,y0,x1,y1")
    return name, vals


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("reference", type=Path, help="the reference figure (PNG, JPEG)")
    ap.add_argument("boxes_inline", nargs="*", metavar="name=x0,y0,x1,y1", help="crop boxes as fractions of width and height")
    ap.add_argument("--boxes", type=Path, help="JSON file of crop boxes")
    ap.add_argument("--out", type=Path, default=Path("ref_crops"), help="folder for orig_<name>.png (default ref_crops)")
    ap.add_argument("--canvas", help="canvas size WxH in logical px to compare with the reference")
    ap.add_argument("--tol", type=float, default=0.02, help="allowed relative aspect-ratio difference (default 0.02)")
    ap.add_argument("--suggest-width", type=float, help="print the canvas height that keeps the aspect ratio at this width")
    a = ap.parse_intermixed_args()

    try:
        from PIL import Image
    except ImportError:
        print("Pillow is needed: pip install pillow", file=sys.stderr)
        return 1
    im = Image.open(a.reference).convert("RGB")
    W, H = im.size
    ar = W / H
    print(f"reference {a.reference.name}: {W} x {H} px, aspect ratio {ar:.4f} ({'landscape' if ar > 1 else 'portrait or square'})")
    status = 0
    if a.suggest_width:
        print(f"canvas for width {a.suggest_width:g} px: height {round(a.suggest_width / ar)} px")
    if a.canvas:
        cw, ch = (float(v) for v in a.canvas.lower().split("x"))
        car = cw / ch
        diff = abs(car - ar) / ar
        ok = diff <= a.tol
        print(f"canvas {cw:g} x {ch:g}: aspect ratio {car:.4f}, differs by {diff * 100:.2f} % ({'ok' if ok else 'TOO FAR'}; limit {a.tol * 100:g} %)")
        if not ok:
            print(f"  use height {round(cw / ar)} px for width {cw:g}")
            status = 1

    boxes = {}
    if a.boxes:
        boxes.update({k: [float(x) for x in v] for k, v in json.loads(a.boxes.read_text()).items()})
    try:
        boxes.update(dict(parse_box(s) for s in a.boxes_inline))
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    if boxes:
        a.out.mkdir(parents=True, exist_ok=True)
        for name, (x0, y0, x1, y1) in boxes.items():
            if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
                print(f"box {name} {x0, y0, x1, y1} is not inside [0, 1] with x0 < x1 and y0 < y1", file=sys.stderr)
                status = 1
                continue
            crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
            p = a.out / f"orig_{name}.png"
            crop.save(p)
            print(f"wrote {p}  ({crop.size[0]} x {crop.size[1]} px, aspect ratio {crop.size[0] / crop.size[1]:.3f})")
        print(f"{len(boxes)} crop(s) requested")
    return status


if __name__ == "__main__":
    sys.exit(main())

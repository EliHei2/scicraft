#!/usr/bin/env python3
"""Read the line numbers that replies cite from the built review PDF, so they stay right after every rebuild.

    python3 resolve_lines.py paper.pdf refs.json --out refs_resolved.json
    python3 resolve_lines.py paper.pdf refs.json --aux paper.aux --fill replies.md --filled replies_final.md
    python3 resolve_lines.py paper.pdf --pagefill 10

Venues with a line-numbered review copy print a ruler: a column of numbers in the left margin, one per line slot.
A cited passage is given by a start phrase and an optional end phrase, both as printed in the PDF; its lines are
the ruler entries nearest in height to the first and the last hit.

refs.json maps a token to a passage or to a float label:
    {"BENCH":  ["ranks first on 9 of", "the 14 tasks"],
     "ABL":    ["Ablations.", "against an identically trained control", "after:Table 2:"],
     "TAB17":  ["Table 17:", "60k", "last"],
     "SPLIT":  [["The model has the higher median", null], ["on the second task", "on the last task"]],
     "T_MAIN": "label:tab:main"}
"after:<phrase>" starts the search on the page of that phrase; "last" takes the last hit of the end phrase on its
page; a list of parts is a passage that a float splits, printed as two ranges. "label:<name>" reads the float or
section number from the .aux file (--aux).

In the replies, write tokens as [[BENCH]] (or the bracket form \u27e6BENCH\u27e7); --fill replaces them. Ranges are printed
"463 to 464" because dashes are banned in reply prose (--joiner changes it).
--pagefill N prints, for the first N pages, the last used ruler line and the empty slots at the bottom.

Needs PyMuPDF (pip install pymupdf). Exit code 1 when a passage or label is not found.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fitz
except ImportError:  # pragma: no cover
    sys.exit("resolve_lines.py needs PyMuPDF: pip install pymupdf")


class Ruler:
    def __init__(self, pdf: str, margin: float = 100, digits: str = r"\d{3,4}"):
        self.doc = fitz.open(pdf)
        self.margin = margin
        self.rulers = []
        for page in self.doc:
            marks = [((y0 + y1) / 2, int(w)) for x0, y0, x1, y1, w, *_ in page.get_text("words")
                     if x1 < margin and re.fullmatch(digits, w)]
            self.rulers.append(sorted(marks))
        if not any(self.rulers):
            sys.exit(f"no ruler numbers found left of x = {margin} pt; is this the line-numbered review copy? (see --margin, --digits)")

    def near(self, pno: int, y: float):
        marks = self.rulers[pno]
        return min(marks, key=lambda m: abs(m[0] - y))[1] if marks else None

    def find(self, phrase: str, start_page: int = 0, last: bool = False):
        """(page from 1, first line, last line) of the first page at or after start_page holding the phrase."""
        for pno in range(start_page, len(self.doc)):
            rects = self.doc[pno].search_for(phrase)
            if not rects:
                continue
            group = [rects[0]]
            for r in rects[1:]:                         # one rect per printed line of a hit; stop at the next hit
                if r.y0 - group[-1].y1 < 6 and len(group) < 6:
                    group.append(r)
                else:
                    break
            if last:
                group = [rects[-1]]
            ys = [(r.y0 + r.y1) / 2 for r in group]
            return pno + 1, self.near(pno, min(ys)), self.near(pno, max(ys))
        return None

    def pagefill(self, n: int, bottom: float = 745, top: float = 60):
        for pno in range(min(n, len(self.doc))):
            page, marks = self.doc[pno], self.rulers[pno]
            if not marks:
                print(f"page {pno + 1:2d}: no ruler")
                continue
            low = max([y1 for x0, y0, x1, y1, *_ in page.get_text("words") if x0 > self.margin and top < y0 and y1 < bottom] or [0])
            for d in page.get_drawings():
                if d["rect"].y1 < bottom and d["rect"].x0 > self.margin:
                    low = max(low, d["rect"].y1)
            for im in page.get_image_info():
                if im["bbox"][3] < bottom:
                    low = max(low, im["bbox"][3])
            last = self.near(pno, low)
            print(f"page {pno + 1:2d}: ruler {marks[0][1]} to {marks[-1][1]}, last used line {last}, empty slots at bottom {marks[-1][1] - last}")


def span(R: Ruler, spec, joiner: str):
    a, b = spec[0], spec[1] if len(spec) > 1 else None
    mode = spec[2] if len(spec) > 2 else ""
    start = 0
    if mode.startswith("after:"):
        hit = R.find(mode[6:])
        if not hit:
            return None, f"anchor page not found: {mode[6:]!r}"
        start = hit[0] - 1
    fa = R.find(a, start)
    if not fa:
        return None, f"start not found: {a!r}"
    first, last = fa[1], fa[2]
    if b:
        fb = R.find(b, fa[0] - 1, last=(mode == "last"))
        if not fb:
            return None, f"end not found: {b!r}"
        last = fb[2]
    if first is None or last is None or last < first:
        return None, f"bad range {first} to {last} (end before start, or on another page)"
    return (first, last, fa[0]), None


def fmt(first: int, last: int, joiner: str) -> str:
    return f"{first}" if first == last else f"{first}{joiner}{last}"


def resolve(R: Ruler, refs: dict, aux: str, joiner: str):
    out, bad = {}, []
    for key, spec in refs.items():
        if isinstance(spec, str) and spec.startswith("label:"):
            lab = spec[6:]
            m = re.search(r"\\newlabel\{" + re.escape(lab) + r"\}\{\{([^}]*)\}", aux or "")
            if m:
                out[key] = m.group(1)
            else:
                bad.append((key, f"label {lab!r} not in the .aux file"))
            continue
        parts = spec if spec and isinstance(spec[0], list) else [spec]
        ranges = []
        for part in parts:
            r, err = span(R, part, joiner)
            if err:
                bad.append((key, err))
                break
            ranges.append(r)
        else:
            merged = [list(ranges[0][:2])]
            for f, l, _ in ranges[1:]:
                if f <= merged[-1][1] + 1:
                    merged[-1] = [min(merged[-1][0], f), max(merged[-1][1], l)]
                else:
                    merged.append([f, l])
            out[key] = ", ".join(fmt(f, l, joiner) for f, l in merged)
            print(f"{key:14s} {out[key]:16s} page {ranges[0][2]}")
    return out, bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pdf", help="the built, line-numbered PDF")
    ap.add_argument("refs", nargs="?", help="JSON of tokens to passages or labels")
    ap.add_argument("--aux", help=".aux file, for label: entries")
    ap.add_argument("--out", help="write the resolved tokens as JSON")
    ap.add_argument("--fill", help="replies with [[TOKEN]] placeholders")
    ap.add_argument("--filled", help="where to write the filled replies (default: print)")
    ap.add_argument("--joiner", default=" to ", help="text between the first and last line (default ' to ')")
    ap.add_argument("--margin", type=float, default=100, help="ruler numbers lie left of this x in pt (default 100)")
    ap.add_argument("--digits", default=r"\d{3,4}", help="regex a ruler number matches (default three or four digits)")
    ap.add_argument("--pagefill", type=int, help="report page fill for the first N pages")
    a = ap.parse_args()
    R = Ruler(a.pdf, a.margin, a.digits)
    if a.pagefill:
        R.pagefill(a.pagefill)
    if not a.refs:
        return 0
    aux = Path(a.aux).read_text(errors="replace") if a.aux else ""
    out, bad = resolve(R, json.loads(Path(a.refs).read_text()), aux, a.joiner)
    for key, why in bad:
        print(f"NOT RESOLVED {key}: {why}")
    if a.out:
        Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    if a.fill:
        text = Path(a.fill).read_text(encoding="utf-8")
        text = re.sub(r"\u27e6([A-Z0-9_]+)\u27e7|\[\[([A-Z0-9_]+)\]\]",
                      lambda m: out.get(m.group(1) or m.group(2), m.group(0)), text)
        left = sorted(set(re.findall(r"\[\[([A-Z0-9_]+)\]\]|\u27e6([A-Z0-9_]+)\u27e7", text)))
        if left:
            print("tokens left unfilled:", ", ".join(x or y for x, y in left))
            bad.append(("fill", "unfilled tokens"))
        if a.filled:
            Path(a.filled).write_text(text, encoding="utf-8")
            print("wrote", a.filled)
        else:
            print(text)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

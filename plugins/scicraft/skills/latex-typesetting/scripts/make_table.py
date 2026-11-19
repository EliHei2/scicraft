#!/usr/bin/env python3
"""Write a booktabs table body from a JSON record, so results tables are generated, never typed.

  make_table.py results_table.json -o tab_results.tex
  make_table.py results_table.json --rank-columns 1-3 --rank-low 4 -o tab_results.tex

The generator may change layout, never a value: every cell's text is printed exactly
as the record holds it. Regenerate after every change to the record. The caption and
\\label stay in the manuscript, around \\input{tab_results}.

JSON format:
{
  "colspec": "@{}lccc@{}",
  "font": "\\\\scriptsize", "colsep": "2.35pt", "max_width": true,
  "rows": [
    {"kind": "head", "cells": [{"text": ""}, {"text": "Task A"}, ...]},
    {"kind": "cmid", "spans": [[2, 3]]},
    {"kind": "mid"},
    {"kind": "group", "text": "pretrained"},
    {"kind": "row", "cells": [{"text": "Method"}, {"text": ".58", "sd": ".09", "star": true}, ...]},
    {"kind": "space", "pt": 3}
  ]
}
A cell may carry: "star" (true only for a significant result, as the caption defines
it; printed as a raised asterisk after the value), "bold" (best by value, only when the
caption declares it), "underline" (second best), "fill" ("first" | "second" | "third" | "warn:30" |
"ok:45"), "rank" (superscript), "sd" (printed small and gray after the value),
"color" (text color name), "span" and "align" (multicolumn).

--rank-columns fills first, second and third per column (1-based column numbers,
higher is better; --rank-low lists columns where lower is better) and adds the
superscript rank, unless a cell already sets "fill". Ties share a rank.

The output defines the rank fills locally, so it compiles with any preamble that loads
booktabs and xcolor with the table option.

Needs Python 3.9+ (standard library only).
"""
import argparse
import json
import re
import sys
from pathlib import Path

FILL = {"first": "rankfirst", "second": "ranksecond", "third": "rankthird"}
COLORS = (r"\definecolor{rankfirst}{HTML}{D3ECE3}\definecolor{ranksecond}{HTML}{D8EBFF}"
          r"\definecolor{rankthird}{HTML}{FDEDCE}\definecolor{warn}{RGB}{210,85,75}\definecolor{ok}{RGB}{65,145,85}")


def fill(f):
    if not f:
        return ""
    if f in FILL:
        return r"\cellcolor{%s}" % FILL[f]
    name, _, pct = f.partition(":")
    if pct and int(pct) > 60:
        print(f"note: fill {f} above 60 % makes the value hard to read", file=sys.stderr)
    return r"\cellcolor{%s!%s}" % (name, pct) if pct and pct != "100" else r"\cellcolor{%s}" % name


def cell(c):
    t = c.get("text", "")
    if c.get("bold") and t:
        t = r"\textbf{%s}" % t
    if c.get("underline") and t:
        t = r"\underline{%s}" % t
    if c.get("star") and t:
        t += r"$^{*}$"
    if c.get("rank"):
        t += r"\textsuperscript{%s}" % c["rank"]
    if c.get("sd"):
        t += r"{\tiny\color{black!62}$\pm$%s}" % c["sd"]
    if c.get("color") and t:
        t = r"\textcolor{%s}{%s}" % (c["color"], t)
    t = fill(c.get("fill")) + t
    if t.startswith("["):
        t = "{" + t + "}"     # a cell starting with [ after \\ would be read as \\[...]
    if c.get("span", 1) > 1:
        t = r"\multicolumn{%d}{%s}{%s}" % (c["span"], c.get("align") or "c", t)
    return t


def number(text):
    m = re.search(r"-?\d*\.?\d+", text.replace("$-$", "-").replace("\\textminus", "-"))
    return float(m.group(0)) if m else None


def parse_cols(spec):
    out = set()
    for part in (spec or "").split(","):
        if "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        elif part.strip():
            out.add(int(part))
    return out


def rank(rows, cols, low):
    data = [r for r in rows if r["kind"] == "row"]
    for col in cols | low:
        vals = sorted({number(r["cells"][col - 1]["text"]) for r in data
                       if len(r["cells"]) >= col and number(r["cells"][col - 1]["text"]) is not None},
                      reverse=col not in low)
        for r in data:
            if len(r["cells"]) < col:
                continue
            c = r["cells"][col - 1]
            v = number(c["text"])
            if v is None or c.get("fill"):
                continue
            k = vals.index(v) + 1
            if k <= 3:
                c["fill"] = ["first", "second", "third"][k - 1]
                c.setdefault("rank", k)


def body(spec):
    ncols = len(re.findall(r"[lcrpXR]", re.sub(r"@\{[^}]*\}|\{[^}]*\}", "", spec["colspec"])))
    out = []
    for it in spec["rows"]:
        k = it["kind"]
        if k in ("head", "row"):
            out.append(" & ".join(cell(c) for c in it["cells"]) + r" \\")
        elif k == "space":
            out.append(r"\addlinespace[%spt]" % it["pt"])
        elif k == "cmid":
            out.append("".join(r"\cmidrule(lr){%d-%d}" % (a, b) for a, b in it["spans"]))
        elif k == "mid":
            out.append(r"\midrule")
        elif k == "group":
            out.append(r"\addlinespace[3pt]\multicolumn{%d}{@{}l}{\textit{%s}}\\[1pt]" % (it.get("ncols", ncols), it["text"]))
        else:
            raise ValueError(f"unknown row kind {k}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record", help="JSON table record")
    ap.add_argument("-o", "--out", help="output .tex (default: print)")
    ap.add_argument("--rank-columns", help="columns to rank, higher is better, e.g. 2-5")
    ap.add_argument("--rank-low", help="columns to rank where lower is better, e.g. 6")
    a = ap.parse_args()
    spec = json.loads(Path(a.record).read_text(encoding="utf-8"))
    if a.rank_columns or a.rank_low:
        rank(spec["rows"], parse_cols(a.rank_columns), parse_cols(a.rank_low))
    tab = "\\begin{tabular}{%s}\n\\toprule\n%s\n\\bottomrule\n\\end{tabular}" % (spec["colspec"], body(spec))
    if spec.get("max_width", True):
        tab = "\\begin{adjustbox}{max width=\\linewidth}\n%s\n\\end{adjustbox}" % tab
    head = f"% generated by make_table.py from {Path(a.record).name}; do not edit\n"
    text = head + "\\begingroup%s\\setlength{\\tabcolsep}{%s}\\renewcommand{\\arraystretch}{1.0}%s\n%s\n\\endgroup\n" % (
        spec.get("font", "\\scriptsize"), spec.get("colsep", "2.35pt"), COLORS, tab)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

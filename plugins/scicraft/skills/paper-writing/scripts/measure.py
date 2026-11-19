#!/usr/bin/env python3
"""Measure a text that arrives from outside the writing loop against the last accepted version.

Written for this skill from the intake procedure of a book project, where the measurement was
done by hand: a package that reported "compile successful, 0 undefined citations" was 2.03 times
the accepted length and 98 percent of the rejected length. Measurement produces a note, never an
edit. A row where the incoming text is closer to the rejected version than to the accepted one is
flagged as a regression.

Rows: words, headings, paragraphs, median and longest paragraph, mean, median, p90 and longest
sentence, share of sentences over 45 words, semicolons per sentence, mean heading length, and per
1,000 words: citations, numerals, bold, cross-references, first person; plus display equations
and figures.

Usage:
  python3 measure.py accepted.tex incoming.tex
  python3 measure.py accepted.tex incoming.tex --rejected rejected.tex
  python3 measure.py accepted.tex incoming.tex --json   # machine-readable

Exit 0 always when the files can be read (the output is evidence for a note, not a verdict);
exit 2 on a usage error. Standard library only. Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

HEAD = re.compile(r"^\s*\\(?:part|chapter|section|subsection|subsubsection|paragraph)\*?\{((?:[^{}]|\{[^{}]*\})*)\}"
                  r"|^#{1,6}\s+(.*)$", re.M)


def strip(t):
    t = re.sub(r"(?m)(?<!\\)%.*$", "", t)
    t = re.sub(r"\\begin\{(equation|align|figure|table)\*?\}.*?\\end\{\1\*?\}", " ", t, flags=re.S)
    t = re.sub(r"\$[^$]*\$", " X ", t)
    t = re.sub(r"\\cite[tp]?\*?(\[[^]]*\])*\{[^}]*\}", " ", t)
    t = re.sub(r"\\(?:c|C)?ref\{[^}]*\}", " 1 ", t)
    t = re.sub(r"\\(?:textbf|emph|textit)\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\[a-zA-Z@]+\*?(\[[^]]*\])?(\{[^}]*\})?", " ", t)
    return t


def sentences(t):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", re.sub(r"\s+", " ", t)) if len(s.split()) > 1]


def pct(xs, q):
    if not xs:
        return 0
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def measure(path):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    heads = [a or b for a, b in HEAD.findall(raw)]
    body = HEAD.sub(" ", raw)
    text = strip(body)
    words = len(text.split())
    paras = [p for p in re.split(r"\n\s*\n", text) if len(p.split()) > 5]
    plen = [len(p.split()) for p in paras]
    sents = sentences(text)
    slen = [len(s.split()) for s in sents]
    k = 1000 / max(words, 1)
    return {
        "words": words,
        "headings": len(heads),
        "paragraphs": len(paras),
        "median paragraph (words)": statistics.median(plen) if plen else 0,
        "longest paragraph (words)": max(plen) if plen else 0,
        "mean sentence (words)": round(statistics.mean(slen), 1) if slen else 0,
        "median sentence (words)": statistics.median(slen) if slen else 0,
        "p90 sentence (words)": pct(slen, 0.9),
        "longest sentence (words)": max(slen) if slen else 0,
        "share of sentences over 45 words (%)": round(100 * sum(x > 45 for x in slen) / max(len(slen), 1), 1),
        "semicolons per sentence": round(text.count(";") / max(len(slen), 1), 2),
        "mean heading length (words)": round(statistics.mean(len(h.split()) for h in heads), 1) if heads else 0,
        "citations per 1k words": round(len(re.findall(r"\\cite[tp]?\*?(?:\[[^]]*\])*\{([^}]*)\}", body)) * k, 1),
        "numerals per 1k words": round(len(re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?", text)) * k, 1),
        "bold per 1k words": round(len(re.findall(r"\\textbf\{|\*\*[^*]+\*\*", body)) * k, 1),
        "cross-references per 1k words": round(len(re.findall(r"\\(?:c|C)?ref\{", body)) * k, 1),
        "first person per 1k words": round(len(re.findall(r"\b(?:I|my|we|our|We|Our|My)\b", text)) * k, 1),
        "display equations": len(re.findall(r"\\begin\{(?:equation|align)\*?\}|\\\[", raw)),
        "figures": len(re.findall(r"\\begin\{figure\*?\}|!\[", raw)),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("accepted", help="the last version the author accepted")
    p.add_argument("incoming", help="the text that arrived from outside the loop")
    p.add_argument("--rejected", help="a version the author rejected, if one exists")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    acc, inc = measure(a.accepted), measure(a.incoming)
    rej = measure(a.rejected) if a.rejected else None
    if a.json:
        print(json.dumps({"accepted": acc, "incoming": inc, "rejected": rej}, indent=2))
        return 0
    cols = ["accepted", "incoming"] + (["rejected"] if rej else []) + ["incoming/accepted", "flag"]
    print(f"{'row':<40}" + "".join(f"{c:>18}" for c in cols))
    regress = 0
    for r in acc:
        ratio = inc[r] / acc[r] if acc[r] else float("nan")
        flag = ""
        if rej is not None and abs(inc[r] - rej[r]) < abs(inc[r] - acc[r]):
            flag = "REGRESSION"
            regress += 1
        vals = [acc[r], inc[r]] + ([rej[r]] if rej else []) + [f"{ratio:.2f}", flag]
        print(f"{r:<40}" + "".join(f"{str(v):>18}" for v in vals))
    if rej is not None:
        print(f"\n{regress} row(s) closer to the rejected version than to the accepted one.")
    print("Record each deviation in the header of the incoming file. Do not edit the text on this basis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check that a paper, caption file, reply or page speaks one statistics vocabulary.

Reads a vocabulary file (default: ../assets/stats_vocabulary.json next to this script) and scans text
files (.tex, .md, .txt, .html, .csv captions) for:

  errors    banned statistics words (whiskers, detectable, q values, daggers, "unadjusted", ...);
            a second multiple-testing correction beside the declared one (Holm next to BH);
            p = 0 or p = .000 (impossible; write p < .001);
            on --surface display: a p value above the print threshold that is printed with '='
            although it is below alpha (the declared rule prints it as 'significant'), and any
            confidence interval when the vocabulary sets intervals_on_display to false.
  warnings  evaluative rank words (wins, beats, top three ...), a p value printed with more digits than
            the rule allows (.0085 instead of <= .009), a p above the print threshold in running text,
            a "+-" without a gloss of what it is anywhere in the file, and p values printed without a
            declaration of the display rule anywhere in the scanned files.

Tables (--surface table) keep exact values, so the print-threshold checks are skipped there; the
vocabulary checks still run. LaTeX comment lines are skipped.

Exit 1 when an error was found. Standard library only. Python 3.9 or later.

Examples:
  python3 stats_lint.py paper/*.tex
  python3 stats_lint.py --surface display figures/captions.md abstract.txt
  python3 stats_lint.py --vocab project_vocab.json --surface table tables/*.tex
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_VOCAB = os.path.join(HERE, "..", "assets", "stats_vocabulary.json")

P_RE = re.compile(
    r"(?<![A-Za-z])\$?(?:p|P)(?:_\{?[A-Za-z.,\\ ]+\}?|[ _-]?(?:adj|value)\w*)?\$?\s*"
    r"(=|<|>|≤|≥|<=|>=|\\leq?|\\geq?|\\le\b|\\ge\b)\s*\$?\s*(0?\.\d+|0|1(?:\.0+)?)(?![\d])")
CI_RE = re.compile(r"(?i)\b\d{2}\s?%\s?(?:CI|confidence)|\bconfidence intervals?\b|\bCIs?\b(?=[\s,.;:)])")
PM_RE = re.compile(r"±|\\pm\b")


def load(path):
    with open(path) as fh:
        v = json.load(fh)
    for k in ("correction", "alpha", "print_threshold", "banned", "warn"):
        if k not in v:
            sys.exit("error: vocabulary %s lacks %r" % (path, k))
    return v


def lines_of(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if path.endswith(".tex") and line.lstrip().startswith("%"):
                continue
            yield i, line.rstrip("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--vocab", default=DEFAULT_VOCAB, help="vocabulary JSON (default: the skill's asset)")
    ap.add_argument("--surface", choices=("text", "display", "table"), default="text",
                    help="text = paper prose or replies; display = figure, abstract, slide, page; table = full tables")
    ap.add_argument("--quiet", action="store_true", help="print errors only")
    a = ap.parse_args(argv)

    v = load(a.vocab)
    alpha, thr = float(v["alpha"]), float(v["print_threshold"])
    banned = [(re.compile(b["pattern"]), b["use"]) for b in v["banned"]]
    warned = [(re.compile(b["pattern"]), b["use"]) for b in v["warn"]]
    others = [re.compile(r"\b%s\b" % re.escape(o)) for o in v.get("other_corrections", [])]
    decl = re.compile(v["declaration_pattern"]) if v.get("declaration_pattern") else None
    gloss = [g.lower() for g in v.get("spread_gloss_words", [])]

    errors, warnings = [], []
    any_p, declared = False, False
    nlines = 0
    for f in a.files:
        if not os.path.isfile(f):
            errors.append("%s: not a file" % f)
            continue
        text = open(f, encoding="utf-8", errors="replace").read()
        if decl and decl.search(text):
            declared = True
        has_gloss = any(g in text.lower() for g in gloss)
        pm_warned = False
        for i, line in lines_of(f):
            nlines += 1
            where = "%s:%d" % (f, i)
            for rx, use in banned:
                for m in rx.finditer(line):
                    errors.append("%s: banned %r -> %s" % (where, m.group(0), use))
            for rx in others:
                for m in rx.finditer(line):
                    errors.append("%s: second correction %r; the paper uses %s everywhere"
                                  % (where, m.group(0), v["correction"]))
            for rx, use in warned:
                for m in rx.finditer(line):
                    warnings.append("%s: %r -> %s" % (where, m.group(0), use))
            if PM_RE.search(line) and not has_gloss and not pm_warned:
                warnings.append("%s: '+-' with no gloss of what it is (SD, IQR, between-unit variability) in this file"
                                % where)
                pm_warned = True
            if a.surface == "display" and not v.get("intervals_on_display", True):
                for m in CI_RE.finditer(line):
                    errors.append("%s: interval %r on a display surface; the declared rule shows p or 'significant' "
                                  "there and keeps intervals in the full table" % (where, m.group(0)))
            for m in P_RE.finditer(line):
                any_p = True
                op, raw = m.group(1), m.group(2)
                val = float(raw)
                if op == "=" and val == 0:
                    errors.append("%s: %r is impossible; write p < .001" % (where, m.group(0).strip()))
                    continue
                if a.surface == "table":
                    continue
                digits = len(raw.split(".")[1]) if "." in raw else 0
                if op == "=" and thr < val < alpha:
                    msg = ("%s: %r is above the print threshold %g; under the declared rule write 'significant "
                           "(adjusted p < %g)' and keep the exact value in the full table, the same for every result"
                           % (where, m.group(0).strip(), thr, alpha))
                    (errors if a.surface == "display" else warnings).append(msg)
                if op == "=" and val < thr and digits > 3:
                    warnings.append("%s: %r has %d decimals; print the bound rounded up (p <= .00x or p < .001)"
                                    % (where, m.group(0).strip(), digits))
    if any_p and decl and not declared and a.surface != "table":
        warnings.append("p values are printed but no file states the display rule (vocabulary declaration_pattern); "
                        "add one sentence to the Methods")
    for e in errors:
        print("ERROR  " + e)
    if not a.quiet:
        for w in warnings:
            print("warn   " + w)
    print("checked %d file(s), %d lines on surface '%s': %d error(s), %d warning(s)"
          % (len(a.files), nlines, a.surface, len(errors), len(warnings)), file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
